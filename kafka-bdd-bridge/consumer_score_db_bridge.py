import json
import calcul_scores.air_quality as IAQ
import calcul_scores.isolation as IIT
from confluent_kafka import Consumer, KafkaError
import psycopg2
import random
from datetime import datetime, timezone
import argparse
import logging
import os
import time
import numpy as np

# ======== DECLARATION DES ARGUMENTS ========

parser = argparse.ArgumentParser(
  prog='Kafka-consumer',
  description='Prend les donnees du topic Kafka APT_10x pour calculer les scores IAQ_2h et IIT_2h et les envoyer a la BDD'
)

parser.add_argument('APT_ID', 
                    type = int, 
                    help = 'le dernier chiffre de l\'identifiant de l\'appartement',
                    default = 1
                    )

# ======== DECLARATION DES ARGUMENTS ========


# ======== CONFIG DES SERVICES ========

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "monuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "monpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "sensor_scores")

conf = {
  'bootstrap.servers': KAFKA_BROKER,
  'group.id': 'mygroup',
  'auto.offset.reset': 'latest'
}

db_params = {
  "host": DB_HOST,
  "port": DB_PORT,
  "database": POSTGRES_DB,
  "user": POSTGRES_USER,
  "password": POSTGRES_PASSWORD
}

# ======== CONFIG DES SERVICES ========

# ======== SETUP VARIABLES ========

MAX_LEN_QUEUES = 12

apt_id = 0

client_iaq = IAQ.CLIENT_AIR_QUALITY()
client_iit = IIT.CLIENT_ISOLATION_SCORE()

timestamp_queue = list()
temp_queue = list()
humid_queue = list()
co2_queue = list()
co_queue = list()
pm25_queue = list()
tvoc_queue = list()
DATA_TYPES = ["temperature", "humidity", "co2", "pm25", "co", "tvoc", "temp_ext", "energy_kwh"]

# ======== SETUP VARIABLES ========

# ======== COMMUNICATION BDD ========

def send_bdd(timestamp, iaq_2h=0.0, iit=100.0):
  global apt_id
  try:
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    insert_query = """
    INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(%s), %s, %s, %s);
    """
    cur.execute(insert_query, (timestamp, apt_id, iaq_2h, iit))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Envoi des données vers la bdd : timestamp : {timestamp} apt_id : {apt_id} IAQ_2h : {iaq_2h} IIT_2h : {iit}")
  except Exception as e:
    logger.error(f"{e}")

# ======== COMMUNICATION BDD ========

# ======== MANIP QUEUES ========

def empty_queues():
  global timestamp_queue, temp_queue, humid_queue, co2_queue, co_queue, pm25_queue, tvoc_queue
  timestamp_queue = list()
  temp_queue = list()
  humid_queue = list()
  co2_queue = list()
  co_queue = list()
  pm25_queue = list()
  tvoc_queue = list()

def read_json(json_data):
  global timestamp_queue, temp_queue, humid_queue, co2_queue, co_queue, pm25_queue, tvoc_queue
  timestamp_queue.append(json_data["timestamp"])
  temp_queue.append(json_data["temperature"])
  humid_queue.append(json_data["humidity"])
  co2_queue.append(json_data["co2"])
  co_queue.append(json_data["co"])
  pm25_queue.append(json_data["pm25"])
  tvoc_queue.append(json_data["tvoc"])

def avg(data: list) -> float:
  count = len(data) - data.count(None)
  if count == 0: return None
  mean = sum(dat for dat in data if dat != None)/count
  return round(mean, 3)

# ======== MANIP QUEUES ========

# ======== DATA PAR TIMESTAMP ========

raw_data = dict()
avg_data = dict()

# ======== DATA PAR TIMESTAMP ========


def main():
  global timestamp_queue, temp_queue, humid_queue, co2_queue, co_queue, pm25_queue, tvoc_queue, apt_id
  global raw_data
  
  def get_appropriate_tsmp(timestamp):
    for key in avg_data.keys():
      if timestamp - key <= 6600:
        return key
    return timestamp

  def insert_into_dict(values: dict, value: float, key1: int, key2: float):
    try:
      try:
        values[key1][key2].append(value)
      except:
        values[key1][key2] = [value]
    except:
      values[key1] = dict()
      values[key1][key2] = [value]

  try:
    while True:

      msg = c.poll(0.2)
      
      if msg is None: logger.info(f"Attente de messages")
      elif msg.error(): logger.error(f"{msg.error()}")
      
      else :
        room = msg.topic().split('.')[1]
        logger.info(f"Données reçues du topic {msg.topic()}")
        logger.info(f"Données reçues : {msg.value()}")
        
        data_bytes = msg.value()
        data_str = data_bytes.decode('utf-8')
        data = json.loads(data_str)

        # tsmp = get_appropriate_tsmp(data["timestamp"])

        for i in DATA_TYPES:
          insert_into_dict(raw_data, data[i], data["timestamp"], i)
          if len(raw_data[data["timestamp"]][i]) == 5:
            tsmp = get_appropriate_tsmp(data["timestamp"])
            insert_into_dict(avg_data, avg(raw_data[data["timestamp"]][i]), tsmp, i)
        
        tstmp_to_remove = list()

        for tstmp in avg_data.keys():
          if len(avg_data[tstmp]["co2"]) == 12:
            iit_2h = client_iit.IIT_2h(avg_data[tstmp]["energy_kwh"], 60, avg_data[tstmp]["temperature"], avg_data[tstmp]["temp_ext"])
            iaq_2h = client_iaq.IAQ(avg_data[tstmp]["co2"], avg_data[tstmp]["co"], "", avg_data[tstmp]["pm25"], avg_data[tstmp]["tvoc"])
            logger.info(f"Nouvel IAQ_2H calculé : {iaq_2h}")
            logger.info(f"Nouvel IIT calculé : {iit_2h}")
            tstmp_to_remove.append(tstmp)
            send_bdd(tstmp, float(iaq_2h), float(iit_2h))
        
        for t in tstmp_to_remove:
          avg_data.pop(t)

  except KeyboardInterrupt:
    pass

  finally:
    c.close()

if __name__ == "__main__":
  args = parser.parse_args()
  apt_id = args.APT_ID

  logger = logging.getLogger("Kafka to Client score bridge")

  logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] [%(levelname)s] %(message)s"
  )

  # ======== CONFIG KAFKA ========

  for attempt in range(1,11):
    try:
      c = Consumer(conf)
      logger.info(f" Connected to Kafka at {KAFKA_BROKER}")
      break
    except KafkaError.NoBrokersAvailable:
      logger.warning(f"Kafka not ready, retry {attempt}/{10}...")
      time.sleep(2)
  
  topics = list()
  for i in ["cuisine","salon","sdb","chambre_1","chambre_2"]:
    topics.append(f"APT_10{apt_id}.{i}.score_data")
  
  not_connected = True
  while not_connected:
    try:
      c.subscribe(topics)
      # On récupère les métadonnées du cluster
      cluster_metadata = c.list_topics(timeout=5.0)
      
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
  # c.subscribe(topic)

  # ======== CONFIG KAFKA ========



  client_iaq = IAQ.CLIENT_AIR_QUALITY()

  # log_file = open(datetime.now().strftime("%d%m%Y_%H%M%S")+".log", 'a')
  main()