from confluent_kafka import Consumer, KafkaException, KafkaError

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

def create_consumer(bootstrap_servers: str = 'localhost:9092', group_id: str = 'cps-consumer-group'):
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
    }
    return Consumer(consumer_config)

def consume_messages(consumer, topics):
    try:
        # Subscribe to topic list
        if isinstance(topics, str):
            topics = [topics]
        consumer.subscribe(list(topics))

        print(f"Consuming messages from topics: {', '.join(topics)}")
        while True:
            # Poll for messages
            msg = consumer.poll(1.0)  # Timeout of 1 second

            if msg is None:
                continue  # No message received, continue polling
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    print(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                # Successfully received a message
                value = msg.value()
                try:
                    value_str = value.decode('utf-8') if value is not None else ''
                except Exception:
                    value_str = str(value)
                print(
                    f"{msg.topic()}[{msg.partition()}] @ {msg.offset()}: {value_str}"
                )

    except KeyboardInterrupt:
        print("Consumer interrupted by user")

    finally:
        # Close the consumer to commit final offsets and clean up resources
        consumer.close()

if __name__ == "__main__":
    consumer = create_consumer()
    consume_messages(consumer, TOPICS)