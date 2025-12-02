"""
Générateur de niveau de particules fines PM2.5.
"""

import random

# Constantes PM2.5 (basées sur seuils OMS)
OUTDOOR_PM25_URBAN = 25      # Air extérieur urbain moyen en µg/m³
MIN_PM25 = 0                 # Minimum théorique
MAX_PM25 = 500               # Maximum capteur (pic extrême)
WHO_THRESHOLD_24H = 15       # Seuil OMS (moyenne 24h) en µg/m³
WHO_THRESHOLD_ANNUAL = 5    # Seuil OMS (moyenne annuelle) en µg/m³
MODERATE_PM25 = 50           # Seuil moyen
DEADLY_PM25 = 250            # Seuil dangereux


def update_pm25(
    current_pm25: float,
    external_pm25: float,
    window_open: bool,
    presence: bool,
    room_name: str,
    hour: int
) -> float:
    """
    Calcule le nouveau niveau de particules fines PM2.5.
    
    Les particules augmentent avec :
    - Activités de cuisine
    - Présence (mouvement, remise en suspension)
    
    Les particules diminuent avec :
    - Fenêtre ouverte (dilution avec air extérieur)
    - Dépôt naturel sur surfaces (10-20%/heure)
    
    Args:
        current_pm25: Niveau actuel (µg/m³)
        external_pm25: Niveau extérieur (µg/m³)
        window_open: Fenêtre ouverte
        presence: Utilisateur présent
        room_name: Nom de la pièce
        hour: Heure actuelle (0-23)
    
    Returns:
        Nouveau niveau de PM2.5 (µg/m³)
    """
    pm25_increase = 0
    
    if presence:
        # Base : mouvement, remise en suspension légère
        pm25_increase = random.uniform(0.5, 2.0)
        
        if room_name == "cuisine":
            if 7 <= hour < 9:
                pm25_increase += random.uniform(5, 15)
            
            if 12 <= hour < 14:
                pm25_increase += random.uniform(10, 30)
            
            if 19 <= hour < 21:
                pm25_increase += random.uniform(15, 50)
        
        elif room_name in ["salon", "studio"]:
            if 20 <= hour < 23 and random.random() < 0.1:  # 10% de chance
                pm25_increase += random.uniform(5, 20)
    
    new_pm25 = current_pm25 + pm25_increase
    
    
    if window_open:
        diff = external_pm25 - new_pm25
        new_pm25 += diff * 0.20
    

    if not window_open:
        decay_rate = 0.025
        new_pm25 = new_pm25 * (1 - decay_rate)
        
        diff = external_pm25 - new_pm25
        new_pm25 += diff * 0.02
    
    new_pm25 = max(MIN_PM25, min(MAX_PM25, new_pm25))
    
    return round(new_pm25, 2)