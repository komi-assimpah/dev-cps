"""
Service d'Orchestration "Smart Heating".

Responsabilité :
- Coordonner les informations de Géolocalisation et des capteurs
- Utiliser le HeatingPredictor (IA) pour prendre la décision finale
- Gérer la cohérence des données
"""

import os
import datetime
from datetime import datetime
import json
import logging
import time

# Kafka Imports
try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:
    KafkaConsumer = None
    KafkaProducer = None

from heating_predictor import HeatingPredictor
from geolocation_service import GeolocationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SmartHeating")

class SmartHeatingService:
    """
    Orchestrateur global.
    Utilise la Géolocalisation (pour savoir quand on arrive)
    ET le HeatingPredictor (pour savoir combien de temps nécessaire pour atteindre la température cible).
    """
    
    def __init__(self, model_path: str = "heating_model.json"):
        self.predictor = HeatingPredictor(model_path)
        self.geo_service = GeolocationService()
        
        # Préférences simulées (en prod on les récupèrera de la BDD)
        self.preferences = {
            "APT_101": 24.0, 
            "APT_102": 20.0, 
            "APT_103": 20.5, 
            "APT_104": 22.0,
            "APT_201": 21.5, 
            "APT_202": 23.0, 
            "APT_203": 22.0, 
            "APT_204": 20.5
        }

    def process_location_signal(self, location_payload: dict, sensor_data: dict) -> dict:
        required = ["apartment_id", "distance", "time", "timestamp"]
        
        for k in required:
            if k not in location_payload:
                return {"action": "ERROR", "reason": f"Missing key: {k}"}
        
        apartment_id = location_payload["apartment_id"]
        eta_minutes = float(location_payload["time"])
        distance_km = float(location_payload["distance"])
        loc_str = location_payload["timestamp"]
        
        # Vérification de la Synchro
        if not sensor_data.get("timestamp"):
             return {"action": "ERROR", "reason": "No sensor timestamp"}
        
        try:
            # Gère les formats ISO et timestamp int
            ts = sensor_data["timestamp"]
            if isinstance(ts, int) or (isinstance(ts, str) and ts.isdigit()):
                 sensor_timestamp = datetime.fromtimestamp(int(ts))
            else:
                 sensor_timestamp = datetime.fromisoformat(ts)

            loc_timestamp = datetime.fromisoformat(loc_str)
            
            time_diff = abs((sensor_timestamp - loc_timestamp).total_seconds())
            # MAX_DELAY_SECONDS = 900 # 15 minutes
            MAX_DELAY_SECONDS = 8640000  # for test only

            if time_diff > MAX_DELAY_SECONDS:
                 return {
                     "action": "ERROR", 
                     "reason": f"Data unsynced. Diff: {time_diff:.0f}s"
                 }
                 
        except ValueError as e:
            return {"action": "ERROR", "reason": f"Invalid timestamp format: {e}"}

        temp_cible = self.preferences.get(apartment_id, 20.0)
        temp_actuelle = sensor_data.get("temp_actuelle", 19.0)
        temp_ext = sensor_data.get("temp_ext", 10.0)
        humidity_ext = sensor_data.get("humidity_ext", 50.0)        
        current_hour = sensor_timestamp.hour
    
        prediction = self.predictor.decide(
            eta_minutes=eta_minutes,
            temp_actuelle=temp_actuelle,
            temp_cible=temp_cible,
            temp_ext=temp_ext,
            humidity_ext=humidity_ext,
            hour=current_hour,
            apartment_id=apartment_id
        )
        
        prediction["geo_info"] = {
            "distance_km": distance_km,
            "eta_minutes": eta_minutes
        }
        
        return prediction

class KafkaHeatingService:
    """Wrapper pour connecter le service à Kafka."""
    
    def __init__(self, kafka_broker="localhost:9092", retries=10, delay=5):
        if not KafkaConsumer:
            raise ImportError("kafka-python not installed")
            
        logger.info(f"Connecting to Kafka at {kafka_broker}...")
        
        # Retry logic for Kafka connection
        self.consumer = None
        self.producer = None
        
        for i in range(retries):
            try:
                self.consumer = KafkaConsumer(
                    "sensor-data",
                    bootstrap_servers=kafka_broker,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    group_id="heating-service-group",
                    auto_offset_reset='latest'
                )
                self.producer = KafkaProducer(
                    bootstrap_servers=kafka_broker,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8")
                )
                logger.info("✓ Connected to Kafka.")
                break
            except Exception as e:
                logger.warning(f"Kafka not ready (attempt {i+1}/{retries}): {e}")
                time.sleep(delay)
        
        if not self.consumer:
            raise RuntimeError(f"Could not connect to Kafka at {kafka_broker}")
        
        # Le coeur du système
        model_path = "IA/heating_model.json"
        if not os.path.exists(model_path): model_path = "heating_model.json"
        self.core_service = SmartHeatingService(model_path)
        logger.info("Kafka Heating Service Ready.")

    def run(self):
        logger.info(" Waiting for sensor data...")
        for message in self.consumer:
            try:
                data = message.value
                # data = {"timestamp": 123456789, "temperature": 20.5, "_mqtt_topic": "building/APT_101/salon/sensors", ...}
                
                # 1. Extraction ID Appartement
                # Topic MQTT original dans _mqtt_topic: building/APT_101/salon/sensors
                mqtt_topic = data.get("_mqtt_topic", "")
                parts = mqtt_topic.split("/")
                if len(parts) >= 2 and parts[0] == "building":
                    apartment_id = parts[1]
                else:
                    # Fallback si l'ID est dans le payload
                    apartment_id = data.get("apartment_id", "UNKNOWN")
                
                if apartment_id == "UNKNOWN":
                    continue

                # 2. Enrichissement avec Géolocalisation (Simulée)
                # Dans le futur, on pourrait lire un topic "geolocation"
                geo_payload = self.core_service.geo_service.get_location_update(apartment_id)
                
                # 3. Adaptation format capteur pour le service
                sensor_payload = {
                     "timestamp": data.get("timestamp"),
                     "temp_actuelle": data.get("temperature", 20.0), # Nom variable différent
                     "temp_ext": 10.0, # TODO: Récupérer de la météo
                     "humidity_ext": 50.0
                }
                
                # 4. Décision
                decision = self.core_service.process_location_signal(geo_payload, sensor_payload)
                
                if decision["action"] != "ERROR":
                    logger.info(f"Decision for {apartment_id}: {decision['action']}")
                    
                    # 5. Publication Commande (si nécessaire)
                    if decision["action"] in ["START_NOW", "WAIT"]:
                        command_payload = {
                            "apartment_id": apartment_id,
                            "action": decision["action"],
                            "timestamp": datetime.now().isoformat(),
                            "reason": decision["reason"]
                        }
                        self.producer.send("heating-commands", value=command_payload)
                        logger.info(f"→ Sent command to Kafka: {command_payload}")
                else:
                    logger.warning(f"Error processing {apartment_id}: {decision['reason']}")

            except Exception as e:
                logger.error(f"Error checking message: {e}")

def demo():
    print("=" * 50)
    print("🏠 SMART HEATING SERVICE (DEMO MODE)")
    print("=" * 50)
    
    try:
        model_path = "IA/heating_model.json" 
        if not os.path.exists(model_path):
            model_path = "heating_model.json"
            
        service = SmartHeatingService(model_path=model_path)
    except Exception as e:
        print(f"❌ Erreur Init: {e}")
        return
        
    print("\n" + "="*60)
    print("📋 SCÉNARIOS DE TEST")
    print("="*60)

    scenarios = [
        {
            "id": "APT_101", 
            "desc": "Retour Boulot (Froid, Loin)", 
            "t_int": 15.0, 
            "t_ext": 5.0
        },
        {
            "id": "APT_102", 
            "desc": "Course Rapide (Proche, Presque chaud)", 
            "t_int": 19.0, 
            "t_ext": 10.0
        },
        {
            "id": "APT_103", 
            "desc": "Week-end (Très Loin, Très Froid)", 
            "t_int": 12.0, 
            "t_ext": 0.0
        },
    ]

    for sc in scenarios:
        print(f"\nTEST: {sc['id']} - {sc['desc']}")
        
        geo_payload = service.geo_service.get_location_update(sc["id"])
        
        sensor_payload = {
            "timestamp": geo_payload["timestamp"], 
            "temp_actuelle": sc["t_int"],
            "temp_ext": sc["t_ext"],
            "humidity_ext": 60.0 
        }
        
        t_cible = service.preferences.get(sc["id"], 20.0)
        print(f"    Position: {geo_payload['distance']} km (arrive dans {geo_payload['time']} min)")
        print(f"    Appart: {sensor_payload['temp_actuelle']}°C (préference {t_cible}°C) | Ext: {sensor_payload['temp_ext']}°C")
        
        decision = service.process_location_signal(geo_payload, sensor_payload)
        
        if decision['action'] == "ERROR":
            print(f"      ERREUR: {decision['reason']}")
        else:
            print(f"      Chauffe estimée: {decision['temps_chauffe_minutes']} min")
            print(f"      DÉCISION: {decision['action']}")
            print(f"      Raison: {decision['reason']}")

if __name__ == "__main__":
    import sys
    if "--kafka" in sys.argv:
        broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        service = KafkaHeatingService(kafka_broker=broker)
        service.run()
    else:
        demo()
