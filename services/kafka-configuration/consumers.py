from confluent_kafka import Consumer, KafkaException, KafkaError
from confluent_kafka import TopicPartition, OFFSET_BEGINNING
import json
import os
import time

# Topics defined in topicgen.py
TOPICS = [
    "TemperatureReadings",
    "CO2",
    "CO",
    "COV",
    "Humidity",
    "PM25",
    "Presence",
    "Weather",
    "Window",
]

def create_consumer(bootstrap_servers: str = 'localhost:9092', group_id: str = 'cps-consumer-group', enable_auto_commit: bool = True):
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': enable_auto_commit,
    }
    return Consumer(consumer_config)

def load_config(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def _headers_match(msg_headers, expected_headers: dict) -> bool:
    if not expected_headers:
        return True
    if not msg_headers:
        return False
    # msg_headers is a list of tuples [(key, value_bytes), ...]
    kv = {}
    for k, v in msg_headers:
        try:
            kv[k] = v.decode('utf-8') if isinstance(v, (bytes, bytearray)) else (v if v is not None else '')
        except Exception:
            kv[k] = str(v) if v is not None else ''
    for ek, ev in expected_headers.items():
        if kv.get(ek) != str(ev):
            return False
    return True

def _seek_controls(consumer: Consumer, topics, from_beginning: bool, seek_timestamp_ms: int | None):
    # Wait for assignment
    assignment = []
    for _ in range(50):
        msg = consumer.poll(0.05)
        assignment = consumer.assignment()
        if assignment:
            break
    if not assignment:
        return
    if from_beginning:
        for tp in assignment:
            consumer.seek(TopicPartition(tp.topic, tp.partition, OFFSET_BEGINNING))
    elif seek_timestamp_ms is not None:
        # Query offsets for timestamp and seek
        tps = [TopicPartition(tp.topic, tp.partition, seek_timestamp_ms) for tp in assignment]
        offsets_for_times = consumer.offsets_for_times(tps, 5.0)
        for tp in offsets_for_times:
            if tp.offset >= 0:
                consumer.seek(tp)

def _headers_to_dict(msg_headers):
    if not msg_headers:
        return {}
    out = {}
    for k, v in msg_headers:
        try:
            out[k] = v.decode('utf-8') if isinstance(v, (bytes, bytearray)) else (v if v is not None else '')
        except Exception:
            out[k] = str(v) if v is not None else ''
    return out


def consume_messages(consumer, topics, headers_filter: dict | None = None, manual_commit: bool = False, from_beginning: bool = False, seek_timestamp_ms: int | None = None, verbose: bool = False):
    try:
        if isinstance(topics, str):
            topics = [topics]
        consumer.subscribe(list(topics))

        # Optional seek controls
        _seek_controls(consumer, topics, from_beginning=from_beginning, seek_timestamp_ms=seek_timestamp_ms)

        print(f"Consuming messages from topics: {', '.join(topics)}")
        if verbose:
            print(f"Headers filter: {headers_filter or {}} | manual_commit={manual_commit} | from_beginning={from_beginning} | seek_ts={seek_timestamp_ms}")
        while True:
            msg = consumer.poll(1.0)  # Timeout of 1 second
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                else:
                    raise KafkaException(msg.error())
            else:
                if not _headers_match(msg.headers(), headers_filter or {}):
                    if verbose:
                        actual_headers = _headers_to_dict(msg.headers())
                        print(f"Skipping message due to header filter. Expected {headers_filter}, got {actual_headers} at {msg.topic()}[{msg.partition()}]@{msg.offset()}")
                    continue

                value = msg.value()
                try:
                    value_str = value.decode('utf-8') if value is not None else ''
                except Exception:
                    value_str = str(value)
                if verbose:
                    print(f"{msg.topic()}[{msg.partition()}] @ {msg.offset()} | key={msg.key()} | headers={_headers_to_dict(msg.headers())}: {value_str}")
                else:
                    print(f"{msg.topic()}[{msg.partition()}] @ {msg.offset()}: {value_str}")

                if manual_commit:
                    # Commit the next offset for this partition
                    consumer.commit(msg)

    except KeyboardInterrupt:
        print("Consumer interrupted by user")
    finally:
        consumer.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="consumers.py",
        description=(
            "Kafka consumer runner that loads settings from a JSON file. "
            "Supports single or multi-consumer configs, header filtering, and offset controls (auto commit, manual commit, seek from beginning or timestamp)."
        ),
        epilog=(
            "Examples:\n"
            "  python3 services/kafka-configuration/consumers.py\n"
            "  python3 services/kafka-configuration/consumers.py --config services/kafka-configuration/consumer.config.json\n"
            "  python3 services/kafka-configuration/consumers.py --config services/kafka-configuration/consumer.multi.json --consumer window-events\n\n"
            "Config schemas:\n"
            "- Single consumer: { bootstrapServers, groupId, topics, headers?, offset? }\n"
            "- Multi consumer:  { bootstrapServers?, consumers: [ { name?, groupId, topics, headers?, offset? } ] }\n\n"
            "Offset options: { autoCommit: bool, fromBeginning: bool, commitEachMessage: bool, seekByTimestampMs: number|null }"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--config',
        default=os.path.join(os.path.dirname(__file__), 'consumer.config.json'),
        help=(
            'Path to consumer JSON config.\n'
            'Supports single schema or a multi-consumer schema under the "consumers" key.'
        )
    )
    parser.add_argument(
        '--consumer',
        default=None,
        help=(
            'Name of consumer to run when using a multi-consumer config.\n'
            'If omitted and the config defines multiple consumers, the script will list available names and exit.'
        )
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose logs (headers, skips, keys)'
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Support both single-consumer schema and multi-consumer schema
    consumers_cfg = cfg.get('consumers', None)
    if consumers_cfg:
        # Allow either list of objects (each with optional name) or dict keyed by name
        consumer_map = {}
        if isinstance(consumers_cfg, dict):
            consumer_map = consumers_cfg
        elif isinstance(consumers_cfg, list):
            for entry in consumers_cfg:
                name = entry.get('name') or entry.get('groupId') or f"consumer_{len(consumer_map)+1}"
                consumer_map[name] = entry
        else:
            raise ValueError("Invalid 'consumers' schema: must be list or object")

        if not args.consumer:
            names = ", ".join(sorted(consumer_map.keys()))
            print(f"Multiple consumers defined. Please select one with --consumer. Available: {names}")
            raise SystemExit(2)

        selected = consumer_map.get(args.consumer)
        if not selected:
            names = ", ".join(sorted(consumer_map.keys()))
            raise SystemExit(f"Consumer '{args.consumer}' not found. Available: {names}")

        bootstrap = selected.get('bootstrapServers', cfg.get('bootstrapServers', 'localhost:9092'))
        group_id = selected.get('groupId', 'cps-consumer-group')
        topics = selected.get('topics', TOPICS)
        headers = selected.get('headers', {})
        offset_cfg = selected.get('offset', {}) or {}
    else:
        bootstrap = cfg.get('bootstrapServers', 'localhost:9092')
        group_id = cfg.get('groupId', 'cps-consumer-group')
        topics = cfg.get('topics', TOPICS)
        headers = cfg.get('headers', {})
        offset_cfg = cfg.get('offset', {}) or {}

    enable_auto_commit = bool(offset_cfg.get('autoCommit', True))
    from_beginning = bool(offset_cfg.get('fromBeginning', False))
    manual_commit = bool(offset_cfg.get('commitEachMessage', False))
    seek_ts = offset_cfg.get('seekByTimestampMs', None)

    consumer = create_consumer(bootstrap_servers=bootstrap, group_id=group_id, enable_auto_commit=enable_auto_commit)
    consume_messages(
        consumer,
        topics,
        headers_filter=headers,
        manual_commit=manual_commit and not enable_auto_commit,
        from_beginning=from_beginning,
        seek_timestamp_ms=seek_ts,
        verbose=args.verbose
    )