"""
MQTT Publisher for Sensors Data on Mosquitto Broker

Publishes sensor data to MQTT topics in the format:
    building/{apartment_id}/{room}/sensors  →  Sensor readings
    building/weather                        →  Weather data
"""

import os
import json
import time
import logging
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MQTTPublisher:
    """Publishes sensor data to MQTT broker."""
    
    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"sensor-generator-{int(time.time())}"
        )
        self.broker = MQTT_BROKER
        self.port = MQTT_PORT
        self.connected = False
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
   
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"MQTT connection failed: {reason_code}")
        else:
            logger.info(f"✓ Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
   
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT: {reason_code}")
        self.connected = False
  

    def connect(self, retries: int = 5, delay: int = 2):
        for attempt in range(retries):
            try:
                self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                self.client.loop_start()
                
                for _ in range(10):
                    if self.connected:
                        return True
                    time.sleep(0.5)
            except ConnectionRefusedError:
                logger.warning(f"MQTT not ready, retry {attempt + 1}/{retries}...")
                time.sleep(delay)
        
        raise RuntimeError(f"Could not connect to MQTT broker at {self.broker}:{self.port}")

    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

    
    def publish_sensor_data(self, apartment_id: str, room: str, data: dict):
        topic = f"building/{apartment_id}/{room}/sensors"
        payload = json.dumps(data)
        result = self.client.publish(topic, payload, qos=1)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish to {topic}: {result.rc}")
            return False
        return True
    
    
    def publish_weather(self, data: dict):
        topic = "building/weather"
        payload = json.dumps(data)
        result = self.client.publish(topic, payload, qos=1)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish weather: {result.rc}")
            return False
        return True
