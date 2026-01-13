"""
Service d'inférence pour le modèle de préchauffage.

Utilise le modèle XGBoost pour prédire le temps de chauffe
et calcule les métriques dérivées (action, confort, énergie).
"""

import xgboost as xgb
import pandas as pd
import numpy as np
import os

class HeatingPredictor:
    """
    Service de prédiction pour le préchauffage intelligent.
    """
    
    def __init__(self, model_path: str = "heating_model.json"):
        """Charge le modèle entraîné."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Modèle non trouvé: {model_path}. "
                "Exécutez d'abord train_model.py"
            )
        
        self.model = xgb.XGBRegressor()
        self.model.load_model(model_path)
        print(f"✓ Modèle chargé: {model_path}")
        
        # Mappings hardcodés (basés sur LabelEncoder par défaut trié)
        # Idéalement, il faudrait charger les LabelEncoder sauvegardés
        self.rooms_map = {
            'chambre': 0, 'chambre_1': 1, 'chambre_2': 2, 
            'cuisine': 3, 'salon': 4, 'sdb': 5
        }
        self.apt_map = {
            f'APT_{101+i}': i for i in range(4)
        }
        self.apt_map.update({f'APT_{201+i}': 4+i for i in range(4)})

    def prepare_features(self, temp_actuelle, temp_cible, temp_ext, humidity_ext, hour, room, apartment_id):
        """Reconstruit les 17 features exactes du training."""
        
        # 1. Variables de base
        delta_temp = temp_cible - temp_actuelle
        temp_preference = temp_cible  # Hypothèse pour la prédiction
        
        # 2. Encodage
        room_encoded = self.rooms_map.get(room, 0)
        apt_encoded = self.apt_map.get(apartment_id, 0)
        
        # 3. Features temporelles
        morning = 1 if 6 <= hour < 10 else 0
        day = 1 if 10 <= hour < 17 else 0
        evening = 1 if 17 <= hour < 22 else 0
        
        # 4. Features dérivées
        delta_squared = delta_temp ** 2
        temp_diff_ext = temp_actuelle - temp_ext
        heating_difficulty = delta_temp * (20 - temp_ext) / 10
        target_gap = temp_preference - temp_actuelle
        delta_x_hour = delta_temp * hour
        ext_x_hour = temp_ext * hour
        
        # Ordre EXACT des colonnes dans train_model.py
        features = [
            delta_temp,         # 0
            delta_squared,      # 1
            temp_ext,           # 2
            temp_actuelle,      # 3 (temp_start)
            temp_preference,    # 4
            humidity_ext,       # 5
            hour,               # 6
            room_encoded,       # 7
            apt_encoded,        # 8
            morning,            # 9
            day,                # 10
            evening,            # 11
            temp_diff_ext,      # 12
            heating_difficulty, # 13
            target_gap,         # 14
            delta_x_hour,       # 15
            ext_x_hour          # 16
        ]
        
        return np.array([features])

    def predict_heating_time(self, temp_actuelle: float, temp_cible: float,
                              temp_ext: float, humidity_ext: float, hour: int,
                              room: str = "salon", apartment_id: str = "APT_101") -> float:
        """
        Prédit le temps de chauffe en minutes.
        """
        if temp_cible <= temp_actuelle:
            return 0.0
        
        features = self.prepare_features(
            temp_actuelle, temp_cible, temp_ext, humidity_ext, hour, room, apartment_id
        )
        
        prediction = self.model.predict(features)[0]
        return max(0, float(prediction))
    
    def decide(self, eta_minutes: float, temp_actuelle: float,
               temp_cible: float, temp_ext: float, humidity_ext: float, hour: int,
               room: str = "salon", apartment_id: str = "APT_101",
               puissance_kw: float = 1.8) -> dict:
        """
        Prend une décision complète de préchauffage.
        """
        temps_chauffe = self.predict_heating_time(
            temp_actuelle, temp_cible, temp_ext, humidity_ext, hour, room, apartment_id
        )
        
        # Marge de sécurité (ex: 10%)
        temps_chauffe_safe = temps_chauffe * 1.1
        
        if temp_actuelle >= temp_cible:
            action = "NO_ACTION"
            reason = "Température atteinte"
        elif eta_minutes <= temps_chauffe_safe:
            action = "START_NOW"
            reason = f"Arrivée dans {eta_minutes}min, chauffe estimée {temps_chauffe:.0f}min"
        else:
            action = "WAIT"
            wait_time = eta_minutes - temps_chauffe_safe
            reason = f"Attendre {wait_time:.0f} min"
        
        energie_kwh = puissance_kw * (temps_chauffe / 60)
        
        return {
            "action": action,
            "temps_chauffe_minutes": round(temps_chauffe, 1),
            "energie_estimee_kwh": round(energie_kwh, 3),
            "reason": reason
        }


def demo():
    print("=" * 50)
    print("TEST DU MODÈLE DE PRÉCHAUFFAGE (XGBoost)")
    print("=" * 50)
    
    try:
        predictor = HeatingPredictor()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    scenarios = [
        # Cas 1: Hiver froid, matin, gros delta
        {"eta": 60, "t_act": 17, "t_cible": 21, "t_ext": 5, "hum": 80, "h": 7, "desc": "Matin froid (17->21°C)"},
        
        # Cas 2: Soirée douce, petit delta
        {"eta": 30, "t_act": 19.5, "t_cible": 21, "t_ext": 12, "hum": 60, "h": 18, "desc": "Soirée douce (19.5->21°C)"},
        
        # Cas 3: Retour we, apart froid
        {"eta": 120, "t_act": 15, "t_cible": 21, "t_ext": 4, "hum": 70, "h": 19, "desc": "Retour WE froid (15->21°C)"},
        
        # Cas 4: Déjà chaud
        {"eta": 15, "t_act": 21.5, "t_cible": 21, "t_ext": 10, "hum": 50, "h": 12, "desc": "Déjà chaud"},
    ]
    
    for s in scenarios:
        print(f"\n📍 {s['desc']}")
        print(f"   Conditions: T_int={s['t_act']}°C, T_ext={s['t_ext']}°C, Hum={s['hum']}%, Heure={s['h']}h")
        
        res = predictor.decide(
            eta_minutes=s["eta"],
            temp_actuelle=s["t_act"],
            temp_cible=s["t_cible"],
            temp_ext=s["t_ext"],
            humidity_ext=s["hum"],
            hour=s["h"]
        )
        
        print(f"   � Action: {res['action']}")
        print(f"   ⏱️  Prédiction: {res['temps_chauffe_minutes']} min")
        print(f"   � {res['reason']}")

if __name__ == "__main__":
    demo()
