"""
Générateur de niveau de COV (Composés Organiques Volatils / TVOC).
Source : https://enless-wireless.fr/monitoring-cov/
"""

import random

# Constantes TVOC (Total Volatile Organic Compounds) - Basées sur OMS/Enless
OUTDOOR_TVOC = 50
MIN_TVOC = 0
MAX_TVOC = 10000
EXCELLENT_THRESHOLD = 250
ACCEPTABLE_THRESHOLD = 1000
DANGER_THRESHOLD = 3000


def update_tvoc(
    current_tvoc: float,
    external_tvoc: float,
    window_open: bool,
    presence: bool,
    room_name: str,
    hour: int
) -> float:
    """
    Calcule le nouveau niveau de COV totaux (TVOC) d'une pièce.
    
    Sources par pièce :
    - Cuisine : cuisson (huiles chauffées, combustion)
    - Salon : meubles, produits d'entretien
    - Chambre : textiles, cosmétiques
    - SDB : produits d'hygiène, cosmétiques
    
    Args:
        current_tvoc: Niveau actuel (µg/m³)
        external_tvoc: Niveau extérieur (µg/m³, ~50 urbain)
        window_open: Fenêtre ouverte
        presence: Utilisateur présent
        room_name: Nom de la pièce
        hour: Heure actuelle (0-23)
    
    Returns:
        Nouveau niveau de TVOC (µg/m³)
    """
    tvoc_increase = 0
    base_emission = random.uniform(5, 15)
    
    
    if presence:
        if room_name == "cuisine":
            if 7 <= hour < 9:
                tvoc_increase = random.uniform(50, 150)
            elif 12 <= hour < 14:
                tvoc_increase = random.uniform(100, 250)
            elif 19 <= hour < 21:
                tvoc_increase = random.uniform(150, 350)
        
        elif room_name == "sdb":
            if 7 <= hour < 9 and random.random() < 0.4:
                tvoc_increase = random.uniform(200, 400)
            elif 20 <= hour < 22 and random.random() < 0.3:
                tvoc_increase = random.uniform(200, 400)
        
        elif "chambre" in room_name:
            if 7 <= hour < 9 and random.random() < 0.3:
                tvoc_increase = random.uniform(100, 250)
        
        elif room_name == "salon":
            if 10 <= hour < 12 and random.random() < 0.1:
                tvoc_increase = random.uniform(300, 600)
    

    new_tvoc = current_tvoc + base_emission + tvoc_increase
    
    
    if window_open:
        diff = external_tvoc - new_tvoc
        new_tvoc += diff * 0.15
    
    if not window_open:
        diff = external_tvoc - new_tvoc
        new_tvoc += diff * 0.02
    
    new_tvoc = max(MIN_TVOC, min(MAX_TVOC, new_tvoc))
    
    return round(new_tvoc, 2)


def get_external_tvoc() -> float:
    base = OUTDOOR_TVOC    
    variation = random.uniform(-20, 50)
    result = base + variation
    return max(20, min(150, result))