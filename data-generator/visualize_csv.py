"""
Visualisation thermique à partir d'un CSV généré.

Lit un CSV de données de capteurs et affiche une animation
de la propagation thermique dans l'appartement.

Usage:
    dans le terminal :
      - python visualize_csv.py output/apt_101_2025-12-01.csv
      - python visualize_csv.py output/apt_101_2025-12-01.csv --speed 0.5
    pour les avoirs en png :
      - python visualize_csv.py output/apt_101_2025-12-01.csv --export frames/
"""

import csv
import sys
import time
import argparse
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from spatial.loader import FlatLoader
from visualization.thermal_view import visualize_thermal_state


def create_thermal_colormap():
    """
    palette de couleurs thermique (Cyan -> Jaune -> Orange -> Rouge)
    """
    colors = [
        (0.0, (0.2, 0.8, 0.8)),  # Cyan (10°C)
        (0.25, (0.9, 0.9, 0.2)), # Jaune (15°C)
        (0.5, (1.0, 0.6, 0.0)),  # Orange (20°C)
        (0.75, (1.0, 0.3, 0.0)), # Orange foncé (25°C)
        (1.0, (0.8, 0.0, 0.0))   # Rouge (30°C)
    ]
    return LinearSegmentedColormap.from_list('thermal', [c[1] for c in colors])


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
    parser.add_argument('--export', help='Exporter les frames en images PNG dans ce dossier')
    
    args = parser.parse_args()
    
    if args.export: # sauvegarder chaque frame en PNG
        from visualization.image_export import save_thermal_image
        import os
        
        os.makedirs(args.export, exist_ok=True)
        
        data = load_csv_data(args.csv_file)
        loader = FlatLoader()
        flat = loader.load_flat(f'config/apartments/{args.apartment}')
        grouped = group_by_timestamp(data)
        
        for idx, ts in enumerate(sorted(grouped.keys())):
            room_temps = grouped[ts]
            temp_ext = float([r for r in data if r['timestamp'] == ts][0]['temp_ext'])
            apply_thermal_diffusion(flat, room_temps, temp_ext)
            
            # Format: APT_101_2025-12-01T00-00-00.png
            ts_safe = ts.replace(':', '-')
            output_path = os.path.join(args.export, f'{args.apartment}_{ts_safe}.png')
            save_thermal_image(flat, output_path, cell_size=30, timestamp=ts, room_temps=room_temps)
        
        print(f"\n[OK] {idx+1} images exportées dans {args.export}/")
    else:
        visualize_csv(args.csv_file, args.apartment, args.speed)


if __name__ == '__main__':
    main()
