import os
import json
import time
from typing import Any, Dict, List

from confluent_kafka import Consumer, KafkaException, KafkaError, TopicPartition, OFFSET_BEGINNING
from influxdb_client import InfluxDBClient, Point, WriteOptions


def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).lower() in {"1", "true", "yes", "on"}


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def read_secret_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception as e:
        raise RuntimeError(f"Failed to read secret file {path}: {e}")


def headers_to_dict(msg_headers) -> Dict[str, str]:
    if not msg_headers:
        return {}
    out: Dict[str, str] = {}
    for k, v in msg_headers:
        try:
            out[k] = v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else (v if v is not None else "")
        except Exception:
            out[k] = str(v) if v is not None else ""
    return out


def parse_value(value: bytes) -> Any:
    if value is None:
        return None
    # Try JSON first
    try:
        return json.loads(value)
    except Exception:
        try:
            return value.decode("utf-8")
        except Exception:
            return str(value)


def build_points(topic: str, payload: Any, headers: Dict[str, str], ts_ms: int) -> List[Point]:
    # Measurement: derived from header 'type' if present, else topic
    # Tags: apartment (topic), plus all headers (string values only)
    # Fields: if payload is dict, numeric/bool/string fields; else 'value' field as string
    t_ns = int(ts_ms) * 1_000_000 if ts_ms is not None else None
    measurement = headers.get("type", topic)
    p = Point(measurement)
    # tag apartment/topic
    if topic:
        p = p.tag("apartment", topic)
    # tags from headers (limit size)
    for k, v in headers.items():
        if isinstance(v, str) and len(v) <= 256:  # basic guard
            p = p.tag(k, v)
    # fields
    if isinstance(payload, dict):
        has_field = False
        for k, v in payload.items():
            if isinstance(v, (int, float)):
                p = p.field(k, v)
                has_field = True
            elif isinstance(v, bool):
                p = p.field(k, v)
                has_field = True
            elif isinstance(v, str):
                # avoid exploding cardinality; only include short strings
                if len(v) <= 256:
                    p = p.field(k, v)
                    has_field = True
        if not has_field:
            p = p.field("value", json.dumps(payload))
    else:
        if payload is None:
            p = p.field("value", "")
        else:
            p = p.field("value", str(payload))
    if t_ns is not None:
        p = p.time(t_ns)
    return [p]


def create_consumer(bootstrap: str, group_id: str, auto_commit: bool, start_from_beginning: bool) -> Consumer:
    cfg = {
        "bootstrap.servers": bootstrap,
        "group.id": group_id,
        "enable.auto.commit": auto_commit,
        "auto.offset.reset": "earliest" if start_from_beginning else "latest",
    }
    return Consumer(cfg)


def seek_beginning_after_assignment(consumer: Consumer):
    # wait for assignment
    assignment = []
    for _ in range(50):
        consumer.poll(0.05)
        assignment = consumer.assignment()
        if assignment:
            break
    if assignment:
        for tp in assignment:
            consumer.seek(TopicPartition(tp.topic, tp.partition, OFFSET_BEGINNING))


def wait_for_kafka(consumer: Consumer, retries: int = 60, delay_sec: float = 1.0) -> None:
    for i in range(retries):
        try:
            md = consumer.list_topics(timeout=2.0)
            if md and md.topics is not None:
                return
        except Exception:
            pass
        time.sleep(delay_sec)
    print("Warning: Kafka metadata not available after waiting; continuing anyway")


def main():
    bootstrap = get_env("KAFKA_BOOTSTRAP", "kafka:29092")
    group_id = get_env("KAFKA_GROUP_ID", "influx-sink")

    influx_url = get_env("INFLUX_URL", "http://influxdb2:8086")
    influx_org = get_env("INFLUX_ORG", "dev")
    influx_bucket = get_env("INFLUX_BUCKET", "home")
    influx_token_file = get_env("INFLUX_TOKEN_FILE", "/run/secrets/influxdb2-admin-token")
    influx_token = read_secret_file(influx_token_file)

    start_from_beginning = env_bool("START_FROM_BEGINNING", True)
    auto_commit = env_bool("AUTO_COMMIT", False)
    commit_each = env_bool("COMMIT_EACH_MESSAGE", False)
    commit_interval = int(os.getenv("COMMIT_INTERVAL", "1"))
    verbose = env_bool("VERBOSE", False)

    consumer = create_consumer(bootstrap, group_id, auto_commit, start_from_beginning)

    # Ensure broker is reachable and optionally filter missing topics to avoid UNKNOWN_TOPIC_OR_PART crashes
    wait_for_kafka(consumer)
    try:
        cluster_topics = set(consumer.list_topics(timeout=5.0).topics.keys())
    except Exception:
        cluster_topics = set()

    # Discover topics dynamically: subscribe to all currently known topics
    subscribe_topics = sorted(cluster_topics) if cluster_topics else []
    if not subscribe_topics:
        print("No topics discovered from Kafka metadata at startup; waiting for producers to create topics.")
        consumer.subscribe([])
    else:
        consumer.subscribe(subscribe_topics)

    if start_from_beginning:
        seek_beginning_after_assignment(consumer)

    client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
    write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=2000))

    print(f"Influx sink started | subscribed={subscribe_topics if subscribe_topics else 'ALL'} | bucket={influx_bucket} org={influx_org} url={influx_url}")

    processed = 0
    # Periodic topic discovery and re-subscribe
    last_refresh = time.time()
    refresh_interval = int(os.getenv("TOPIC_REFRESH_SECONDS", "30"))
    try:
        while True:
            # Refresh topic list periodically
            if refresh_interval > 0 and (time.time() - last_refresh) >= refresh_interval:
                try:
                    md = consumer.list_topics(timeout=2.0)
                    new_topics = sorted(list(md.topics.keys())) if md and md.topics else []
                    if new_topics and new_topics != subscribe_topics:
                        subscribe_topics = new_topics
                        consumer.subscribe(subscribe_topics)
                        if verbose:
                            print(f"Updated subscription: {subscribe_topics}")
                except Exception as e:
                    if verbose:
                        print(f"Topic refresh failed: {e}")
                finally:
                    last_refresh = time.time()

            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                code = msg.error().code()
                if code == KafkaError._PARTITION_EOF:
                    if verbose:
                        print(f"EOF {msg.topic()}[{msg.partition()}] @ {msg.offset()}")
                    continue
                # Tolerate transient connectivity and missing topic errors
                if code in (getattr(KafkaError, '_ALL_BROKERS_DOWN', None), getattr(KafkaError, '_TRANSPORT', None)):
                    if verbose:
                        print(f"Kafka transport error: {msg.error()}")
                    continue
                if code == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    if verbose:
                        print(f"Unknown topic/partition: {msg.error()} (will retry)")
                    time.sleep(1.0)
                    continue
                # Otherwise, surface the error
                raise KafkaException(msg.error())

            hdrs = headers_to_dict(msg.headers())
            payload = parse_value(msg.value())
            ts = msg.timestamp()[1] if msg.timestamp() else None
            points = build_points(msg.topic(), payload, hdrs, ts)

            try:
                for p in points:
                    write_api.write(bucket=influx_bucket, record=p)
                processed += 1
                if verbose and (processed % 100 == 0):
                    print(f"Wrote {processed} points to Influx")
                # Manually commit if auto-commit is disabled and commit_each is enabled
                if (not auto_commit) and commit_each and (processed % max(1, commit_interval) == 0):
                    try:
                        consumer.commit(message=msg, asynchronous=True)
                    except Exception as ce:
                        if verbose:
                            print(f"Commit error: {ce}")
            except Exception as e:
                print(f"Write failed for {msg.topic()}[{msg.partition()}]@{msg.offset()}: {e}")

    except KeyboardInterrupt:
        print("Stopping sink...")
    finally:
        try:
            write_api.flush()
        except Exception:
            pass
        client.close()
        consumer.close()


if __name__ == "__main__":
    main()
