"""
Module d'injection d'anomalies pour tester le filtrage des données.
Types d'anomalies : impossible, spike, null

l'injections d'anomalies est n'est utilisé que pour l'envoie de données via MQTT dans generate.py
toutefois le module est indépendant et peut être utilisé ailleurs, comme dans le mode batch csv
"""

import random
import logging

logger = logging.getLogger("sensor-validation")

VALID_SENSORS_RANGES = {
    "temperature": (-20, 50),    # °C - réaliste intérieur
    "humidity": (0, 100),        # % - physique
    "co2": (300, 5000),          # ppm - min atmosphérique, max capteur
    "pm25": (0, 500),            # µg/m³ - max capteur
    "co": (0, 100),              # ppm - max sécurité
    "tvoc": (0, 10000),          # µg/m³ - max capteur
}

IMPOSSIBLE_SENSORS_VALUES = {
    "temperature": [-273, -100, 150, 500],   # < zéro absolu, > eau bouillante
    "humidity": [-50, 150, 999],              # < 0% ou > 100%
    "co2": [-100, 100, 50000],                # < 0 ou < atmosphère (420), énorme
    "pm25": [-10, 2000, 99999],               # < 0 ou >> max capteur
    "co": [-5, 1000, 9999],                   # < 0 ou létal++
    "tvoc": [-100, 50000, 99999],             # < 0 ou >> max
}

ANOMALY_PROBABILITY = 0.02


def random_inject_anomaly(sensor_data: dict) -> dict:
    if ANOMALY_PROBABILITY < random.random(): # Pas d'anomalie
        return sensor_data  
    
    sensors = list(VALID_SENSORS_RANGES.keys())
    sensor = random.choice(sensors)
    
    if sensor_data.get(sensor) is None: # Pas de ce capteur dans cette pièce
        return sensor_data
    
    original = sensor_data[sensor]
    anomaly_type = random.choice(["impossible", "spike", "null"])
    
    if anomaly_type == "impossible":
        sensor_data[sensor] = random.choice(IMPOSSIBLE_SENSORS_VALUES[sensor])
    elif anomaly_type == "spike":
        sensor_data[sensor] = original * 10
    else:
        sensor_data[sensor] = None
    
    logger.warning(f"[ANOMALY_INJECTED] {sensor}: {original} → {sensor_data[sensor]} ({anomaly_type})")
    return sensor_data
