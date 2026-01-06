import json
import calcul_scores.air_quality as IAQ
from confluent_kafka import Consumer, KafkaError
import psycopg2
import random
from datetime import datetime, timezone

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


# ======== CONFIG KAFKA ========

c = Consumer(conf)
topic = "APT_101"
c.subscribe([topic])

# ======== CONFIG KAFKA ========


# ======== SETUP VARIABLES ========

MAX_LEN_QUEUES = 12

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

def send_bdd(timestamp, id_appart=1, iaq_2h=0.0, iit=100.0):
  try:
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    insert_query = """
    INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(%s), %s, %s, %s);
    """
    cur.execute(insert_query, (timestamp, id_appart, iaq_2h, iit))
    conn.commit()
    cur.close()
    conn.close()
    print(f"[SUCCESS] INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp({timestamp}), {id_appart}, {iaq_2h}, {iit});", file=log_file)
  except Exception as e:
    print(f"[ERROR] {e}", file=log_file)

# ======== COMMUNICATION BDD ========

# ======== LECTURE JSON ========

# def forgiving_json_deserializer(v):
#     try:
#         return json.loads(v.decode('utf-8'))
#     except json.decoder.JSONDecodeError:
#         # log.exception('Unable to decode: %s', v)
#         return None

def read_json(json_data):
  timestamp_queue.append(json_data["timestamp"])
  temp_queue.append(json_data["temp"])
  humid_queue.append(json_data["humid"])
  co2_queue.append(json_data["co2"])
  co_queue.append(json_data["co"])
  pm25_queue.append(json_data["pm25"])
  tvoc_queue.append(json_data["tvoc"])

# ======== LECTURE JSON ========

def main():
  global timestamp_queue, temp_queue, humid_queue, co2_queue, co_queue, pm25_queue, tvoc_queue
  try:
    while True:
      msg = c.poll(1.0)
      if msg is None: print(f"[INFO] Waiting for topic messages", file=log_file)
      elif msg.error(): print(f"[ERROR] {msg.error()}")
      else : # consommation miam miam
        print(f"[INFO] Received data from topic", file=log_file)
        data_bytes = msg.value()
        data_str = data_bytes.decode('utf-8')
        data_dict = json.loads(data_str)
        timestamp_queue.append(data_dict["timestamp"])
        temp_queue.append(data_dict["temp"])
        humid_queue.append(data_dict["humid"])
        co2_queue.append(data_dict["co2"])
        co_queue.append(data_dict["co"])
        pm25_queue.append(data_dict["pm25"])
        tvoc_queue.append(data_dict["tvoc"])
        if (len(timestamp_queue) == 12):
          IAQ_2h = client_iaq.IAQ(co2_queue, co_queue, "", pm25_queue, tvoc_queue)
          send_bdd(timestamp_queue[0], 1, IAQ_2h, random.uniform(0.0, 100.0))
          timestamp_queue = list()
          temp_queue = list()
          humid_queue = list()
          co2_queue = list()
          co_queue = list()
          pm25_queue = list()
          tvoc_queue = list()
        # read_json(...)
        # if (len(timestamp_queue) == 12) : 
        #   IAQ_2h = client_iaq.IAQ(co2_queue, co_queue, "", pm25_queue, tvoc_queue)
        #   send_bdd(timestamp_queue[0], 1, IAQ_2h, random.uniform(0.0, 100.0))
  except KeyboardInterrupt:
    pass
  finally:
    c.close()

  # while (len(timestamp_queue) != 12):
  #   print(f"[INFO] lecture de : messages_test/message{len(timestamp_queue)}.json'", file=log_file)
  #   read_json('messages_test/message'+str(len(timestamp_queue))+'.json')
  # IAQ_2h = client_iaq.IAQ(co2_queue, co_queue, "", pm25_queue, tvoc_queue)
  # print(f"[INFO] IAQ_2h : {IAQ_2h}", file=log_file)
  # send_bdd(timestamp_queue[0], 1, IAQ_2h, random.uniform(0.0, 100.0))

if __name__ == "__main__":
  client_iaq = IAQ.CLIENT_AIR_QUALITY()

  timestamp_queue = list()
  temp_queue = list()
  humid_queue = list()
  co2_queue = list()
  co_queue = list()
  pm25_queue = list()
  tvoc_queue = list()

  log_file = open(datetime.now().strftime("%d%m%Y_%H%M%S")+".log", 'a')
  main()


# print(f"timestamp: {timestamp_queue[0]}")
# print(f"temperature : {temp_queue}")
# print(f"humidity : {humid_queue}")
# print(f"ICONE : {client_iaq.co2_score(co2_queue)} | co2 : {co2_queue}")
# print(f"co SCORE : {client_iaq.co_score(co_queue, "")} | co : {co_queue}")
# print(f"pm25 SCORE : {client_iaq.pm25_score(pm25_queue)} | pm25 : {pm25_queue}")
# print(f"cov SCORE : {client_iaq.cov_score(tvoc_queue)} | tvoc : {tvoc_queue}")
