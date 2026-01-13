"""
Générateurs de données pour les capteurs.
"""

from .weather import generate_weather_for_day, get_external_pm25
from .presence import is_user_home
from .window import window_is_opened
from .temperature import update_temperature
from .co2 import update_co2
from .humidity import update_humidity
from .pm25 import update_pm25
from .co import update_co, get_external_co
from .cov import update_tvoc, get_external_tvoc
from .energy import update_energy_consumption

__all__ = [
    "generate_weather_for_day",
    "get_external_pm25",
    "is_user_home",
    "window_is_opened",
    "update_temperature",
    "update_co2",
    "update_humidity",
    "update_pm25",
    "update_co",
    "get_external_co",
    "update_tvoc",
    "get_external_tvoc",
    "update_energy_consumption",
]
