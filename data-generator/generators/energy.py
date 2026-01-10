"""
Générateur de consommation électrique du chauffage.
Formule: Consommation (kWh) = Puissance (W) * Temps (h) / 1000
"""

from config import ROOM_SURFACES

HEATING_POWER_PER_M2 = 100  # W/m²


def get_room_surface(room_name: str) -> float:
    return ROOM_SURFACES.get(room_name, 12)


def get_heater_power(room_name: str) -> float:
    return get_room_surface(room_name) * HEATING_POWER_PER_M2


def update_energy_consumption(
    current_energy_kwh: float,
    heater_on: bool,
    room_name: str,
    interval_minutes: int
) -> float:
    """
    Met à jour la consommation électrique cumulative.
    """
    if not heater_on:  # Chauffage OFF
        return current_energy_kwh
    else:  # Chauffage ON : calculer la conso de l'intervalle
        heater_power = get_heater_power(room_name)
        interval_consumption = heater_power * (interval_minutes / 60) / 1000
        return round(current_energy_kwh + interval_consumption, 4)
