"""
Générateur de données météo.
"""

import random
from datetime import datetime
from typing import List


def generate_weather_for_day(date: datetime, config: dict) -> List[dict]:
    """
    Génère la météo pour une journée (144 points = 24h × 6/h).
    
    Args:
        date: Date du jour
        config: {"temp_min": float, "temp_max": float, "humidity_base": float}
    
    Returns:
        Liste de {hour, minute, temp_ext, humidity_ext}
    """
    weather = []
    temp_min = config["temp_min"]
    temp_max = config["temp_max"]
    humidity_base = config["humidity_base"]
    
    for hour in range(24):
        for minute in [0, 10, 20, 30, 40, 50]:
            # Température : min à 6h, max à 15h
            if hour <= 6:
                temp = temp_min + (hour / 6) * 1
            elif hour <= 15:
                progress = (hour - 6) / 9
                temp = temp_min + (temp_max - temp_min) * progress
            else:
                progress = (hour - 15) / 9
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
