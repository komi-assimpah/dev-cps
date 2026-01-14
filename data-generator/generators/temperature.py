"""
Générateur de température intérieure.
"""

import random


def update_temperature(
    current_temp: float,
    external_temp: float,
    window_open: bool,
    heater_on: bool,
    temp_preference: float,
    temp_offset: float,
    heat_loss_factor: float,
    orientation: str,
    hour: int
) -> float:
    """
    Calcule la nouvelle température d'une pièce.
    
    Args:
        current_temp: Température actuelle
        external_temp: Température extérieure
        window_open: Fenêtre ouverte
        heater_on: Chauffage actif (True/False)
        temp_preference: Température préférée
        temp_offset: Offset selon orientation
        heat_loss_factor: Facteur de perte (étage)
        orientation: "north", "east", "south", "west"
        hour: Heure actuelle
    
    Returns:
        Nouvelle température
    """
    new_temp = current_temp
    
    solar_gain = 0.0
    if orientation == "south" and 11 <= hour <= 16:
        solar_gain = 0.3
    elif orientation == "east" and 7 <= hour <= 11:
        solar_gain = 0.2
    elif orientation == "west" and 16 <= hour <= 20:
        solar_gain = 0.2
    elif orientation == "north" and 10 <= hour <= 16:
        solar_gain = 0.05
    new_temp += solar_gain
    
    if heater_on:
        target_temp = temp_preference + temp_offset
        new_temp += (target_temp - current_temp) * 0.15
    
    # Pertes naturelles
    diff = external_temp - current_temp
    new_temp += diff * 0.02 * heat_loss_factor
    
    if window_open:
        diff = external_temp - current_temp
        new_temp += diff * 0.15 * heat_loss_factor
    
    # Bruit capteur
    new_temp += random.uniform(-0.1, 0.1)
    
    return round(new_temp, 1)
