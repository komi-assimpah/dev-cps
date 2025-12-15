"""
Visualisation spatiale des appartements avec capteurs et murs.
"""

# Codes couleur ANSI pour le terminal
RESET = '\033[0m'
BLACK = '\033[48;5;16m  '       # Murs (noir)
RED = '\033[48;5;196m  '        # Capteurs température (rouge)
BLUE = '\033[48;5;21m  '        # Capteurs IAQ (bleu)
GREEN = '\033[48;5;46m  '       # Actionneurs (vert)
WHITE = '\033[48;5;255m  '      # Espaces vides (blanc)
GRAY = '\033[48;5;240m  '       # Extérieur (gris)


def print_spatial_view(flat, show_legend=True):
    """
    Affiche la grille spatiale avec les capteurs et murs.
    
    :param flat: Grille 2D de Cell objects
    :param show_legend: Afficher la légende
    """
    if show_legend:
        print("\n 🗺️  Légende :")
        print(f"   {BLACK}{RESET} = Murs (noir)")
        print(f"   {RED}{RESET} = Capteurs Température (rouge)")
        print(f"   {BLUE}{RESET} = Capteurs IAQ - CO2, CO, TVOC, PM2.5 (bleu)")
        print(f"   {GREEN}{RESET} = Actionneurs Chauffage (vert)")
        print(f"   {GRAY}{RESET} = Extérieur (gris)")
        print(f"   {WHITE}{RESET} = Espaces vides (blanc)")
        print()
    
    # Afficher la grille
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            
            # Priorité : capteurs > actionneurs > murs > extérieur > vide
            if cell.sensor == "SENSOR_TEMP":
                print(RED, end='')
            elif cell.sensor == "SENSOR_IAQ":
                print(BLUE, end='')
            elif cell.actuator is not None:
                print(GREEN, end='')
            elif cell.is_wall:
                print(BLACK, end='')
            elif cell.is_outside:
                print(GRAY, end='')
            else:
                print(WHITE, end='')
        
        print(RESET)  # Nouvelle ligne


def print_sensor_list(flat):
    """
    Affiche la liste des capteurs détectés dans la grille.
    
    :param flat: Grille 2D de Cell objects
    """
    sensors = []
    
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            if cell.sensor is not None:
                sensors.append({
                    'type': cell.sensor,
                    'room': cell.room,
                    'pos': (j, i)
                })
    
    if sensors:
        print("\n📍 Capteurs détectés :")
        temp_count = 0
        iaq_count = 0
        
        for sensor in sensors:
            icon = "[TEMP]" if sensor['type'] == "SENSOR_TEMP" else "[IAQ] "
            print(f"   {icon} {sensor['type']:15} | {sensor['room']:15} | Position: {sensor['pos']}")
            
            if sensor['type'] == "SENSOR_TEMP":
                temp_count += 1
            else:
                iaq_count += 1
        
        print(f"\n   Total : {temp_count} capteurs température, {iaq_count} capteurs IAQ")
    else:
        print("\n ⚠️  Aucun capteur détecté")


def print_actuator_list(flat):
    """
    Affiche la liste des actionneurs détectés dans la grille.
    
    :param flat: Grille 2D de Cell objects
    """
    actuators = []
    
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            if cell.actuator is not None:
                actuators.append({
                    'type': cell.actuator,
                    'room': cell.room,
                    'pos': (j, i)
                })
    
    if actuators:
        print("\n🔥 Actionneurs détectés :")
        for actuator in actuators:
            print(f"   [HEAT] {actuator['type']:15} | {actuator['room']:15} | Position: {actuator['pos']}")
        print(f"\n   Total : {len(actuators)} actionneurs")
    else:
        print("\n ⚠️  Aucun actionneur détecté")
