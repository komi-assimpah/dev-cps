import csv
from datetime import datetime # , timezone
import json
import time

from confluent_kafka import Producer
import paho.mqtt.client as mqtt

from utils import cleaner
from utils import json_formatter

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

# user_iaq = IAQ.USER_AIR_QUALITY()
# user_iit = IIT.USER_ISOLATION_SCORE()
qt_data = 5

HISTORY_MAX_DEPTH = 50
DATA_TYPES = ["temperature", "humidity", "co2", "pm25", "co", "tvoc"]
THRESHOLD_DATA_TYPE = [10.0, 10.0, 100.0, 10.0, 1.5, 1200.0]

history = dict()
nb_outliers = dict()

for k in range(len(DATA_TYPES)):
  history[DATA_TYPES[k]] = list()
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


# ==== FONCTIONS UTILITAIRES ====

def main():
  values = dict()
  
  # nb_rooms = 0

  def on_message(client, userdata, message):
    nonlocal values #, nb_rooms

    print(f"[INFO] {datetime.now()} Message reçu sur le topic {message.topic}")

    room = message.topic.split('/')[2]

    data = json.loads(message.payload.decode('utf-8'))
    
    json_data = json_formatter.init_json(data["timestamp"])
    print(f"[INFO] {datetime.now()} Nettoyage des données de la piece {room}")
    for i in DATA_TYPES:
      new_value = data[i]

      try:
        (new_value, old_value) = cleaner.median_filter(new_value, i, values[room][i])
        print(f"[INFO] Filtre median appliqué pour : {i}")
        if old_value != None: print(f"[INFO] Changement : {old_value} -> {new_value}")

      except KeyError: # 1er passage, pas d'historique
        pass
      except Exception as e:
        print(f"[ERROR] {e}")
      
      json_data[i] = new_value


      # Sauvegarde de l'historique
      try:
        try: # En temps normal
          values[room][i].append(data[i])
          if len(values[room][i]) > HISTORY_MAX_DEPTH:
            values[room][i] = values[room][i][-HISTORY_MAX_DEPTH:]
        except: # Si l'historique de la data existe pas
          values[room][i] = [data[i]]
      except: # Si l'historique de piece existe pas
        values[room] = dict()
        values[room][i] = [data[i]]

    final_json = json_formatter.convert_json(json_data)

    topic = f"APT_10{apt_id}_{room}"
    
    print(final_json)
    producer.produce(topic, final_json, f"donnees_capteurs_APT_10{apt_id}")
    producer.flush()
    print(f"[INFO] {datetime.now()} Donnees envoyees sur le topic {topic}")
    time.sleep(0.2)

      
    

  # Configuration du client
  client = mqtt.Client()
  client.on_message = on_message

  client.connect("localhost", 1883, 60)

  client.subscribe("building/APT_101/+/sensors")

  client.loop_forever()


if __name__ == "__main__":
  args = parser.parse_args()
  apt_id = args.APT_ID

  producer = Producer(config)
  topic = f"APT_10{apt_id}"

  file = None
  i = 0
  main()