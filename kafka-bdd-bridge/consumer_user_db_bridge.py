"""
Kafka to MongoDB Consumer

Lit les données capteurs du topic Kafka 'sensor-data' et les stocke dans MongoDB.
"""

import json
import os
import time
import logging
import argparse
from confluent_kafka import Consumer, KafkaError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

parser = argparse.ArgumentParser(
  prog='Kafka-consumer',
  description='Prend les donnees du topic Kafka APT_10x pour calculer les scores IAQ_2h et IIT_2h et les envoyer a la BDD'
)

parser.add_argument('APT_ID', 
                    type = int, 
                    help = 'le dernier chiffre de l\'identifiant de l\'appartement',
                    default = 1
                    )


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
  format="[%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Kafka to MongoDB bridge")


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
      topics = list()
      for i in ["cuisine","salon","sdb","chambre_1","chambre_2"]:
        topics.append(f"APT_10{apt_id}.{i}.score_data")
        topics.append(f"APT_10{apt_id}.{i}.extra_data")

      not_connected = True
      while not_connected:
        try:
          consumer.subscribe(topics)
          # On récupère les métadonnées du cluster
          cluster_metadata = consumer.list_topics(timeout=5.0)
          
          # On vérifie si TOUS nos topics sont connus du broker
          topics_sur_broker = cluster_metadata.topics.keys()
          manquants = [t for t in topics if t not in topics_sur_broker]
          
          if not manquants:
            logger.info(f"Tous les topics sont validés sur le broker.")
            not_connected = False
          else:
            logger.warning(f"Topics manquants sur le broker : {manquants}")
            time.sleep(2)
                
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification : {e}")
            time.sleep(2)

      logger.info(f"✓ Connected to Kafka")
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


def insert_sensor_data(db, data, apartment_id, room):
  """Insère un document capteur dans la collection de l'appartement."""
  # Convertir timestamp string en datetime si présent
  if 'timestamp' in data and isinstance(data['timestamp'], str):
    try:
      data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    except ValueError:
      pass
  
  data["room"] = room

  # Déterminer la collection (1 par appartement)
  collection_name = get_collection_name(apartment_id)
  collection = db[collection_name]

  query_filter = {
    "timestamp": data.get('timestamp'),
    "room": data.get('room')  # Assure-toi que la clé s'appelle bien 'room' dans ton JSON
  }

  update_action = {
    "$set": data
  }

  collection.update_one(query_filter, update_action, upsert=True)
  
  # collection.update_one(data, upsert=True)

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
        appartment_id = msg.topic().split('.')[0]
        room = msg.topic().split('.')[1]
        data = json.loads(msg.value().decode('utf-8'))
        insert_sensor_data(db, data, appartment_id, room)
        
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
  args = parser.parse_args()
  apt_id = args.APT_ID
  main()
