"""
MQTT to Kafka Bridge (Bidirectional)

- Upstream: MQTT (Sensors) -> Kafka (sensor-data)
- Downstream: Kafka (Heating Commands) -> MQTT (Actuators)

Topics mapping:
    MQTT: building/{apartment_id}/{room}/sensors  →  Kafka: sensor-data
    MQTT: building/weather                        →  Kafka: weather-data necessary for the external scores calculation
    Kafka: heating-commands                       →  MQTT: building/{apartment_id}/{room}/heater/set
"""

import paho.mqtt.client as mqtt
import os
import json
import logging
import time
import threading
from datetime import datetime

from kafka import KafkaProducer, KafkaConsumer
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
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            logger.info(f"✓ Producer connected to Kafka at {KAFKA_BROKER}")
            return producer
        except NoBrokersAvailable:
            logger.warning(f"Kafka not ready, retry {attempt + 1}/{retries}...")
            time.sleep(delay)
    
    raise RuntimeError(f"Could not connect Producer to Kafka")

def create_kafka_consumer(topic: str, retries: int = 10, delay: int = 5) -> KafkaConsumer:
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id="bridge-consumer-group",
                auto_offset_reset='latest'
            )
            logger.info(f"✓ Consumer connected to Kafka topic '{topic}'")
            return consumer
        except NoBrokersAvailable:
            logger.warning(f"Kafka Consumer not ready, retry {attempt + 1}/{retries}...")
            time.sleep(delay)
            
    raise RuntimeError(f"Could not connect Consumer to Kafka")


def get_kafka_topic(mqtt_topic: str) -> str:
    """Map MQTT topic to Kafka topic ."""
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
    """Bidirectional Bridge."""  
    
    def __init__(self):
        # MQTT Client
        self.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="mqtt-kafka-bridge"
        )
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        self.kafka_producer = create_kafka_producer()
        self.kafka_consumer = create_kafka_consumer("heating-commands")
        
        self.running = True
        self.message_count = 0

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"MQTT connection failed: {reason_code}")
        else:
            logger.info(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe("building/#")
            logger.info("Subscribed to building/#")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT: {reason_code}")
        
    def on_message(self, client, userdata, msg):
        """MQTT -> Kafka"""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            kafka_topic = get_kafka_topic(msg.topic)
            
            payload["_mqtt_topic"] = msg.topic
            payload["_bridge_timestamp"] = datetime.now().isoformat()
            
            key = get_message_key(msg.topic, payload)
            self.kafka_producer.send(kafka_topic, key=key, value=payload)
            
            self.message_count += 1
            if self.message_count % 100 == 0:
                logger.info(f"→ Forwarded {self.message_count} messages to Kafka")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {msg.topic}: {e}")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
    
    def consume_kafka_loop(self):
        """Kafka -> MQTT"""
        logger.info("Starting Kafka Consumer Loop...")
        try:
            for msg in self.kafka_consumer:
                if not self.running: break
                
                try:
                    payload = msg.value
                    logger.info(f"← Received command from Kafka: {payload}")
                    
                    # Attend un payload du type: {"apartment_id": "APT_101", "room": "salon", "action": "START_NOW", ...}
                    apt_id = payload.get("apartment_id")
                    room = payload.get("room", "all")
                    action = payload.get("action")
                    
                    if apt_id and action:
                        # Construction du topic MQTT de commande
                        if room == "all":
                            #TODO: Send all rooms commands
                            mqtt_topic = f"building/{apt_id}/salon/heater/set"
                        else:
                            mqtt_topic = f"building/{apt_id}/{room}/heater/set"
                        
                        mqtt_payload = json.dumps({"action": action, "ts": datetime.now().isoformat()})
                        self.mqtt_client.publish(mqtt_topic, mqtt_payload)
                        logger.info(f"← Published to MQTT {mqtt_topic}: {mqtt_payload}")
                        
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka Consumer crashed: {e}")
    
    def connect_mqtt(self, retries: int = 10, delay: int = 3):
        for attempt in range(retries):
            try:
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                return
            except ConnectionRefusedError:
                logger.warning(f"MQTT not ready, retry {attempt + 1}/{retries}...")
                time.sleep(delay)
        raise RuntimeError(f"Could not connect to MQTT after {retries} attempts")
    
    def run(self):
        """Start the bridge (MQTT Loop + Kafka Thread)."""
        logger.info("=" * 50)
        logger.info("MQTT-KAFKA-BRIDGE (BIDIRECTIONAL)")
        logger.info("=" * 50)
        
        self.connect_mqtt()
        
        # Lancer le consommateur Kafka dans un thread séparé
        kafka_thread = threading.Thread(target=self.consume_kafka_loop, daemon=True)
        kafka_thread.start()
        
        # Boucle principale MQTT (Bloquante)
        try:
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.running = False
        finally:
            self.kafka_producer.close()
            self.kafka_consumer.close()
            self.mqtt_client.disconnect()


if __name__ == "__main__":
    bridge = MQTTKafkaBridge()
    bridge.run()
