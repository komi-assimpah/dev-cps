"""
Générateur d'état des fenêtres.
"""

import random


def update_window(current_open: bool, presence: bool, co2: float, hour: int) -> bool:
    """
    Décide si une fenêtre est ouverte ou fermée.
    
    Logique :
    - Absent → fermée
    - CO2 > 1000 → chance d'ouvrir
    - Aération matinale (8h-10h) → chance d'ouvrir
    - Déjà ouverte → chance de fermer
    
    Args:
        current_open: État actuel
        presence: Utilisateur présent
        co2: Niveau de CO2 (ppm)
        hour: Heure actuelle
    
    Returns:
        True si ouverte
    """
    if not presence:
        return False
    
    if current_open:
        return random.random() > 0.2  # 20% chance de fermer
    
    # CO2 élevé
    if co2 > 1000 and random.random() < 0.5:
        return True
    
    # Aération matinale
    if 8 <= hour <= 10 and random.random() < 0.15:
        return True
    
    return False
