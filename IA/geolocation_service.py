"""
Service de Géolocalisation.
Responsabilité : Fournir les données de localisation (Distance/Temps) simulées ou réelles.
en prod on utilisera des services externes comme OpenRouteService 
"""

from datetime import datetime

class GeolocationService:
    def __init__(self):
        self.simulated_positions = {
            "APT_101": {"distance": 25.5, "time": 45}, # distance moyenne
            "APT_102": {"distance": 5.0, "time": 15},  # Proche
            "APT_103": {"distance": 1200.0, "time": 900}, # Loin
        }

    def get_location_update(self, apartment_id: str) -> dict:
        pos = self.simulated_positions.get(apartment_id, {"distance": 50.0, "time": 60})
        
        return {
            "apartment_id": apartment_id,
            "distance": float(pos["distance"]),     # km
            "time": float(pos["time"]),             # minutes (ETA)
            "timestamp": datetime.now().isoformat()
        }
