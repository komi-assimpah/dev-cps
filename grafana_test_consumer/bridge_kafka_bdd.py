import calcul_scores.air_quality as IAQ
import csv
from datetime import datetime, timezone
import json
import psycopg2
import random

client_iaq = IAQ.CLIENT_AIR_QUALITY()

db_params = {
  "host": "localhost",
  "database": "sensor_scores",
  "user": "monuser",
  "password": "monpassword"
}


co_values = list()
co2_values = list()
pm25_values = list()

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
    #to_timestamp(1766962800)
  except Exception as e:
    print(f"Erreur DB : {e}")

qt_data = 12
try:
  with open('datasets/dataset_apt_102.csv', newline='') as csvfile:
    file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
    for i in range(1,len(file),qt_data):
      timestamp = file[i][0]

      co2_values = [float(rows[4]) for rows in file[i:i+qt_data]]
      co_values = [float(rows[5]) for rows in file[i:i+qt_data]]
      pm25_values = [float(rows[6]) for rows in file[i:i+qt_data]]
      tvoc_values = [float(rows[7]) for rows in file[i:i+qt_data]]

      IAQ_2h = client_iaq.IAQ(co2_values, co_values, "", pm25_values, tvoc_values)
      # old_IAQ_2h = client_iaq.old_IAQ(co2_values, co_values, "", pm25_values, tvoc_values)

      # print(f"score : {IAQ_2h}, old_score : {old_IAQ_2h}")
      send_bdd(timestamp, 2, IAQ_2h, random.uniform(0.0, 100.0))

      # print(f"{timestamp} : {IAQ_2h}")
except Exception as e:
  print(f"pas de data :( {e}")

# print(co_values)
# print(co2_values)
# print(pm25_values)

# ICONE = client_iaq.co2_score(co2_values)
# co_score = client_iaq.co_score(co_values, "ug/m3")
# pm_score = client_iaq.pm25_score(pm25_values)
# print(ICONE, co_score, pm_score, client_iaq.cov_score([]))
