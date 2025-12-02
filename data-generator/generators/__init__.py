"""
Générateurs de données pour les capteurs.
"""

from .weather import generate_weather_for_day
from .presence import is_user_home
from .window import update_window
from .temperature import update_temperature
from .co2 import update_co2
from .humidity import update_humidity

__all__ = [
    "generate_weather_for_day",
    "is_user_home",
    "update_window",
    "update_temperature",
    "update_co2",
    "update_humidity",
]
