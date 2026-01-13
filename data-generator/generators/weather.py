"""
Générateur de données météo.
"""

import random
from datetime import datetime
from typing import List


import pandas as pd
from pathlib import Path

class WeatherProvider:
    _instance = None
    _df = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WeatherProvider()
        return cls._instance

    def __init__(self):
        csv_path = Path(__file__).parent.parent / "dataset" / "open-meteo-43.69N7.19E17m.csv"
        try:
            # Skip les 3 premieres lignes de metadonnees
            self._df = pd.read_csv(csv_path, skiprows=3)
            # Renommer les colonnes pour simplifier
            self._df.columns = ["time", "temp", "humidity"]
            self._df["time"] = pd.to_datetime(self._df["time"])
            self._df = self._df.set_index("time")
            print(f"[INFO] Meteo chargee: {len(self._df)} enregistrements ({self._df.index.min()} a {self._df.index.max()})")
        except Exception as e:
            print(f"[WARN] Impossible de charger la meteo ({e}), utilisation mode aleatoire")
            self._df = None

    def get_weather(self, date: datetime, hour: int, minute: int) -> dict:
        if self._df is None:
            return None
            
        # Construire le timestamp recherche (avec l'annee des donnees CSV)
        # Attention: Le CSV est en 2024-2025. Si on simule 2025-2026, il faut adapter l'annee
        # Option simple: On projette tout sur l'annee du CSV pour trouver la correspondance
        
        # Trouver l'annee disponible dans le CSV pour ce mois/jour
        target_month = date.month
        target_day = date.day
        
        # Chercher une date correspondante dans le CSV
        # On essaie de trouver une correspondance exacte jour/mois dans le dataframe
        # car le CSV couvre Nov 2024 a Nov 2025 (exemple)
        
        # Creation d'une date bidon pour chercher dans l'index
        # On regarde si on trouve 2024 ou 2025 dans le CSV
        search_date = pd.Timestamp(year=date.year, month=target_month, day=target_day, hour=hour, minute=0)
        
        # Si la date exacte n'est pas dans le CSV (ex: on simule 2026 mais CSV est 2024), 
        # on essaie de reculer d'un an
        if search_date not in self._df.index:
            search_date = search_date.replace(year=search_date.year - 1)
        
        # Si toujours pas, on essaie encore un an (CSV peut etre vieux)
        if search_date not in self._df.index:
             search_date = search_date.replace(year=search_date.year - 1)

        # Interpolation
        # Le CSV est horaire. Si on veut 10h10, on interpole entre 10h et 11h
        try:
            # Heure pile
            ts_start = search_date.replace(minute=0)
            # Heure suivante
            ts_end = ts_start + pd.Timedelta(hours=1)
            
            if ts_start in self._df.index and ts_end in self._df.index:
                row_start = self._df.loc[ts_start]
                row_end = self._df.loc[ts_end]
                
                # Ratio de minutes (ex: 10/60 = 0.16)
                ratio = minute / 60.0
                
                temp = row_start["temp"] + (row_end["temp"] - row_start["temp"]) * ratio
                hum = row_start["humidity"] + (row_end["humidity"] - row_start["humidity"]) * ratio
                
                return {"temp": temp, "humidity": hum}
            elif ts_start in self._df.index:
                # Fallback sur heure pile
                row = self._df.loc[ts_start]
                return {"temp": row["temp"], "humidity": row["humidity"]}
                
        except Exception:
            pass
            
        return None

def generate_weather_for_day(date: datetime, config: dict, interval_seconds: int = 600) -> List[dict]:
    """
    Génère la météo pour une journée. Essaie d'utiliser le CSV, sinon fallback aléatoire.
    """
    weather = []
    
    # Tenter de charger le provider
    provider = WeatherProvider.get_instance()
    
    # Parametres fallback
    temp_min = config["temp_min"]
    temp_max = config["temp_max"]
    humidity_base = config["humidity_base"]
    
    # Calculer le nombre de points dans la journée
    total_seconds_in_day = 24 * 60 * 60
    num_points = total_seconds_in_day // interval_seconds
    
    for i in range(num_points):
        # Convertir l'index en heure et minute
        total_minutes = (i * interval_seconds) // 60
        hour = total_minutes // 60
        minute = total_minutes % 60
        
        # Essayer de recuperer depuis CSV
        csv_data = provider.get_weather(date, hour, minute)
        
        if csv_data:
            temp = csv_data["temp"]
            humidity = csv_data["humidity"]
        else:
            # --- FALLBACK ALEATOIRE (code existant) ---
            hour_decimal = hour + minute / 60.0
            
            if hour_decimal <= 6:
                temp = temp_min + (hour_decimal / 6) * 1
            elif hour_decimal <= 15:
                progress = (hour_decimal - 6) / 9
                temp = temp_min + (temp_max - temp_min) * progress
            else:
                progress = (hour_decimal - 15) / 9
                temp = temp_max - (temp_max - temp_min) * progress * 0.7
            
            temp += random.uniform(-0.3, 0.3)
            
            # Humidité : inverse de la température
            humidity = humidity_base + (temp_min - temp) * 2
            humidity = max(40, min(85, humidity + random.uniform(-2, 2)))
        
        weather.append({
            "hour": hour,
            "minute": minute,
            "temp_ext": round(temp, 1),
            "humidity_ext": round(humidity, 1),
        })
    
    return weather


def get_external_pm25(hour: int) -> float:
    """
    Génère un niveau de PM2.5 extérieur réaliste pour environnement urbain.
    
    Pattern typique urbain :
    - Pic matin (7h-9h) : trafic routier
    - Creux après-midi (14h-16h) : dispersion atmosphérique
    - Pic soir (18h-20h) : trafic + chauffage domestique
    - Bas la nuit : peu d'activité
    
    Args:
        hour: Heure actuelle (0-23)
    
    Returns:
        Niveau PM2.5 extérieur (µg/m³)
    """
    base = 25  # OUTDOOR_PM25_URBAN
    
    # Pic matin (trafic)
    if 7 <= hour < 9:
        base += random.uniform(5, 15)
    
    # Pic soir (trafic + chauffage domestique)
    elif 18 <= hour < 21:
        base += random.uniform(10, 20)
    
    # Creux après-midi
    elif 14 <= hour < 17:
        base -= random.uniform(5, 10)
    
    # Nuit : faible activité
    elif 23 <= hour or hour < 6:
        base -= random.uniform(5, 10)
    
    weather_factor = random.uniform(-5, 5)
    
    result = base + weather_factor
    return max(5, min(100, result))
