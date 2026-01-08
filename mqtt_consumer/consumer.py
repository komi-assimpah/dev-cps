import calcul_scores.air_quality as IAQ
import calcul_scores.isolation as IIT
import csv
from datetime import datetime # , timezone
import json
import time
from scipy.signal import medfilt
import numpy as np
from confluent_kafka import Producer
# import json
# import psycopg2
# import random

import argparse


# ======== DECLARATION DES ARGUMENTS ========

parser = argparse.ArgumentParser(
  prog='mqtt-consumer',
  description="""
              Prend les informations des topics mqtt APT_10x/{piece}/capteur, traite les donnees, fait la moyenne des capteurs, 
              et envoie les data sur le topic kafka APT_10x
              """
)

parser.add_argument('APT_ID', 
                    type = int, 
                    help = 'le dernier chiffre de l\'identifiant de l\'appartement',
                    default = 1
)

# ======== DECLARATION DES ARGUMENTS ========


# ==== CONFIG PRODUCER KAFKA ====

config = {
  'bootstrap.servers': 'localhost:9092',
  'acks': 'all'
}

# ==== SETUP VARIABLES ====

user_iaq = IAQ.USER_AIR_QUALITY()
user_iit = IIT.USER_ISOLATION_SCORE()
qt_data = 5

DATA_TYPES = ["temperature", "humidity", "co2", "pm25", "co", "tvoc"]
THRESHOLD_DATA_TYPE = [10.0, 10.0, 100.0, 10.0, 1.5, 1200.0]

last_values = dict()
nb_outliers = dict()

for k in range(len(DATA_TYPES)):
  last_values[DATA_TYPES[k]] = list()
  nb_outliers[DATA_TYPES[k]] = list()

# ==== SETUP VARIABLES ====

# ==== FONCTIONS UTILITAIRES ====

def encoder(obj):
  if isinstance(obj, set):
    return list(obj)
  return obj

def gen_list_of_sensor_data(column: int) -> list:
  global qt_data, file, i
  return [float(rows[column]) for rows in file[i:i+qt_data] if (rows[column])]

def avg(data: list) -> float:
  count = len(data) - data.count(None)
  mean = sum(dat for dat in data if dat != None)/count
  return round(mean, 3)

def create_json(timestamp: int, temperature: float, humidity: float, co2: float, co: float, pm25: float, tvoc: float) -> dict:
  json_data = dict()
  json_data["timestamp"] = timestamp
  json_data["temperature"] = temperature
  json_data["humidity"] = humidity
  json_data["co2"] = co2
  json_data["co"] = co
  json_data["pm25"] = pm25
  json_data["tvoc"] = tvoc

def get_dynamic_threshold(history, k=5):
    median = np.median(history)
    mad = np.median(np.abs(history - median))
    return k * (mad * 1.4826)

def remove_outliers(new_data: list, data_type: str):
  global last_values, nb_outliers
  try:
    start_idx = len(last_values[data_type])
    last_values[data_type].extend(new_data)

    if len(last_values[data_type]) > 100:
      last_values[data_type] = last_values[data_type][-100:]
      start_idx = len(last_values[data_type]) - len(new_data)
    
    if len(last_values[data_type]) >= 9:
      arr_full = np.array(last_values[data_type], dtype=float)
      med_filtered = medfilt(last_values[data_type], kernel_size=9)

      threshold = get_dynamic_threshold(last_values[data_type])
      # print(f"[INFO] [THRESHOLD] [{data_type}] {threshold}")

      raw_new = arr_full[start_idx:]
      filtered_new = med_filtered[start_idx:]

      diff = np.abs(raw_new - filtered_new)
      outliers_detectes = diff > threshold

      outliers = raw_new[outliers_detectes].tolist()

      if len(outliers) > 0: print(f"[INFO] [{data_type}] Détection de {len(outliers)} outliers {outliers} dans {new_data}")

      return (list(med_filtered[-len(new_data):]), outliers)
    else:
      return (new_data, list())
  except Exception as e:
    print(f"ERROR : {e}")
    return (new_data, list())

# ==== FONCTIONS UTILITAIRES ====

def main():
  global file, i, apt_id, topic
  for i in range(1,30):
    filename = f"datasets/apt_10{apt_id}_2025-12-{i:02d}.csv"
    try:
      with open(filename, newline='') as csvfile:
        file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))

        for i in range(1,len(file),qt_data):

          json_data = dict()
          json_data["timestamp"] = int(datetime.fromisoformat(file[i][0]).timestamp())
          
          for j in range(len(DATA_TYPES)):

            l = gen_list_of_sensor_data(j+5)
            (data, outliers) = remove_outliers(l, DATA_TYPES[j]) #, THRESHOLD_DATA_TYPE[j])
            
            nb_outliers[DATA_TYPES[j]] = 0 if len(outliers) == 0 else nb_outliers[DATA_TYPES[j]]+len(outliers)
            # print(f"[INFO] Nombre d'outliers par type de data : {nb_outliers}")
            json_data[DATA_TYPES[j]] = avg(data)
          
          final_json = json.dumps(json_data, default=encoder)
          producer.produce(topic, final_json, f"donnees_capteurs_APT_10{apt_id}")
          producer.flush()
          time.sleep(0.2)
          
    except Exception as e:
      print(f"pas de data :( {e}")

if __name__ == "__main__":
  args = parser.parse_args()
  apt_id = args.APT_ID

  producer = Producer(config)
  topic = f"APT_10{apt_id}"

  file = None
  i = 0
  main()