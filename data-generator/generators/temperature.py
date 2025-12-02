"""
Générateur de température intérieure.
"""

import random


def update_temperature(
    current_temp: float,
    external_temp: float,
    window_open: bool,
    presence: bool,
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
        presence: Utilisateur présent
        temp_preference: Température préférée
        temp_offset: Offset selon orientation
        heat_loss_factor: Facteur de perte (étage)
        orientation: "north", "east", "south", "west"
        hour: Heure actuelle
    
    Returns:
        Nouvelle température
    """
    target_temp = temp_preference if presence else (temp_preference - 4)
    target_temp += temp_offset
    
    # Effet soleil selon orientation
    if orientation == "south" and 11 <= hour <= 16:
        target_temp += 1.5
    elif orientation == "east" and 7 <= hour <= 11:
        target_temp += 1.0
    elif orientation == "west" and 16 <= hour <= 20:
        target_temp += 1.0
    
    new_temp = current_temp + (target_temp - current_temp) * 0.08
    
    # Effet fenêtre ouverte
    if window_open:
        diff = external_temp - current_temp
        new_temp += diff * 0.15 * heat_loss_factor
    
    # Pertes naturelles
    diff = external_temp - current_temp
    new_temp += diff * 0.02 * heat_loss_factor
    
    # Bruit capteur
    new_temp += random.uniform(-0.1, 0.1)
    
    return round(new_temp, 1)
