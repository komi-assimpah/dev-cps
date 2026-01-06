from confluent_kafka.admin import AdminClient, NewTopic


def create_kafka_topic(bootstrap_servers: str, topic_name: str, num_partitions: int, replication_factor: int):
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    topic = NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)

    try:
        result = admin_client.create_topics([topic])
        for t, future in result.items():
            try:
                future.result()  # Wait for operation to finish
                print(f"Topic '{t}' created successfully.")
            except Exception as e:
                print(f"Failed to create topic '{t}': {e}")
    except Exception as e:
        print(f"Error while creating topic: {e}")


def list_kafka_topics(bootstrap_servers: str):
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    md = admin_client.list_topics(timeout=10)
    topics = md.topics if md else {}
    if not topics:
        print("No topics found.")
        return
    print("Topics:")
    for name in sorted(topics.keys()):
        t = topics[name]
        pcount = len(t.partitions) if hasattr(t, 'partitions') and t.partitions else 0
        print(f"- {name} (partitions: {pcount})")


def delete_kafka_topic(bootstrap_servers: str, topic_name: str, timeout: int = 30):
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    try:
        fs = admin_client.delete_topics([topic_name], operation_timeout=timeout)
        for t, f in fs.items():
            try:
                f.result()
                print(f"Topic '{t}' deleted successfully.")
            except Exception as e:
                print(f"Failed to delete topic '{t}': {e}")
    except Exception as e:
        print(f"Error while deleting topic: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="topicgen.py",
        description="Kafka topic utility: create, list, or delete topics.",
        epilog=(
            "Examples:\n"
            "  # List topics\n"
            "  python3 services/kafka-configuration/topicgen.py --list\n\n"
            "  # Create a topic\n"
            "  python3 services/kafka-configuration/topicgen.py MyApartment --partitions 3 --replication 1\n\n"
            "  # Delete a topic\n"
            "  python3 services/kafka-configuration/topicgen.py --delete MyApartment\n"
        ),
    )
    parser.add_argument('--bootstrap', default='localhost:9092', help='Kafka bootstrap servers (default: localhost:9092)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list', '-l', action='store_true', help='List all topics and exit')
    group.add_argument('--delete', '-d', metavar='NAME', help='Delete the specified topic')
    parser.add_argument('name', nargs='?', help='Topic name to create (used when not listing or deleting)')
    parser.add_argument('--partitions', type=int, default=1, help='Number of partitions (create only)')
    parser.add_argument('--replication', type=int, default=1, help='Replication factor (create only)')
    args = parser.parse_args()

    if args.list:
        list_kafka_topics(args.bootstrap)
        raise SystemExit(0)

    if args.delete:
        delete_kafka_topic(args.bootstrap, args.delete)
        raise SystemExit(0)

    if not args.name:
        parser.error("a topic NAME is required for creation when not using --list or --delete")

    create_kafka_topic(args.bootstrap, args.name, args.partitions, args.replication)