"""
MQTT to Kafka Bridge (Bidirectional + Filtering)

- Upstream: MQTT (Sensors) -> Kafka (sensor-data AND APT_10x.room)
- Downstream: Kafka (Heating Commands) -> MQTT (Actuators)

Topics mapping:
  MQTT: building/{apartment_id}/{room}/sensors  →  Kafka: sensor-data
  MQTT: building/weather                        →  Kafka: weather-data necessary
  Kafka: heating-commands                       →  MQTT: building/{apartment_id}/{room}/heater/set

Features:
- Median Filtering on sensor data (De-noising)
- Dual Publishing: 
    1. sensor-data (Global, JSON enriched) -> For MongoDB/Global Services
    2. APT_10x.{room} (Specific) -> For TimescaleDB Legacy Bridge
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

from utils import cleaner
from utils import json_formatter

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

HISTORY_MAX_DEPTH = 50
DATA_TYPES = ["temperature", "humidity", "co2", "pm25", "co", "tvoc"]


def create_kafka_producer(retries: int = 10, delay: int = 5) -> KafkaProducer:
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v, default=json_formatter.encoder).encode("utf-8"),
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


class MQTTKafkaBridge:
    """Bidirectional Bridge with Filtering."""  
    
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
        
        # Filtering State: history[room][data_type] = [list of values]
        self.history = dict()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"MQTT connection failed: {reason_code}")
        else:
            logger.info(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe("building/#")
            logger.info("Subscribed to building/#")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT: {reason_code}")
        
    def _apply_filter(self, room, data_type, value):
        """Applies median filter to the value using history."""
        if room not in self.history:
            self.history[room] = dict()
        if data_type not in self.history[room]:
            self.history[room][data_type] = list()
        
        try:
            value = cleaner.clean_none_value(value, self.history[room][data_type])
            
            (filtered_value, outlier) = cleaner.median_filter(value, data_type, self.history[room][data_type])
            
            if outlier is not None:
                logger.debug(f"[{room}] Outlier detected for {data_type}: {outlier} -> replaced by {filtered_value}")
          
            if len(self.history[room][data_type]) > HISTORY_MAX_DEPTH:
                 self.history[room][data_type] = self.history[room][data_type][-HISTORY_MAX_DEPTH:]
                 
            return filtered_value
            
        except Exception as e:
            logger.error(f"Error filtering {data_type} for {room}: {e}")
            return value

    def on_message(self, client, userdata, msg):
        """MQTT -> Kafka"""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if msg.topic == "building/weather":
                self.kafka_producer.send("weather-data", key="weather", value=payload)
            
            elif msg.topic.startswith("building/") and msg.topic.endswith("/sensors"):
                parts = msg.topic.split('/')
                if len(parts) == 4:
                    apartment_id = parts[1]
                    room = parts[2]
                    
                    filtered_payload = payload.copy()
                    
                    for dtype in DATA_TYPES:
                        if dtype in payload:
                            raw_val = payload[dtype]
                            filtered_val = self._apply_filter(room, dtype, raw_val)
                            filtered_payload[dtype] = filtered_val
                    
                    # --- DUAL PUBLISHING ---
                    # Target 1: Global 'sensor-data' (Agregated)
                    final_global_payload = filtered_payload.copy()
                    final_global_payload["apartment_id"] = apartment_id
                    final_global_payload["room"] = room
                    final_global_payload["_mqtt_topic"] = msg.topic
                    
                    key = apartment_id
                    self.kafka_producer.send("sensor-data", key=key, value=final_global_payload)
                    
                    # Target 2: Specific 'APT_ID.room' (Legacy/Timescale)
                    legacy_topic = f"{apartment_id}.{room}"
                    
                    # Legacy consumer expects timestamp as Integer (Unix Timestamp)
                    legacy_payload = filtered_payload.copy()
                    if isinstance(legacy_payload.get("timestamp"), str):
                         try:
                             legacy_payload["timestamp"] = int(datetime.fromisoformat(legacy_payload["timestamp"]).timestamp())
                         except ValueError:
                             pass # Keep as is if parsing fails

                    self.kafka_producer.send(legacy_topic, key=room, value=legacy_payload)
                    
                    self.message_count += 1
                    if self.message_count % 50 == 0:
                        logger.info(f"→ Processed {self.message_count} sensor messages")

            else:
                pass
            
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
                    
                    apt_id = payload.get("apartment_id")
                    room = payload.get("room", "all")
                    action = payload.get("action")
                    
                    if apt_id and action:
                        if room == "all":
                            mqtt_topic = f"building/{apt_id}/+/heater/set"
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
        logger.info("MQTT-KAFKA-BRIDGE (BIDIRECTIONAL + FILTERING)")
        logger.info("=" * 50)
        
        self.connect_mqtt()
        
        kafka_thread = threading.Thread(target=self.consume_kafka_loop, daemon=True)
        kafka_thread.start()
        
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