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
