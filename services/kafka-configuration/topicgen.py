from confluent_kafka.admin import AdminClient, NewTopic

def create_kafka_topic(bootstrap_servers, topic_name, num_partitions, replication_factor):
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    topic = NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)

    try:
        # Create the topic
        result = admin_client.create_topics([topic])
        for topic, future in result.items():
            try:
                future.result()  # Wait for operation to finish
                print(f"Topic '{topic}' created successfully.")
            except Exception as e:
                print(f"Failed to create topic '{topic}': {e}")
    except Exception as e:
        print(f"Error while creating topic: {e}")

if __name__ == "__main__":
    # Kafka broker address
    bootstrap_servers = "localhost:9092"
    # Topic configuration
    topic_name = ["TemperatureReadings","CO2","CO","COV","Humidity","PM25","Presence","Weather","Window"]
    num_partitions = 1
    replication_factor = 1

    for name in topic_name:
        create_kafka_topic(bootstrap_servers, name, num_partitions, replication_factor)