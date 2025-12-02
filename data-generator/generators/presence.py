"""
Générateur de présence utilisateur.
"""

import random


def is_user_home(hour: int, minute: int, day_of_week: int, user_config: dict) -> bool:
    """
    Détermine si l'utilisateur est présent.
    
    Args:
        hour: Heure (0-23)
        minute: Minute (0-59)
        day_of_week: Jour (0=lundi, 6=dimanche)
        user_config: Config utilisateur avec "schedule" et "work_days"
    
    Returns:
        True si présent
    """
    schedule = user_config["schedule"]
    work_days = user_config["work_days"]
    
    current_time = hour + minute / 60
    
    # Jour non travaillé
    if day_of_week not in work_days:
        # Majoritairement à la maison, sauf sorties aléatoires
        if 10 <= hour <= 16 and random.random() < 0.2:
            return False
        return True
    
    # Jour travaillé
    wake = schedule["wake_up"]
    leave = schedule["leave_home"]
    back = schedule["come_back"]
    
    if wake <= current_time < leave:
        return True
    if leave <= current_time < back:
        return False
    if current_time >= back:
        return True
    
    return True
