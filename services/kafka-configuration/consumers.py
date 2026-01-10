from confluent_kafka import Consumer, KafkaException, KafkaError
from confluent_kafka import TopicPartition, OFFSET_BEGINNING
import os
import time

def create_consumer(bootstrap_servers: str = 'localhost:9092', group_id: str = 'cps-consumer-group', enable_auto_commit: bool = True):
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': enable_auto_commit,
    }
    return Consumer(consumer_config)

# JSON config ingestion removed; CLI-only configuration

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
            "Kafka consumer runner (CLI-only). "
            "Choose topics interactively or via --topic; supports header filtering and offset controls (auto commit, manual commit, seek from beginning or timestamp)."
        ),
        epilog=(
            "Examples:\n"
            "  python3 services/kafka-configuration/consumers.py --bootstrap localhost:9092 --group-id demo --topic X --from-beginning\n"
            "  python3 services/kafka-configuration/consumers.py --list-topics\n\n"
            "Offset options: use --from-beginning, --manual-commit, and --seek-ts-ms for timestamp seek."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--bootstrap', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('--group-id', default='cps-consumer-group', help='Kafka consumer group id')
    parser.add_argument('--from-beginning', action='store_true', help='Seek to beginning after assignment')
    parser.add_argument('--manual-commit', action='store_true', help='Commit offsets manually after each message')
    parser.add_argument('--seek-ts-ms', type=int, default=None, help='Seek to offsets by timestamp (Unix epoch ms)')
    parser.add_argument('--headers', default='', help='Header filter as key=value pairs separated by commas (e.g., a=b,room=kitchen)')
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose logs (headers, skips, keys)'
    )
    # Removed --topic; selection is done dynamically from broker metadata
    parser.add_argument(
        '--list-topics', action='store_true', help='List available topics and exit'
    )
    args = parser.parse_args()
    # Parse headers filter from CLI
    headers = {}
    if args.headers:
        for pair in args.headers.split(','):
            pair = pair.strip()
            if not pair:
                continue
            if '=' in pair:
                k, v = pair.split('=', 1)
                headers[k.strip()] = v.strip()
            else:
                headers[pair] = ''

    bootstrap = args.bootstrap
    group_id = args.group_id
    enable_auto_commit = not args.manual_commit
    from_beginning = args.from_beginning
    manual_commit = args.manual_commit
    seek_ts = args.seek_ts_ms

    consumer = create_consumer(bootstrap_servers=bootstrap, group_id=group_id, enable_auto_commit=enable_auto_commit)

    # Discover topics from broker
    try:
        md = consumer.list_topics(timeout=5.0)
        broker_topics = sorted(list(md.topics.keys())) if md and md.topics else []
    except Exception:
        broker_topics = []

    if args.list_topics:
        print("Available topics:")
        for t in broker_topics:
            print(f"- {t}")
        consumer.close()
        raise SystemExit(0)

    # Prompt user to choose a topic dynamically from broker metadata
    selected_topics = None
    if broker_topics:
        print("Topics on broker:")
        for idx, t in enumerate(broker_topics):
            print(f"  [{idx}] {t}")
        inp = input("Select topic index: ").strip()
        try:
            i = int(inp)
            if 0 <= i < len(broker_topics):
                selected_topics = broker_topics[i]
                print(f"Selected topic: {selected_topics}")
            else:
                raise ValueError("Index out of range")
        except Exception:
            print("Invalid selection. Exiting.")
            consumer.close()
            raise SystemExit(2)
    else:
        print("No topics available from broker metadata. Exiting.")
        consumer.close()
        raise SystemExit(2)

    consume_messages(
        consumer,
        selected_topics,
        headers_filter=headers,
        manual_commit=manual_commit and not enable_auto_commit,
        from_beginning=from_beginning,
        seek_timestamp_ms=seek_ts,
        verbose=args.verbose
    )