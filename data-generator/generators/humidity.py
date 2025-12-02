"""
Générateur d'humidité intérieure.
"""

import random


def update_humidity(
    current_humidity: float,
    external_humidity: float,
    window_open: bool,
    presence: bool,
    room_name: str,
    hour: int
) -> float:
    """
    Calcule la nouvelle humidité.
    
    L'humidité dépend :
    - De la fenêtre ouverte (tend vers extérieur)
    - Des activités (douche, cuisine)
    
    Args:
        current_humidity: Humidité actuelle (%)
        external_humidity: Humidité extérieure (%)
        window_open: Fenêtre ouverte
        presence: Utilisateur présent
        room_name: Nom de la pièce
        hour: Heure actuelle
    
    Returns:
        Nouvelle humidité (%)
    """
    new_humidity = current_humidity
    
    # Fenêtre ouverte : tend vers extérieur
    if window_open:
        diff = external_humidity - current_humidity
        new_humidity += diff * 0.1
    
    # Activités
    if presence:
        # Douche matin/soir
        if (7 <= hour <= 8 or 19 <= hour <= 20) and room_name == "sdb":
            new_humidity += random.uniform(3, 8)
        
        # Cuisine
        if (7 <= hour <= 8 or 12 <= hour <= 13 or 19 <= hour <= 20):
            if room_name == "cuisine":
                new_humidity += random.uniform(2, 5)
    
    # Retour à la normale (50%)
    new_humidity += (50 - new_humidity) * 0.03
    
    # Bornes
    new_humidity = max(30, min(80, new_humidity))
    
    return round(new_humidity + random.uniform(-1, 1), 1)
