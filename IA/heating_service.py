import os
import datetime
from datetime import datetime
import json
import logging
import time
import re

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
    def __init__(self, model_path: str = "heating_model.json"):
        self.predictor = HeatingPredictor(model_path)
        self.geo_service = GeolocationService()
        self.preferences = {
            "APT_101": 24.0, 
            "APT_102": 20.0, 
            # ...
        }

    def process_location_signal(self, location_payload: dict, sensor_data: dict) -> dict:
        # On utilise maintenant la préférence reçue dans le message fusionné si disponible
        apartment_id = location_payload.get("apartment_id", "APT_101")
        temp_cible = sensor_data.get("temp_preference", self.preferences.get(apartment_id, 20.0))
        
        # Extraction des données fusionnées
        temp_actuelle = sensor_data.get("temperature", 19.0)
        temp_ext = sensor_data.get("temp_ext", 10.0)
        humidity_ext = sensor_data.get("humidity_ext", 50.0)
        eta_minutes = float(location_payload.get("time", 20))
        distance_km = float(location_payload.get("distance", 5))
        
        # Utilisation du timestamp du message fusionné
        ts = sensor_data.get("timestamp")
        dt_object = datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.now()
        current_hour = dt_object.hour

        prediction = self.predictor.decide(
            eta_minutes=eta_minutes,
            temp_actuelle=temp_actuelle,
            temp_cible=temp_cible,
            temp_ext=temp_ext,
            humidity_ext=humidity_ext,
            hour=current_hour,
            apartment_id=apartment_id
        )
        
        prediction["geo_info"] = {"distance_km": distance_km, "eta_minutes": eta_minutes}
        # Ajout de la pièce dans le retour pour le log
        prediction["room"] = sensor_data.get("room", "unknown")
        
        return prediction

class KafkaHeatingService:
    def __init__(self, kafka_broker="localhost:9092", retries=10, delay=5):
        if not KafkaConsumer:
            raise ImportError("kafka-python not installed")
            
        logger.info(f"Connecting to Kafka at {kafka_broker}...")
        
        self.consumer = None
        self.producer = None
        
        # Buffer pour la fusion des données : {(room, timestamp): {données_cumulées}}
        self.data_buffer = {}
        
        for i in range(retries):
            try:
                self.consumer = KafkaConsumer(
                    bootstrap_servers=kafka_broker,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    group_id="heating-service-group",
                    auto_offset_reset='latest'
                )
                # S'abonner aux patterns APT_101.{room}.score_data et extra_data
                self.consumer.subscribe(pattern=r'^APT_101\..*\.(score_data|extra_data)$')
                
                self.producer = KafkaProducer(
                    bootstrap_servers=kafka_broker,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8")
                )
                logger.info("✓ Connected to Kafka and subscribed to room topics.")
                break
            except Exception as e:
                logger.warning(f"Kafka not ready (attempt {i+1}/{retries}): {e}")
                time.sleep(delay)
        
        model_path = "IA/heating_model.json"
        if not os.path.exists(model_path): model_path = "heating_model.json"
        self.core_service = SmartHeatingService(model_path)

    def run(self):
        logger.info("Waiting for room data (score/extra)...")
        for message in self.consumer:
            try:
                topic = message.topic
                data = message.value
                
                # 1. Analyse du topic pour extraire la room
                # Format attendu : APT_101.salon.score_data
                parts = topic.split(".")
                if len(parts) < 3: continue
                
                apartment_id = parts[0]
                room = parts[1]
                data_type = parts[2] # score_data ou extra_data
                timestamp = data.get("timestamp")

                if not timestamp: continue

                # 2. Gestion du Buffer (Concaténation)
                buffer_key = (room, timestamp)
                if buffer_key not in self.data_buffer:
                    self.data_buffer[buffer_key] = {"room": room}

                # Fusion des nouvelles données dans l'entrée du buffer
                self.data_buffer[buffer_key].update(data)

                # 3. Vérification si on a reçu les deux types de messages
                # On vérifie la présence d'une clé unique à chaque type pour valider la fusion
                is_complete = (
                    "temp_preference" in self.data_buffer[buffer_key] and  # vient de extra_data
                    "temperature" in self.data_buffer[buffer_key]         # vient de score_data
                )

                if is_complete:
                    merged_data = self.data_buffer.pop(buffer_key) # On récupère et on vide le buffer
                    logger.info(f"✨ Data complete for {room} at {timestamp}. Processing...")
                    
                    # 4. Enrichissement Géo et Décision
                    geo_payload = self.core_service.geo_service.get_location_update(apartment_id)
                    decision = self.core_service.process_location_signal(geo_payload, merged_data)
                    
                    if decision["action"] != "ERROR":
                        logger.info(f"Decision for {apartment_id} ({room}): {decision['action']}")
                        
                        # 5. Publication Commande
                        if decision["action"] in ["START_NOW", "WAIT"]:
                            command_payload = {
                                "apartment_id": apartment_id,
                                "room": room,
                                "action": decision["action"],
                                "timestamp": datetime.now().isoformat(),
                                "reason": decision["reason"],
                                "merged_input": merged_data # Optionnel : pour debug
                            }
                            self.producer.send("heating-commands", value=command_payload)
                    
                # Nettoyage optionnel : supprimer les vieux messages orphelins du buffer (> 5 min)
                self._cleanup_buffer()

            except Exception as e:
                logger.error(f"Error processing message on {topic}: {e}")

    def _cleanup_buffer(self):
        """Evite que le buffer ne grossisse indéfiniment si un message manque."""
        now = time.time()
        # On supprime ce qui a plus de 10 minutes (basé sur le timestamp du message)
        to_delete = [k for k, v in self.data_buffer.items() if (now - v.get("timestamp", 0)) > 600]
        for k in to_delete:
            del self.data_buffer[k]

def demo():
    """Simulation locale des scénarios d'origine adaptés à la nouvelle structure fusionnée."""
    print("=" * 60)
    print("SMART HEATING - DEMO SCENARIOS (APT_101)")
    print("=" * 60)
    
    service = SmartHeatingService()
    current_ts = 1764552600 # Timestamp de test
    
    # Scénarios de base adaptés
    scenarios = [
        {
            "desc": "Retour Boulot (Froid, Loin)",
            "room": "salon",
            "t_int": 15.0,
            "t_ext": 5.0,
            "dist": 25.0,
            "eta": 45.0,
            "pref": 24.0
        },
        {
            "desc": "Course Rapide (Proche, Presque chaud)",
            "room": "chambre",
            "t_int": 19.0,
            "t_ext": 10.0,
            "dist": 2.0,
            "eta": 10.0,
            "pref": 22.0
        },
        {
            "desc": "Week-end (Très Loin, Très Froid)",
            "room": "salon",
            "t_int": 12.0,
            "t_ext": 0.0,
            "dist": 150.0,
            "eta": 180.0,
            "pref": 24.0
        }
    ]

    for sc in scenarios:
        print(f"\n▶ TEST : {sc['desc']}")
        
        # 1. Simulation du Payload Fusionné (Score + Extra)
        merged_data = {
            "timestamp": current_ts,
            "room": sc["room"],
            # Champs issus de extra_data
            "window_open": False,
            "heater_on": False,
            "presence": False,
            "humidity_ext": 65.0,
            "temp_preference": sc["pref"],
            # Champs issus de score_data
            "temperature": sc["t_int"],
            "temp_ext": sc["t_ext"],
            "energy_kwh": 1.5,
            "humidity": 45.0
        }
        
        # 2. Simulation du Payload Géolocalisation
        geo_payload = {
            "apartment_id": "APT_101",
            "distance": sc["dist"],
            "time": sc["eta"],
            "timestamp": datetime.fromtimestamp(current_ts).isoformat()
        }

        print(f"   [Données] Pièce: {sc['room']} | Int: {sc['t_int']}°C | Cible: {sc['pref']}°C | Ext: {sc['t_ext']}°C")
        print(f"   [Géo]     Distance: {sc['dist']} km | ETA: {sc['eta']} min")

        # 3. Calcul de la décision
        decision = service.process_location_signal(geo_payload, merged_data)

        if decision["action"] == "ERROR":
            print(f"ERREUR: {decision['reason']}")
        else:
            print(f"DÉCISION: {decision['action']}")
            print(f"RAISON  : {decision['reason']}")
            print(f"CHAUFFE : {decision.get('temps_chauffe_minutes')} min")

if __name__ == "__main__":
    import sys
    if "--kafka" in sys.argv:
        # Note: assure-toi que le broker est accessible
        try:
            broker = os.getenv("KAFKA_BROKER", "localhost:9092")
            service = KafkaHeatingService(kafka_broker=broker)
            service.run()
        except Exception as e:
            print(f"Impossible de démarrer Kafka: {e}")
    else:
        demo()