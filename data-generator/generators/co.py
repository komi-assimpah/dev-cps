"""
Générateur de niveau de monoxyde de carbone (CO).
Source : https://msss.gouv.qc.ca/professionnels/sante-environnementale/monoxyde-de-carbone/baremes-utilises-par-les-organismes-publics/
"""

import random

# Constantes CO en ppm (basées sur recommandations OMS 2010)
OUTDOOR_CO = 0.5            
MIN_CO = 0                   
MAX_CO = 500                
WHO_THRESHOLD_24H = 6        
WHO_THRESHOLD_1H = 25        
DANGER_THRESHOLD = 50        


def update_co(
    current_co: float,
    external_co: float,
    window_open: bool,
    presence: bool,
    room_name: str,
    hour: int
) -> float:
    """
    Calcule le nouveau niveau de monoxyde de carbone (CO).
    
    Args:
        current_co: Niveau actuel (ppm)
        external_co: Niveau extérieur (ppm, ~0.5 urbain)
        window_open: Fenêtre ouverte
        presence: Utilisateur présent
        room_name: Nom de la pièce (voir config.py : "cuisine", "salon", etc.)
        hour: Heure actuelle (0-23)
    
    Returns:
        Nouveau niveau de CO (ppm)
    """
    co_increase = 0
    
    
    if room_name == "cuisine" and presence:
        if 7 <= hour < 9:
            co_increase = random.uniform(0.3, 1.0)
        elif 12 <= hour < 14:
            co_increase = random.uniform(0.5, 1.5)
        elif 19 <= hour < 21:
            co_increase = random.uniform(0.8, 2.5)
        
        if random.random() < 0.01: # ANOMALIE RARE : brûleur encrassé/mal réglé
            co_increase += random.uniform(5, 15)
    
    new_co = current_co + co_increase
    
    
    if window_open:
        diff = external_co - new_co
        new_co += diff * 0.30
    
    if not window_open:
        diff = external_co - new_co
        new_co += diff * 0.05
    
    new_co = max(MIN_CO, min(MAX_CO, new_co))
    
    return round(new_co, 2)


def get_external_co() -> float:
    """
    Génère un niveau de CO extérieur réaliste (environnement urbain).
    Returns:
        Niveau CO extérieur (ppm)
    """
    base = OUTDOOR_CO
    variation = random.uniform(-0.2, 0.5)
    result = base + variation
    return max(0.1, min(2.0, result)) 
