import calcul_scores.air_quality as IAQ
import calcul_scores.isolation as IIT
import csv
from datetime import datetime # , timezone
import json
import time
from scipy.signal import medfilt
import numpy as np
# import json
# import psycopg2
# import random

# ==== SETUP VARIABLES ====

user_iaq = IAQ.USER_AIR_QUALITY()
user_iit = IIT.USER_ISOLATION_SCORE()
qt_data = 5

DATA_TYPES = ["temperature", "humidity", "co2", "pm25", "co", "tvoc"]
THRESHOLD_DATA_TYPE = [5.0, 5.0, 50.0, 5.0, 1.0, 1000.0]

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

def remove_outliers(new_data: list, data_type: str, threshold=5.0):
  global last_values, nb_outliers
  try:
    # print(data_type)
    start_idx = len(last_values[data_type])

    last_values[data_type].extend(new_data)

    med_filtered = medfilt(last_values[data_type], kernel_size=5)

    raw_new = np.array(last_values[data_type][start_idx:])
    filtered_new = med_filtered[start_idx:]

    diff = np.abs(raw_new - filtered_new)
    outliers_detectes = diff > threshold
    nb_outliers = np.sum(outliers_detectes)
    
    outliers = list()
    indices = np.where(outliers_detectes)[0]
    for i in indices: outliers.append(raw_new[i])

    if nb_outliers > 0: print(f"[INFO] [{data_type}] Détection de {nb_outliers} outliers : {outliers}")

    return (list(med_filtered[-5:]), outliers)
  except Exception as e:
    print(f"ERROR : {e}")
    return new_data

# ==== FONCTIONS UTILITAIRES ====

def main():
  global file, i
  # print("timestamp, id_appart, avg_temp, avg_humid, avg_co2, avg_co, avg_pm25, avg_tvoc")
  for i in range(1):
    filename = "output/apt_101_2025-12-01.csv"
    # filename = f"datasets/apt_102_2025-12-0{i:02d}.csv"
    try:
      with open(filename, newline='') as csvfile:
        file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
        for i in range(1,len(file),qt_data):
          json_data = dict()
          json_data["timestamp"] = int(datetime.fromisoformat(file[i][0]).timestamp())
          for j in range(len(DATA_TYPES)):
            l = gen_list_of_sensor_data(j+5)
            (data, outliers) = remove_outliers(l, DATA_TYPES[j], THRESHOLD_DATA_TYPE[j])
            consecutive_outliers = 0 if len(outliers) == 0 else consecutive_outliers+len(outliers)
            json_data[DATA_TYPES[j]] = avg(data)
          final_json = json.dumps(json_data, default=encoder)
          time.sleep(0.1)
          
    except Exception as e:
      print(f"pas de data :( {e}")

if __name__ == "__main__":
  file = None
  i = 0
  main()