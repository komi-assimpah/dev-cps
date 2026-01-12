from config import INITIAL_SENSOR_VALUES


class RoomState:
    """État d'une pièce (valeurs courantes des capteurs)."""
    def __init__(self, apt_config: dict, room_name: str):
        user = apt_config["user"]
        self.temp = user["temp_preference"] - 1.5 + apt_config["temp_offset"]
        self.co2 = INITIAL_SENSOR_VALUES["co2"]
        self.humidity = INITIAL_SENSOR_VALUES["humidity"]
        self.pm25 = INITIAL_SENSOR_VALUES["pm25"]
        self.co = INITIAL_SENSOR_VALUES["co"]
        self.tvoc = INITIAL_SENSOR_VALUES["tvoc"]
        self.energy_kwh = 0.0
        self.window_open = False
        self.heater_on = False