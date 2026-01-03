"""
Configuration des 8 appartements de l'immeuble.

Structure :
- Étage 1 : APT_101 (Nord), APT_102 (Est), APT_103 (Sud), APT_104 (Ouest)
- Étage 2 : APT_201 (Nord), APT_202 (Est), APT_203 (Sud), APT_204 (Ouest)
"""
#TODO: IDEE ->representer les apparts sous forme de tableau 2D avec l'emplacement des capteurs, murs... pour mieux piloter les modif des conditions avec un yaml

APARTMENTS = {
    # =================== ÉTAGE 1 ===================
    "APT_101": {
        "floor": 1,
        "orientation": "north",
        "type": "T3",
        "rooms": ["salon", "cuisine", "chambre_1", "chambre_2", "sdb"],
        "rooms_with_co2": ["salon", "cuisine"],
        "temp_offset": -1.0,
        "heat_loss_factor": 1.0,
        "user": {
            "name": "Famille Martin",
            "schedule": {"wake_up": 7, "leave_home": 8, "come_back": 18, "sleep_time": 23},
            "work_days": [0, 1, 2, 3, 4],
            "temp_preference": 24.0,
        }
    },
    "APT_102": {
        "floor": 1,
        "orientation": "east",
        "type": "T2",
        "rooms": ["salon", "chambre", "cuisine", "sdb"],
        "rooms_with_co2": ["salon"],
        "temp_offset": +0.5,
        "heat_loss_factor": 1.0,
        "user": {
            "name": "Marc Dupont",
            "schedule": {"wake_up": 6, "leave_home": 7, "come_back": 19, "sleep_time": 23},
            "work_days": [0, 1, 2, 3, 4],
            "temp_preference": 20.0,
        }
    },
    "APT_103": {
        "floor": 1,
        "orientation": "south",
        "type": "T3",
        "rooms": ["salon", "cuisine", "chambre_1", "chambre_2", "sdb"],
        "rooms_with_co2": ["salon", "cuisine"],
        "temp_offset": +1.5,
        "heat_loss_factor": 1.0,
        "user": {
            "name": "Famille Bernard",
            "schedule": {"wake_up": 7, "leave_home": 8, "come_back": 17, "sleep_time": 22},
            "work_days": [0, 1, 2, 3, 4],
            "temp_preference": 20.5,
        }
    },
    "APT_104": {
        "floor": 1,
        "orientation": "west",
        "type": "Studio",
        "rooms": ["studio", "sdb"],
        "rooms_with_co2": ["studio"],
        "temp_offset": +0.8,
        "heat_loss_factor": 1.0,
        "user": {
            "name": "Julie Student",
            "schedule": {"wake_up": 9, "leave_home": 10, "come_back": 18, "sleep_time": 1},
            "work_days": [0, 1, 2, 3],
            "temp_preference": 22.0,
        }
    },
    
    # =================== ÉTAGE 2 ===================
    "APT_201": {
        "floor": 2,
        "orientation": "north",
        "type": "T2",
        "rooms": ["salon", "chambre", "cuisine", "sdb"],
        "rooms_with_co2": ["salon", "cuisine"],
        "temp_offset": -1.5,
        "heat_loss_factor": 1.3,
        "user": {
            "name": "Pierre Télétravail",
            "schedule": {"wake_up": 8, "leave_home": 12, "come_back": 13, "sleep_time": 23},
            "work_days": [0, 1, 2, 3, 4],
            "temp_preference": 21.5,
        }
    },
    "APT_202": {
        "floor": 2,
        "orientation": "east",
        "type": "Studio",
        "rooms": ["studio", "sdb"],
        "rooms_with_co2": ["studio"],
        "temp_offset": 0.0,
        "heat_loss_factor": 1.3,
        "user": {
            "name": "Sophie Infirmière",
            "schedule": {"wake_up": 5, "leave_home": 6, "come_back": 15, "sleep_time": 21},
            "work_days": [0, 1, 2, 4, 5],
            "temp_preference": 20.0,
        }
    },
    "APT_203": {
        "floor": 2,
        "orientation": "south",
        "type": "T3",
        "rooms": ["salon", "cuisine", "chambre_1", "chambre_2", "sdb"],
        "rooms_with_co2": ["salon", "cuisine"],
        "temp_offset": +1.0,
        "heat_loss_factor": 1.3,
        "user": {
            "name": "Retraités Durand",
            "schedule": {"wake_up": 7, "leave_home": 10, "come_back": 12, "sleep_time": 22},
            "work_days": [1, 3, 5],
            "temp_preference": 22.0,
        }
    },
    "APT_204": {
        "floor": 2,
        "orientation": "west",
        "type": "T2",
        "rooms": ["salon", "chambre", "cuisine", "sdb"],
        "rooms_with_co2": ["salon"],
        "temp_offset": +0.3,
        "heat_loss_factor": 1.3,
        "user": {
            "name": "Couple Moreau",
            "schedule": {"wake_up": 6, "leave_home": 7, "come_back": 18, "sleep_time": 23},
            "work_days": [0, 1, 2, 3, 4],
            "temp_preference": 20.5,
        }
    },
}

# Météo de base (Nice, hiver)
#TODO: retrieve a real weather dataset in csv file
WEATHER = {
    "temp_min": 6.0,
    "temp_max": 14.0,
    "humidity_base": 65.0,
}
