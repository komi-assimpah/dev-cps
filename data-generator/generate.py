"""
Générateur de CSV pour les capteurs IoT.

Usage :
    python generate.py                      # 1 jour, tous les appartements
    python generate.py --days 7             # 1 semaine
    python generate.py --apartment APT_101  # Un seul appartement
    python generate.py --days 1 --apartment APT_101
"""

import csv
import os
import argparse
from datetime import datetime, timedelta
from typing import List

from config import APARTMENTS, WEATHER
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


def generate_room_data(
    room_name: str,
    apt_config: dict,
    weather: List[dict],
    date: datetime
) -> List[dict]:
    """Génère les données pour UNE pièce sur UNE journée."""
    data = []
    day_of_week = date.weekday()
    
    user = apt_config["user"]
    temp_pref = user["temp_preference"]
    temp_offset = apt_config["temp_offset"]
    heat_loss = apt_config["heat_loss_factor"]
    orientation = apt_config["orientation"]
    has_co2 = room_name in apt_config["rooms_with_co2"]
    
    current_temp = temp_pref - 1.5 + temp_offset
    current_co2 = 550.0
    current_humidity = 50.0
    current_pm25 = 15.0   # Niveau initial urbain (µg/m³)
    current_co = 0.8      # Niveau initial faible (ppm)
    current_tvoc = 250.0  # Niveau initial acceptable (µg/m³)
    window_open = False
    
    for w in weather:
        hour = w["hour"]
        minute = w["minute"]
        temp_ext = w["temp_ext"]
        humidity_ext = w["humidity_ext"]
        
        timestamp = date.replace(hour=hour, minute=minute, second=0)
        
        presence = is_user_home(hour, minute, day_of_week, user)
        
        window_open = window_is_opened(window_open, presence, current_co2, hour)
        
        current_temp = update_temperature(
            current_temp, temp_ext, window_open, presence,
            temp_pref, temp_offset, heat_loss, orientation, hour
        )
        
        if has_co2:
            current_co2 = update_co2(current_co2, presence, window_open, room_name, hour)
        
        current_humidity = update_humidity(current_humidity, humidity_ext, window_open, presence, room_name, hour)
        
        external_pm25 = get_external_pm25(hour)
        current_pm25 = update_pm25(current_pm25, external_pm25, window_open, presence, room_name, hour)
        
        external_co = get_external_co()
        current_co = update_co(
            current_co, external_co, window_open, presence, room_name, hour
        )
        
        external_tvoc = get_external_tvoc()
        current_tvoc = update_tvoc(
            current_tvoc, external_tvoc, window_open, presence, room_name, hour
        )
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "room": room_name,
            "temperature": current_temp,
            "humidity": current_humidity,
            "co2": current_co2 if has_co2 else None,
            "pm25": current_pm25,
            "co": current_co,
            "tvoc": current_tvoc,
            "window_open": window_open,
            "presence": presence,
            "temp_ext": temp_ext,
            "humidity_ext": humidity_ext,
        })
    
    return data


def generate_apartment_data(apt_id: str, apt_config: dict, weather: List[dict], date: datetime) -> List[dict]:
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
    
    print(f"  [OK] {filename} generated: ({len(data)} lignes)")


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


def main():
    parser = argparse.ArgumentParser(description="Génère les CSV de données capteurs")
    parser.add_argument("--days", type=int, default=1, help="Nombre de jours")
    parser.add_argument("--apartment", type=str, default=None, help="Un seul appartement")
    parser.add_argument("--output", type=str, default="output", help="Dossier de sortie")
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    # Sélectionner les appartements
    if args.apartment:
        if args.apartment not in APARTMENTS:
            print(f"[ERROR] Appartement inconnu : {args.apartment}")
            return
        apartments = {args.apartment: APARTMENTS[args.apartment]}
    else:
        apartments = APARTMENTS
    
    print("=" * 50)
    print("GÉNÉRATION DES DONNÉES CAPTEURS")
    print("=" * 50)
    print(f"Jours : {args.days}")
    print(f"Nb Appartements : {len(apartments)}")
    print("=" * 50)
    
    start_date = datetime(2025, 12, 1)  # Un lundi
    
    for day in range(args.days):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        print(f"\n[{date_str}] ({current_date.strftime('%A')})")
        
        weather = generate_weather_for_day(current_date, WEATHER)
        save_weather_csv(weather, current_date, f"{args.output}/weather_{date_str}.csv")
        
        for apt_id, apt_config in apartments.items():
            data = generate_apartment_data(apt_id, apt_config, weather, current_date)
            save_csv(data, f"{args.output}/{apt_id.lower()}_{date_str}.csv")
    
    print("\n" + "=" * 50)
    print("[OK] Terminé !")


if __name__ == "__main__":
    main()
