from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient


def print_current_topics(bootstrap_servers: str):
    admin = AdminClient({'bootstrap.servers': bootstrap_servers})
    md = admin.list_topics(timeout=10)
    topics = sorted(md.topics.keys())
    print("Available topics:")
    for t in topics:
        print(f"- {t}")


def choose_topic() -> str:
    return input("Enter the topic name: ").strip()


def parse_headers(headers_input: str):
    headers_list = []
    if not headers_input.strip():
        return headers_list
    parts = headers_input.split(",")
    for p in parts:
        item = p.strip()
        if not item:
            continue
        if "=" in item:
            k, v = item.split("=", 1)
        elif ":" in item:
            k, v = item.split(":", 1)
        else:
            k, v = item, ""
        headers_list.append((k.strip(), v.strip().encode("utf-8")))
    return headers_list


def create_message():
    key_in = input("Enter the message key (optional): ").strip()
    value_in = input("Enter the message value: ").strip()
    headers_in = input(
        "Enter headers as key=value pairs, comma-separated (e.g., a=1,b=2). Leave blank for none: "
    ).strip()
    key = key_in.encode("utf-8") if key_in else None
    value = value_in.encode("utf-8")
    headers = parse_headers(headers_in)
    return key, value, headers


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(
            f"Delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


def send_message(producer: Producer, topic: str, key, value, headers):
    producer.produce(
        topic=topic,
        key=key,
        value=value,
        headers=(headers if headers else None),
        on_delivery=delivery_report,
    )
    producer.flush(10)


def main():
    bootstrap_servers = "localhost:9092"  # Adjust this to your Kafka broker
    print_current_topics(bootstrap_servers)

    topic = choose_topic()
    key, value, headers = create_message()

    producer = Producer({'bootstrap.servers': bootstrap_servers})
    send_message(producer, topic, key, value, headers)


if __name__ == "__main__":
    main()