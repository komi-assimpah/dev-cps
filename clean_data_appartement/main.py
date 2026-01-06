import calcul_scores.air_quality as IAQ
import calcul_scores.isolation as IIT
import csv
from datetime import datetime, timezone
import json
import psycopg2
import random

user_iaq = IAQ.USER_AIR_QUALITY()
user_iit = IIT.USER_ISOLATION_SCORE()
qt_data = 4

print("timestamp, id_appart, avg_temp, avg_humid, avg_co2, avg_co, avg_pm25, avg_tvoc")
for i in range(1,10):
  filename = "datasets/apt_102_2025-12-0"+str(i)+".csv"
  try:
    with open(filename, newline='') as csvfile:
      file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
      for i in range(1,len(file),qt_data):
        timestamp = datetime.fromisoformat(file[i][0])
        timestamp_int = int(timestamp.timestamp())

        temp_values = [float(rows[5]) for rows in file[i:i+qt_data]]
        count_temp_values = len(temp_values) - temp_values.count(0)
        avg_temp = round(sum(temp_values)/count_temp_values, 3)

        humid_values = [float(rows[6]) for rows in file[i:i+qt_data]]
        count_humid_values = len(humid_values) - humid_values.count(0)
        avg_humid = round(sum(humid_values)/count_humid_values, 3)

        co2_values = [float(rows[7]) if rows[7] else 0.0 for rows in file[i:i+qt_data]]
        count_co2_values = len(co2_values) - co2_values.count(0)
        avg_co2 = round(sum(co2_values)/count_co2_values, 3)
        # print(avg_co2)

        pm_values = [float(rows[8]) for rows in file[i:i+qt_data]]
        count_pm_values = len(pm_values) - pm_values.count(0)
        avg_pm = round(sum(pm_values)/count_pm_values, 3)

        co_values = [float(rows[9]) for rows in file[i:i+qt_data]]
        count_co_values = len(co_values) - co_values.count(0)
        avg_co = round(sum(co_values)/count_co_values, 3)

        tvoc_values = [float(rows[10]) for rows in file[i:i+qt_data]]
        count_tvoc_values = len(tvoc_values) - tvoc_values.count(0)
        avg_tvoc = round(sum(tvoc_values)/count_tvoc_values, 3)

        print(f"{timestamp_int}, 2, {avg_temp}, {avg_humid}, {avg_co2}, {avg_co}, {avg_pm}, {avg_tvoc}")
  except Exception as e:
    print(f"pas de data :( {e}")


for i in range(10,31):
  filename = "datasets/apt_102_2025-12-"+str(i)+".csv"
  try:
    with open(filename, newline='') as csvfile:
      file = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
      for i in range(1,len(file),qt_data):
        timestamp = datetime.fromisoformat(file[i][0])
        timestamp_int = int(timestamp.timestamp())

        temp_values = [float(rows[5]) for rows in file[i:i+qt_data]]
        count_temp_values = len(temp_values) - temp_values.count(0)
        avg_temp = round(sum(temp_values)/count_temp_values, 3)

        humid_values = [float(rows[6]) for rows in file[i:i+qt_data]]
        count_humid_values = len(humid_values) - humid_values.count(0)
        avg_humid = round(sum(humid_values)/count_humid_values, 3)

        co2_values = [float(rows[7]) if rows[7] else 0.0 for rows in file[i:i+qt_data]]
        count_co2_values = len(co2_values) - co2_values.count(0)
        avg_co2 = round(sum(co2_values)/count_co2_values, 3)
        # print(avg_co2)

        pm_values = [float(rows[8]) for rows in file[i:i+qt_data]]
        count_pm_values = len(pm_values) - pm_values.count(0)
        avg_pm = round(sum(pm_values)/count_pm_values, 3)

        co_values = [float(rows[9]) for rows in file[i:i+qt_data]]
        count_co_values = len(co_values) - co_values.count(0)
        avg_co = round(sum(co_values)/count_co_values, 3)

        tvoc_values = [float(rows[10]) for rows in file[i:i+qt_data]]
        count_tvoc_values = len(tvoc_values) - tvoc_values.count(0)
        avg_tvoc = round(sum(tvoc_values)/count_tvoc_values, 3)

        print(f"{timestamp_int}, 2, {avg_temp}, {avg_humid}, {avg_co2}, {avg_co}, {avg_pm}, {avg_tvoc}")
  except Exception as e:
    print(f"pas de data :( {e}")
