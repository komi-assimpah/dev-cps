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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="topicgen.py",
        description="Create a single Kafka topic by name",
    )
    parser.add_argument('--bootstrap', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('name', help='Topic name to create')
    parser.add_argument('--partitions', type=int, default=1, help='Number of partitions')
    parser.add_argument('--replication', type=int, default=1, help='Replication factor')
    args = parser.parse_args()

    create_kafka_topic(args.bootstrap, args.name, args.partitions, args.replication)