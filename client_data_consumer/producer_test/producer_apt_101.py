import csv
import json
from confluent_kafka import Producer
import time

config = {
        # User-specific properties that you must set
        'bootstrap.servers': 'localhost:9092',

        # Fixed properties
        'acks': 'all'
    }

def encoder(obj):
  if isinstance(obj, set):
    return list(obj)
  return obj

producer = Producer(config)

topic = "APT_101"

try:
  with open('datasets/dataset_apt_101.csv', newline='') as csvfile:
    file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
    for i in range(1,len(file)):
      cur_json = dict()
      cur_json["timestamp"] = int(file[i][0])
      cur_json["temp"] = float(file[i][2])
      cur_json["humid"] = float(file[i][3])
      cur_json["co2"] = float(file[i][4])
      cur_json["co"] = float(file[i][5])
      cur_json["pm25"] = float(file[i][6])
      cur_json["tvoc"] = float(file[i][7])
      json_string = json.dumps(cur_json, default=encoder)
      print(type(json_string))
      print(json_string)
      producer.produce(topic, json_string, "test_producer")
      producer.flush()
      time.sleep(1)
except Exception as e:
  print(f"{e}")