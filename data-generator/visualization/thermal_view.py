"""
Visualisation thermique avec carte de chaleur colorée.
"""

# Codes couleur ANSI
RESET = '\033[0m'
BLACK = '\033[48;5;16m  '  # noir pour les murs


def get_color_square_temp(temp):
    """
    Retourne un carré coloré basé sur la température.
    Palette CHAUDE pour visualiser la propagation de chaleur.
    
    - Cyan   : 10-15°C (froid)
    - Jaune  : 15-20°C (tiède)
    - Orange : 20-25°C (chaud)
    - Rouge  : 25-30°C (très chaud)
    
    Args:
        temp: Température en °C (-1 pour mur)
    
    Returns:
        code ANSI coloré en String
    """
    if temp == -1:
        return BLACK
    
    temp = max(10, min(30, temp))
    
    if temp < 15:  # Cyan (10-15°C) - Froid
        ratio = (temp - 10) / 5.0
        color_code = int(51 + ratio * 10)
    elif temp < 20: # Jaune (15-20°C) - Tiède
        ratio = (temp - 15) / 5.0
        color_code = int(220 + ratio * 6)
    elif temp < 25: # Orange (20-25°C) - Chaud
        ratio = (temp - 20) / 5.0
        color_code = int(208 + ratio * 8)
    else: # Rouge (25-30°C) - Très chaud
        ratio = (temp - 25) / 5.0
        color_code = int(196 + ratio * 4)
    return f'\033[48;5;{color_code}m  {RESET}'


def print_thermal_map(flat, show_temps=False):
    """
    Affiche la carte thermique colorée de l'appartement.
    
    Args:
        flat: Grille 2D de Cell objects
        show_temps: Afficher les températures numériques
    """
    print("\n Carte Thermique (Propagation de chaleur) :")
    print("   Cyan (10-15°C) - Jaune (15-20°C) - Orange (20-25°C) - Rouge (25-30°C)\n")
    
    
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            temp = cell.temp
            
            if cell.is_wall and not cell.is_window:
                print(BLACK, end='')
                continue
            
            if cell.is_outside:
                print('\033[48;5;57m  \033[0m', end='')  # Violet foncé
                continue
            
            color_square = get_color_square_temp(temp)
            
            if cell.sensor == "SENSOR_TEMP":
                print('\033[48;5;196m T\033[0m', end='') # Capteur température - fond rouge avec T
            elif cell.sensor == "SENSOR_IAQ": 
                print('\033[48;5;21m I\033[0m', end='') # Capteur IAQ - fond bleu avec I
            elif cell.actuator: # Actionneur - fond vert avec H
                print('\033[48;5;46m H\033[0m', end='')
            else:
                print(color_square, end='')
        
        print(RESET)


def print_temperature_legend():
    print("\n Légende des températures :")
    
    temps = [0, 10, 15, 20, 25, 30, 40, 50, 60]
    
    for temp in temps:
        color = get_color_square_temp(temp)
        print(f"   {color}{RESET} = {temp:2d}°C")


def print_room_temperatures(flat):
    """
    Affiche les températures des capteurs par pièce.
    
    Args:
        flat: Grille 2D de Cell objects
    """
    room_temps = {}
    
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            if cell.sensor == "SENSOR_TEMP" and cell.room:
                room_temps[cell.room] = cell.temp
    
    if room_temps:
        print("\nTempératures par pièce (capteurs) :")
        for room in sorted(room_temps.keys()):
            temp = room_temps[room]
            color = get_color_square_temp(temp)
            print(f"   {color}{RESET} {room:15} : {temp:5.1f}°C")


def visualize_thermal_state(flat, timestamp=None, show_legend=False):
    """
    Visualisation complète de l'état thermique.
    
    Args:
        flat: Grille 2D de Cell objects
        timestamp: Horodatage optionnel
        show_legend: Afficher la légende des couleurs
    """
    print("\n" + "=" * 60)
    if timestamp:
        print(f"[{timestamp}]")
    print("=" * 60)
    
    print_thermal_map(flat)
    print_room_temperatures(flat)
    if show_legend:
        print_temperature_legend()
    
    print("=" * 60)
