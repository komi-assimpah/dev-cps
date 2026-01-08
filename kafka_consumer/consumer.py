import json
import calcul_scores.air_quality as IAQ
from confluent_kafka import Consumer, KafkaError
import psycopg2
import random
from datetime import datetime, timezone
import argparse


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

conf = {
  'bootstrap.servers': 'localhost:9092',
  'group.id': 'mygroup',
  'auto.offset.reset': 'latest'
}

db_params = {
  "host": "localhost",
  "database": "sensor_scores",
  "user": "monuser",
  "password": "monpassword"
}

# ======== CONFIG DES SERVICES ========

# ======== SETUP VARIABLES ========

MAX_LEN_QUEUES = 12

apt_id = 0

client_iaq = IAQ.CLIENT_AIR_QUALITY()

timestamp_queue = list()
temp_queue = list()
humid_queue = list()
co2_queue = list()
co_queue = list()
pm25_queue = list()
tvoc_queue = list()

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
    print(f"[SUCCESS] Envoi des données vers la bdd : timestamp : {timestamp} apt_id : {apt_id} IAQ_2h : {iaq_2h} IIT_2h : {iit}")
  except Exception as e:
    print(f"[ERROR] {e}")

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

# ======== MANIP QUEUES ========

def main():
  global timestamp_queue, temp_queue, humid_queue, co2_queue, co_queue, pm25_queue, tvoc_queue, apt_id
  
  try:
    while True:

      msg = c.poll(0.2)
      
      if msg is None: print(f"[INFO] Attente de messages")
      elif msg.error(): print(f"[ERROR] {msg.error()}")
      
      else :
        print(f"[INFO] Données reçues du topic {msg.topic()} : {msg.key().decode('utf-8')}")
        
        # lire et decoder les valeurs
        data_bytes = msg.value()
        data_str = data_bytes.decode('utf-8')
        data_dict = json.loads(data_str)
        
        # mettre a jour les queues
        read_json(data_dict)
        
        # une fois qu'on a 12 valeurs dans les queues
        if (len(timestamp_queue) == 12):
          # on calcule les scores
          IAQ_2h = client_iaq.IAQ(co2_queue, co_queue, "", pm25_queue, tvoc_queue)
          # IIT_2h = ....

          # on envoie a la bdd et on vide les queues
          send_bdd(timestamp_queue[0], IAQ_2h, random.uniform(0.0, 100.0))
          empty_queues()

  except KeyboardInterrupt:
    pass

  finally:
    c.close()

if __name__ == "__main__":
  args = parser.parse_args()
  apt_id = args.APT_ID

  # ======== CONFIG KAFKA ========

  c = Consumer(conf)
  topic = "APT_10"+str(apt_id)
  c.subscribe([topic])

  # ======== CONFIG KAFKA ========

  client_iaq = IAQ.CLIENT_AIR_QUALITY()

  # log_file = open(datetime.now().strftime("%d%m%Y_%H%M%S")+".log", 'a')
  main()