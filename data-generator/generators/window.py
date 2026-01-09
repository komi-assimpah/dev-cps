"""
Générateur d'état des fenêtres.
"""

import random


def window_is_opened(
    current_open: bool,
    presence: bool,
    co2: float,
    hour: int,
    temp: float,
    room_name: str
) -> bool:
    """
    Décide si une fenêtre est ouverte selon la pièce et l'heure.
    
    Logique :
    1. Fermée si absent ou temp < 17°C
    2. Chaque pièce a des créneaux d'ouverture spécifiques
    3. Hors créneau → ferme automatiquement
    """
    if not presence:
        return False
    
    if temp < 17.0:
        return False
    
    
    if room_name == "sdb":
        in_slot = (7 <= hour <= 8) or (19 <= hour <= 21)
        if not in_slot:
            return False
        if current_open:
            return random.random() < 0.6  # 60% de rester ouverte
        return random.random() < 0.5  # 50% d'ouvrir
    
    if room_name == "cuisine":
        in_slot = hour in [7, 12, 19, 20] or co2 > 800
        if not in_slot:
            return False  # Ferme hors créneau
        if current_open:
            return random.random() < 0.5  # 50% de rester ouverte
        return random.random() < 0.4  # 40% d'ouvrir
    
    if room_name.startswith("chambre"):
        in_slot = (8 <= hour <= 9)
        if not in_slot:
            return False  # Ferme hors créneau
        if current_open:
            return random.random() < 0.5  # 50% de rester ouverte
        return random.random() < 0.3  # 30% d'ouvrir (pas toutes en même temps)
    
    if co2 > 1000:
        if current_open:
            return random.random() < 0.4  # 40% de rester ouverte
        return random.random() < 0.3  # 30% d'ouvrir
    
    return False
