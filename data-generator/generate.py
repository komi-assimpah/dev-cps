"""
Générateur de données capteurs IoT.

Usage :
    # Mode batch (CSV) - par défaut
    python generate.py                          # 1 jour, tous les appartements
    python generate.py --days 7                 # 1 semaine
    python generate.py --apartment APT_101      # Un seul appartement

    # Mode temps réel (MQTT)
    python generate.py --mode realtime                        # Défaut: lectures toutes les 10min simulées, publiées toutes les 1sec réelle
    python generate.py --mode realtime --interval 300         # Lectures toutes les 5min simulées, publiées toutes les 1sec réelle
    python generate.py --mode realtime --interval 300 --speed 600   # Lectures toutes les 5min simulées, publiées 2x plus vite (0.5sec réelle)
    python generate.py --mode realtime --speed 0              # Aussi vite que possible

    Formule : délai_réel = interval / speed
"""

import csv
import os
import argparse
import time
from datetime import datetime, timedelta
from typing import List

from config import APARTMENTS, WEATHER, INITIAL_SENSOR_VALUES, INTERVAL_10_MINS
from generators import (
    generate_weather_for_day,
    get_external_pm25,
    get_external_co,
    get_external_tvoc,
    is_user_home,
    window_is_opened,
    update_temperature,
    update_co2,
    update_humidity,
    update_pm25,
    update_co,
    update_tvoc,
)

# TODO: add energy consumption generation temperature dependent
# TODO: fonction qui insert des données erronées (capteur HS, valeurs aberrantes...) pour tester la filtration et suivi dans les logs 
#   ou les mettre dans les fichiers responsables de la génération de chaque données cpteurs 
#TODO:ugmenter la frequence de lecture des capteurs critiques (CO2, PM25, CO, TVOC)

class RoomState:
    """État d'une pièce (valeurs courantes des capteurs)."""
    
    def __init__(self, apt_config: dict, room_name: str):
        user = apt_config["user"]
        self.temp = user["temp_preference"] - 1.5 + apt_config["temp_offset"]
        self.co2 = INITIAL_SENSOR_VALUES["co2"]
        self.humidity = INITIAL_SENSOR_VALUES["humidity"]
        self.pm25 = INITIAL_SENSOR_VALUES["pm25"]
        self.co = INITIAL_SENSOR_VALUES["co"]
        self.tvoc = INITIAL_SENSOR_VALUES["tvoc"]
        self.window_open = False


def update_room_sensors(
    state: RoomState,
    apt_config: dict,
    room_name: str,
    hour: int,
    minute: int,
    day_of_week: int,
    temp_ext: float,
    humidity_ext: float
) -> dict:
    """
    Met à jour l'état des capteurs d'une pièce et retourne les données.
    Cette fonction est utilisée par les deux modes (batch et realtime).
    """
    user = apt_config["user"]
    temp_pref = user["temp_preference"]
    temp_offset = apt_config["temp_offset"]
    heat_loss = apt_config["heat_loss_factor"]
    orientation = apt_config["orientation"]
    has_co2 = room_name in apt_config["rooms_with_co2"]
    
    presence = is_user_home(hour, minute, day_of_week, user)
    state.window_open = window_is_opened(state.window_open, presence, state.co2, hour, state.temp, room_name)
    
    state.temp = update_temperature(
        state.temp, temp_ext, state.window_open, presence,
        temp_pref, temp_offset, heat_loss, orientation, hour
    )
    
    state.co2 = update_co2(state.co2, presence, state.window_open, room_name, hour)
    state.humidity = update_humidity(state.humidity, humidity_ext, state.window_open, presence, room_name, hour)
    state.pm25 = update_pm25(state.pm25, get_external_pm25(hour), state.window_open, presence, room_name, hour)
    state.co = update_co(state.co, get_external_co(), state.window_open, presence, room_name, hour)
    state.tvoc = update_tvoc(state.tvoc, get_external_tvoc(), state.window_open, presence, room_name, hour)
    
    return {
        "room": room_name,
        "temperature": round(state.temp, 2),
        "humidity": round(state.humidity, 2),
        "co2": round(state.co2, 2) if has_co2 else None,
        "pm25": round(state.pm25, 2),
        "co": round(state.co, 3),
        "tvoc": round(state.tvoc, 2),
        "window_open": state.window_open,
        "presence": presence,
        "temp_ext": temp_ext,
        "humidity_ext": humidity_ext,
    }


def generate_room_data(room_name: str, apt_config: dict, weather: List[dict], date: datetime) -> List[dict]:
    """Génère les données pour UNE pièce sur UNE journée (mode batch)."""
    state = RoomState(apt_config, room_name)
    data = []
    day_of_week = date.weekday()
    
    for w in weather:
        hour, minute = w["hour"], w["minute"]
        timestamp = date.replace(hour=hour, minute=minute, second=0)
        
        sensor_data = update_room_sensors(
            state, apt_config, room_name,
            hour, minute, day_of_week,
            w["temp_ext"], w["humidity_ext"]
        )
        sensor_data["timestamp"] = timestamp.isoformat()
        data.append(sensor_data)
    
    return data


def generate_apartment_data(apt_id: str, apt_config: dict, weather: List[dict], date: datetime) -> List[dict]:
    """Génère les données pour un appartement sur une journée."""
    all_data = []
    
    for room in apt_config["rooms"]:
        room_data = generate_room_data(room, apt_config, weather, date)
        for row in room_data:
            row["apartment_id"] = apt_id
        all_data.extend(room_data)
    
    all_data.sort(key=lambda x: (x["timestamp"], x["room"]))
    return all_data


def save_csv(data: List[dict], filename: str):
    if not data:
        return
    
    fields = ["timestamp", "apartment_id", "room", "window_open", "presence", "temperature", "humidity",
              "co2", "pm25", "co", "tvoc", "temp_ext", "humidity_ext"]
    
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  [OK] {filename} ({len(data)} lignes)")


def save_weather_csv(weather: List[dict], date: datetime, filename: str):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "temperature", "humidity"])
        writer.writeheader()
        for w in weather:
            ts = date.replace(hour=w["hour"], minute=w["minute"], second=0)
            writer.writerow({
                "timestamp": ts.isoformat(),
                "temperature": w["temp_ext"],
                "humidity": w["humidity_ext"],
            })
    print(f"  [OK] {filename} ({len(weather)} lignes)")


def run_csv_batch_mode(args, apartments: dict):
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 50)
    print("GÉNÉRATION DES DONNÉES CAPTEURS (MODE BATCH CSV)")
    print("=" * 50)
    print(f"Jours : {args.days}")
    print(f"Appartements : {len(apartments)}")
    print("=" * 50)
    
    #TODO: améliorer pour commencer à maintenant si on veut
    start_date = datetime(2025, 12, 1)  # Lundi
    
    for day in range(args.days):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        print(f"\n[{date_str}] ({current_date.strftime('%A')})")
        
        weather = generate_weather_for_day(current_date, WEATHER, args.interval)
        save_weather_csv(weather, current_date, f"{args.output}/weather_{date_str}.csv")
        
        for apt_id, apt_config in apartments.items():
            data = generate_apartment_data(apt_id, apt_config, weather, current_date)
            save_csv(data, f"{args.output}/{apt_id.lower()}_{date_str}.csv")
    
    print("\n" + "=" * 50)
    print("[OK] Terminé !")


def run_realtime_mode(args, apartments: dict):
    """Mode temps réel : publie sur MQTT avec simulation temporelle."""
    from producers import MQTTPublisher
    
    print("=" * 50)
    print("GÉNÉRATION TEMPS RÉEL (MODE MQTT)")
    print("=" * 50)
    print(f"Broker MQTT : {args.mqtt_broker}:{args.mqtt_port}")
    print(f"Appartements : {len(apartments)}")
    print(f"Speed factor : {args.speed} (0=max speed)")
    print("=" * 50)
    
    publisher = MQTTPublisher()
    publisher.connect()
    
    # Calculer le délai réel entre deux lectures
    # delay = intervalle_simulé / facteur_accélération
    if args.speed == 0:
        delay_seconds = 0
    else:
        delay_seconds = args.interval / args.speed
    
    print(f"Intervalle de lecture : {args.interval}s simulées ({args.interval//60}min)")
    print(f"Délai entre envois : {delay_seconds:.2f}s réelles")
    print("=" * 50)
    print("\nDémarrage... (Ctrl+C pour arrêter)\n")
    
    room_states = {}
    for apt_id, apt_config in apartments.items():
        room_states[apt_id] = {}
        for room in apt_config["rooms"]:
            room_states[apt_id][room] = RoomState(apt_config, room)
    
    start_date = datetime(2025, 12, 1)
    current_date = start_date
    current_time_index = 0
    message_count = 0
    
    try:
        while True:
            weather = generate_weather_for_day(current_date, WEATHER, args.interval)
            w = weather[current_time_index]
            hour, minute = w["hour"], w["minute"]
            temp_ext, humidity_ext = w["temp_ext"], w["humidity_ext"]
            
            timestamp = current_date.replace(hour=hour, minute=minute, second=0)
            day_of_week = current_date.weekday()
            
            # Publier météo
            publisher.publish_weather({
                "timestamp": timestamp.isoformat(),
                "temperature": temp_ext,
                "humidity": humidity_ext,
            })
            
            # Traiter chaque appartement/pièce
            for apt_id, apt_config in apartments.items():
                for room_name in apt_config["rooms"]:
                    state = room_states[apt_id][room_name]
                    
                    sensor_data = update_room_sensors(
                        state, apt_config, room_name,
                        hour, minute, day_of_week,
                        temp_ext, humidity_ext
                    )
                    sensor_data["timestamp"] = timestamp.isoformat()
                    sensor_data["apartment_id"] = apt_id
                    
                    publisher.publish_sensor_data(apt_id, room_name, sensor_data)
                    message_count += 1
            
            if message_count % 50 == 0:
                print(f"[{timestamp.isoformat()}] {message_count} messages publiés")
            
            current_time_index += 1
            if current_time_index >= len(weather):
                current_time_index = 0
                current_date += timedelta(days=1)
                print(f"\n--- Nouveau jour : {current_date.strftime('%Y-%m-%d')} ---\n")
            
            if delay_seconds > 0:
                time.sleep(delay_seconds)
                
    except KeyboardInterrupt:
        print(f"\n\n[OK] Arrêté. {message_count} messages publiés.")
    finally:
        publisher.disconnect()


def main():
    # Valeurs par défaut depuis les variables d'environnement (pour Docker)
    default_mode = os.getenv("MODE", "batch")
    default_broker = os.getenv("MQTT_BROKER", "localhost")
    default_port = int(os.getenv("MQTT_PORT", "1883"))
    default_interval = int(os.getenv("INTERVAL", str(INTERVAL_10_MINS)))
    default_speed = os.getenv("SPEED", None)
    default_apartment = os.getenv("APARTMENT", None) or None
    
    parser = argparse.ArgumentParser(description="Générateur de données capteurs IoT")
    parser.add_argument("--mode", choices=["batch", "realtime"], default=default_mode, help="Mode de génération")
    parser.add_argument("--days", type=int, default=1, help="Nombre de jours (batch)")
    parser.add_argument("--apartment", type=str, default=default_apartment, help="Un seul appartement")
    parser.add_argument("--output", type=str, default="output", help="Dossier de sortie CSV")
    parser.add_argument("--mqtt-broker", type=str, default=default_broker, help="Adresse broker MQTT")
    parser.add_argument("--mqtt-port", type=int, default=default_port, help="Port broker MQTT")
    parser.add_argument("--interval", type=int, default=default_interval, help=f"Intervalle simulé entre lectures capteurs en secondes (défaut={INTERVAL_10_MINS}s soit {INTERVAL_10_MINS//60}min)")
    parser.add_argument("--speed", type=int, default=int(default_speed) if default_speed else None, help="Facteur d'accélération temps réel (défaut=interval pour 1sec réelle, 0=max speed)")
    
    args = parser.parse_args()
    
    # Si --speed n'est pas spécifié, utiliser --interval pour avoir 1 seconde réelle par défaut
    if args.speed is None:
        args.speed = args.interval
    
    if args.apartment:
        if args.apartment not in APARTMENTS:
            print(f"[ERROR] Appartement inconnu : {args.apartment}")
            return
        apartments = {args.apartment: APARTMENTS[args.apartment]}
    else:
        apartments = APARTMENTS
    
    if args.mode == "batch":
        run_csv_batch_mode(args, apartments)
    else:
        run_realtime_mode(args, apartments)


if __name__ == "__main__":
    main()
