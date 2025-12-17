"""
Visualisation thermique à partir d'un CSV généré.

Lit un CSV de données de capteurs et affiche une animation
de la propagation thermique dans l'appartement.

Usage:
    python visualize_csv.py output/apt_101_2025-12-01.csv
    python visualize_csv.py output/apt_101_2025-12-01.csv --speed 0.5
"""

import csv
import sys
import time
import argparse
from datetime import datetime
from spatial.loader import FlatLoader
from visualization.thermal_view import visualize_thermal_state


def load_csv_data(csv_path):
    """
    Charge les données du CSV.
    
    Returns:
        List of dicts avec les données par timestamp
    """
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data


def group_by_timestamp(data):
    """
    Groupe les données par timestamp.
    
    Returns:
        Dict {timestamp: {room: temperature}}
    """
    grouped = {}
    
    for row in data:
        ts = row['timestamp']
        room = row['room']
        temp = float(row['temperature'])
        
        if ts not in grouped:
            grouped[ts] = {}
        
        grouped[ts][room] = temp
    
    return grouped


def apply_thermal_diffusion(flat, room_temps, temp_ext):
    """
    Applique les températures du CSV sur la grille spatiale.
    
    Args:
        flat: Grille 2D de cellules de l'appart
        room_temps: Dict {room_name: temperature}
        temp_ext: Température extérieure
    """
    
    for i in range(len(flat)):
        for j in range(len(flat[i])):
            cell = flat[i][j]
            
            if cell.is_wall and not cell.is_window:
                cell.temp = -1
            elif cell.is_outside:
                cell.temp = temp_ext
            elif cell.room and cell.room in room_temps:
                cell.temp = room_temps[cell.room]
            else:
                cell.temp = temp_ext


def visualize_csv(csv_path, apartment_id, speed=1.0):
    """
    Visualise les données thermiques d'un CSV.
    
    Args:
        csv_path: Chemin vers le CSV
        apartment_id: ID de l'appartement (ex: APT_101)
        speed: Vitesse de lecture (1.0 = normal, 0.5 = lent, 2.0 = rapide)
    """
    data = load_csv_data(csv_path)
    
    print(f"Chargement de la grille spatiale : {apartment_id}")
    loader = FlatLoader()
    flat = loader.load_flat(f'config/apartments/{apartment_id}')
    
    grouped = group_by_timestamp(data)
    
    timestamps = sorted(grouped.keys())
    print(f"[OK] {len(timestamps)} timestamps trouves")
    print(f"Vitesse : {speed}x")
    print("\n" + "="*60)
    print("Appuyez sur Ctrl+C pour arreter")
    print("="*60)
    
    delay = 0.5 / speed
    
    try:
        for ts in timestamps:
            room_temps = grouped[ts]
            temp_ext = float([r for r in data if r['timestamp'] == ts][0]['temp_ext'])
            
            apply_thermal_diffusion(flat, room_temps, temp_ext)
            
            print("\033[2J\033[H")  # Clear screen
            visualize_thermal_state(flat, timestamp=ts)
            
            time.sleep(delay)
    
    except KeyboardInterrupt:
        print("\n\n  Arrêté par l'utilisateur")


def main():
    parser = argparse.ArgumentParser(description="Visualise les données thermiques d'un CSV")
    parser.add_argument('csv_file', help='Chemin vers le fichier CSV')
    parser.add_argument('--speed', type=float, default=1.0, help='Vitesse de lecture (défaut: 1.0)')
    parser.add_argument('--apartment', default='APT_101', help='ID de l\'appartement (défaut: APT_101)')
    
    args = parser.parse_args()
    
    visualize_csv(args.csv_file, args.apartment, args.speed)


if __name__ == '__main__':
    main()
