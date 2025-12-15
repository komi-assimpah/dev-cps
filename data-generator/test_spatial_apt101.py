#!/usr/bin/env python3
"""
Script de test pour la représentation spatiale de APT_101.
Affiche la grille avec les murs, capteurs et actionneurs.
"""

import sys
import os

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spatial.loader import FlatLoader
from visualization.spatial_view import print_spatial_view, print_sensor_list, print_actuator_list


def main():
    print("=" * 60)
    print("🏢 TEST : Représentation Spatiale APT_101")
    print("=" * 60)
    
    try:
        # Charger l'appartement
        print("\n📂 Chargement de l'appartement...")
        loader = FlatLoader()
        flat = loader.load_flat('config/apartments/APT_101')
        
        print(f"✅ Grille chargée : {len(flat)}x{len(flat[0])} cellules")
        
        # Afficher les listes de capteurs et actionneurs
        print_sensor_list(flat)
        print_actuator_list(flat)
        
        # Afficher la visualisation spatiale
        print("\n" + "=" * 60)
        print("🗺️  VISUALISATION SPATIALE")
        print("=" * 60)
        print_spatial_view(flat, show_legend=True)
        
        print("\n" + "=" * 60)
        print("✅ Test terminé avec succès !")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Erreur : Fichier non trouvé")
        print(f"   {e}")
        print("\n💡 Vérifiez que les fichiers suivants existent :")
        print("   - config/apartments/APT_101/config.yml")
        print("   - config/apartments/APT_101/plan.png")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
