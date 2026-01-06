"""
MQTT to Kafka Bridge

Subscribes to MQTT topics and forwards messages to Kafka topics.

Topics mapping:
    MQTT: building/{apartment_id}/{room}/sensors  →  Kafka: sensor-data
    MQTT: building/weather                        →  Kafka: weather-data necessary for the external scores calculation
"""

import paho.mqtt.client as mqtt
import os
import json
import logging
import time
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def create_kafka_producer(retries: int = 10, delay: int = 5) -> KafkaProducer:
    """Create Kafka producer with retry logic."""
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            logger.info(f"✓ Connected to Kafka at {KAFKA_BROKER}")
            return producer
        except NoBrokersAvailable:
            logger.warning(f"Kafka not ready, retry {attempt + 1}/{retries}...")
            time.sleep(delay)
    
    raise RuntimeError(f"Could not connect to Kafka after {retries} attempts")


def get_kafka_topic(mqtt_topic: str) -> str:
    """Map MQTT topic to Kafka topic."""
    if mqtt_topic == "building/weather":
        return "weather-data"
    elif mqtt_topic.startswith("building/") and mqtt_topic.endswith("/sensors"):
        return "sensor-data"
    else:
        return "iot-unknown"


def get_message_key(mqtt_topic: str, payload: dict) -> str:
    """Generate Kafka message key for partitioning."""
    if "apartment_id" in payload:
        return payload["apartment_id"]
    return mqtt_topic


class MQTTKafkaBridge:
    """Bridge that forwards MQTT messages to Kafka."""
    
    def __init__(self):
        self.kafka_producer = create_kafka_producer()
        self.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="mqtt-kafka-bridge"
        )
        self.message_count = 0
        
        # Setup MQTT callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Called when connected to MQTT broker."""
        if reason_code == 0:
            logger.info(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            # Subscribe to all building topics
            client.subscribe("building/#")
            logger.info("✓ Subscribed to building/#")
        else:
            logger.error(f"MQTT connection failed: {reason_code}")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Called when disconnected from MQTT broker."""
        logger.warning(f"Disconnected from MQTT: {reason_code}")
    
    def on_message(self, client, userdata, msg):
        """Called when a message is received from MQTT."""
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode("utf-8"))
            
            # Determine Kafka topic
            kafka_topic = get_kafka_topic(msg.topic)
            
            # Add metadata
            payload["_mqtt_topic"] = msg.topic
            payload["_bridge_timestamp"] = datetime.now().isoformat()
            
            # Get message key
            key = get_message_key(msg.topic, payload)
            
            # Send to Kafka
            self.kafka_producer.send(kafka_topic, key=key, value=payload)
            
            self.message_count += 1
            if self.message_count % 100 == 0:
                logger.info(f"→ Forwarded {self.message_count} messages")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {msg.topic}: {e}")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
    
    def connect_mqtt(self, retries: int = 10, delay: int = 3):
        """Connect to MQTT broker with retry logic."""
        for attempt in range(retries):
            try:
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                return
            except ConnectionRefusedError:
                logger.warning(f"MQTT not ready, retry {attempt + 1}/{retries}...")
                time.sleep(delay)
        
        raise RuntimeError(f"Could not connect to MQTT after {retries} attempts")
    
    def run(self):
        """Start the bridge."""
        logger.info("=" * 50)
        logger.info("MQTT-KAFKA BRIDGE")
        logger.info("=" * 50)
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Kafka Broker: {KAFKA_BROKER}")
        logger.info("=" * 50)
        
        self.connect_mqtt()
        
        # Blocking loop
        try:
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.kafka_producer.close()
            self.mqtt_client.disconnect()


if __name__ == "__main__":
    bridge = MQTTKafkaBridge()
    bridge.run()
