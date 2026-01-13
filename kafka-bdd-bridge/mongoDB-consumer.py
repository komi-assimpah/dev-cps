"""
Kafka to MongoDB Consumer

Lit les données capteurs du topic Kafka 'sensor-data' et les stocke dans MongoDB.
"""

import json
import os
import time
import logging
from confluent_kafka import Consumer, KafkaError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

# ======== CONFIG ========

KAFKA_CONFIG = {
    'bootstrap.servers': os.getenv('KAFKA_BROKER', 'localhost:9092'),
    'group.id': 'mongodb-consumer-group',
    'auto.offset.reset': 'latest'
}

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'iot_building')

KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'sensor-data')

# ======== CONFIG ========

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ======== CONNEXION MONGODB ========

def connect_mongo(retries=10, delay=5):
    for attempt in range(retries):
        try:
            client = MongoClient(MONGO_URI)
            client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB at {MONGO_URI}")
            return client
        except ConnectionFailure:
            logger.warning(f"MongoDB not ready, retry {attempt + 1}/{retries}...")
            time.sleep(delay)
    
    raise RuntimeError(f"Could not connect to MongoDB after {retries} attempts")


def connect_kafka(retries=10, delay=5):
    for attempt in range(retries):
        try:
            consumer = Consumer(KAFKA_CONFIG)
            consumer.subscribe([KAFKA_TOPIC])
            logger.info(f"✓ Connected to Kafka, subscribed to '{KAFKA_TOPIC}'")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka not ready, retry {attempt + 1}/{retries}... ({e})")
            time.sleep(delay)
    
    raise RuntimeError(f"Could not connect to Kafka after {retries} attempts")

# ======== CONNEXION MONGODB ========


# ======== INSERTION MONGODB ========

def get_collection_name(apartment_id: str) -> str:
    """Génère le nom de collection basé sur l'apartment_id."""
    if apartment_id:
        return f"sensor_{apartment_id.lower()}"  # APT_101 → sensor_apt_101
    return "sensor_unknown"


def insert_sensor_data(db, data):
    """Insère un document capteur dans la collection de l'appartement."""
    # Convertir timestamp string en datetime si présent
    if 'timestamp' in data and isinstance(data['timestamp'], str):
        try:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        except ValueError:
            pass
    
    # Déterminer la collection (1 par appartement)
    apartment_id = data.get('apartment_id', 'unknown')
    collection_name = get_collection_name(apartment_id)
    collection = db[collection_name]
    
    collection.insert_one(data)

# ======== INSERTION MONGODB ========


# ======== MAIN ========

def main():
    logger.info("=" * 50)
    logger.info("KAFKA TO MONGODB CONSUMER")
    logger.info("=" * 50)
    logger.info(f"Kafka: {KAFKA_CONFIG['bootstrap.servers']}")
    logger.info(f"Topic: {KAFKA_TOPIC}")
    logger.info(f"MongoDB: {MONGO_URI}/{MONGO_DATABASE}.<collection_par_appart>")
    logger.info("=" * 50)
    
    mongo_client = connect_mongo()
    db = mongo_client[MONGO_DATABASE]
    
    consumer = connect_kafka()
    
    message_count = 0
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Kafka error: {msg.error()}")
                continue
            
            try:
                data = json.loads(msg.value().decode('utf-8'))
                insert_sensor_data(db, data)
                
                message_count += 1
                if message_count % 100 == 0:
                    logger.info(f"→ Inserted {message_count} documents into MongoDB")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error inserting document: {e}")
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    
    finally:
        consumer.close()
        mongo_client.close()
        logger.info(f"Total documents inserted: {message_count}")

# ======== MAIN ========


if __name__ == "__main__":
    main()
