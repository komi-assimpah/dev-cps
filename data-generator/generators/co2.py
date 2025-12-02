"""
Générateur de niveau de CO2.
"""

import random

# Constantes CO2
OUTDOOR_CO2_PPM = 420
DEADLY_CO2_PPM = 1500
MIN_CO2_PPM = 400
MAX_CO2_PPM = 2500


def update_co2(
    current_co2: float,
    presence: bool,
    window_open: bool,
    room_name: str,
    hour: int
) -> float:
    """
    Calcule le nouveau niveau de CO2.
    
    La production de CO2 dépend :
    - De la présence (respiration)
    - De l'activité selon l'heure et la pièce
    - De l'aération (fenêtre)
    
    Args:
        current_co2: Niveau actuel (ppm)
        presence: Utilisateur présent
        window_open: Fenêtre ouverte
        room_name: Nom de la pièce
        hour: Heure actuelle
    
    Returns:
        Nouveau niveau de CO2 (ppm)
    """
    co2_increase = 0
    
    if presence:
        # Base : respiration normale
        co2_increase = random.uniform(5, 12)
        
        # === ACTIVITÉS SELON L'HEURE ET LA PIÈCE ===
        # Nuit (23h-7h) : accumulation chambres
        if hour >= 23 or hour < 7:
            if "chambre" in room_name or room_name == "studio":
                co2_increase += random.uniform(15, 25)
        
        # Petit-déjeuner (7h-9h)
        if 7 <= hour < 9:
            if room_name == "cuisine":
                co2_increase += random.uniform(20, 40)
            elif room_name in ["salon", "studio"]:
                co2_increase += random.uniform(5, 10)
        
        # Déjeuner (12h-14h)
        if 12 <= hour < 14:
            if room_name == "cuisine":
                co2_increase += random.uniform(25, 50)
            elif room_name in ["salon", "studio"]:
                co2_increase += random.uniform(10, 20)
        
        # Dîner (19h-21h)
        if 19 <= hour < 21:
            if room_name == "cuisine":
                co2_increase += random.uniform(30, 60)
            elif room_name in ["salon", "studio"]:
                co2_increase += random.uniform(15, 25)
        
        # Soirée (20h-23h)
        if 20 <= hour < 23:
            if room_name in ["salon", "studio"]:
                co2_increase += random.uniform(10, 20)
    
    new_co2 = current_co2 + co2_increase
    
    if window_open:
        new_co2 -= random.uniform(40, 80)
    
    # Tendance vers extérieur
    new_co2 += (OUTDOOR_CO2_PPM - new_co2) * 0.02
    
    # Bornes
    new_co2 = max(MIN_CO2_PPM, min(MAX_CO2_PPM, new_co2))
    
    return round(new_co2, 0)
