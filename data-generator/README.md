# Générateur de Données Capteurs IoT

Ce composant génère des données synthétiques réalistes de capteurs IoT pour les appartements d'un immeuble.

---

## Utilisation Rapide

```bash
cd data-generator

# Générer 1 jour pour tous les appartements
python generate.py

# Générer 7 jours
python generate.py --days 7

# Générer pour un seul appartement
python generate.py --apartment APT_101
```

**Sortie** : Les CSV sont créés dans `output/`

---

## Fichiers Générés

| Fichier | Contenu |
|---------|---------|
| `weather_YYYY-MM-DD.csv` | Météo externe (température, humidité) |
| `apt_101_YYYY-MM-DD.csv` | Données capteurs APT_101 |
| ... | Un fichier par appartement |

### Colonnes des CSV capteurs

```csv
timestamp,apartment_id,room,window_open,presence,temperature,humidity,co2,pm25,co,tvoc,temp_ext,humidity_ext
```

| Colonne | Description |
|---------|-------------|
| `temperature` | °C intérieure |
| `humidity` | % humidité |
| `co2` | ppm (null si pas de capteur) |
| `pm25` | µg/m³ particules fines |
| `co` | ppm monoxyde de carbone |
| `tvoc` | µg/m³ composés volatils |

---

## 🏢 Les 8 Appartements

| ID | Étage | Orientation | Type | Pièces |
|----|-------|-------------|------|--------|
| APT_101 | 1 | Nord | T3 | salon, cuisine, chambre_1, chambre_2, sdb |
| APT_102 | 1 | Est | T2 | salon, chambre, cuisine, sdb |
| APT_103 | 1 | Sud | T3 | salon, cuisine, chambre_1, chambre_2, sdb |
| APT_104 | 1 | Ouest | Studio | studio, sdb |
| APT_201 | 2 | Nord | T2 | salon, chambre, cuisine, sdb |
| APT_202 | 2 | Est | Studio | studio, sdb |
| APT_203 | 2 | Sud | T3 | salon, cuisine, chambre_1, chambre_2, sdb |
| APT_204 | 2 | Ouest | T2 | salon, chambre, cuisine, sdb |

---

## ⚙️ Comment ça Marche

### Vue d'ensemble

```
generate.py
    │
    ├── Pour chaque jour
    │   ├── Génère météo du jour (weather.py)
    │   │
    │   └── Pour chaque appartement
    │       └── Pour chaque pièce
    │           └── Toutes les 5 min :
    │               ├── presence.py   → L'utilisateur est-il là ?
    │               ├── window.py     → Fenêtre ouverte ?
    │               ├── temperature.py → Calcul température
    │               ├── humidity.py    → Calcul humidité
    │               ├── co2.py         → Calcul CO2
    │               ├── pm25.py        → Calcul PM2.5
    │               ├── co.py          → Calcul CO
    │               └── cov.py         → Calcul TVOC
    │
    └── Sauvegarde CSV
```

### Logique de Simulation

#### Température (`generators/temperature.py`)

```python
# Facteurs pris en compte :
- Température cible selon présence (préférence user mise dans la config ou cette température soustrait de 4°C si absent)
- Effet soleil selon orientation (sud +1.5°C midi, est/ouest +1°C)
- Pertes si fenêtre ouverte (15% de la diff avec extérieur)
- Pertes naturelles (2% de la diff)
- Bruit capteur (±0.1°C)
```

#### CO2 (`generators/co2.py`)

```python
# Production selon activité :
- Nuit (23h-7h) : +15-25 ppm/5min dans chambres
- Petit-déj (7h-9h) : +20-40 ppm cuisine
- Déjeuner (12h-14h) : +25-50 ppm cuisine
- Dîner (19h-21h) : +30-60 ppm cuisine
- Soirée (20h-23h) : +10-20 ppm salon

# Fenêtre ouverte : -40 à -80 ppm/5min
```

#### Présence (`generators/presence.py`)

Basée sur le profil utilisateur dans `config.py` :
- `wake_up`, `leave_home`, `come_back`, `sleep_time`
- `work_days` : jours travaillés (0=Lundi)

####  Fenêtre (`generators/window.py`)

S'ouvre si :
- CO2 > 1200 ppm ET utilisateur présent, on part du principe que c'est l'utilisateur qui ouvre la fenêtre
- Reste ouverte 15-30 min

---

## Personnalisation

### pour modifier un appartement

Dans `config.py` :

```python
"APT_101": {
    "temp_offset": -1.0,        # Décalage température (nord = froid)
    "heat_loss_factor": 1.0,    # 1.3 pour étage 2 (plus exposé)
    "user": {
        "schedule": {"wake_up": 7, "leave_home": 8, "come_back": 18, "sleep_time": 23},
        "work_days": [0, 1, 2, 3, 4],  # Lundi-Vendredi
        "temp_preference": 24.0,
    }
}
```

### pour modifier la météo

```python
WEATHER = {
    "temp_min": 6.0,   # Nuit
    "temp_max": 14.0,  # Après-midi
    "humidity_base": 65.0,
}
```

### pour modifier les seuils capteurs

Éditer directement les fichiers `generators/*.py` :

| Fichier | Constantes importantes |
|---------|------------------------|
| `co2.py` | `OUTDOOR_CO2_PPM = 420`, seuil fenêtre 1200 |
| `pm25.py` | Base urbaine 25 µg/m³ |
| `temperature.py` | Inertie 0.08, pertes 0.02 |

---

## pour visualiser les spatial de l'évolution des températures

```bash
# Installer dépendances
pip install numpy matplotlib

# Visualiser en temps réel
python visualize_csv.py output/apt_101_2025-12-01.csv

# Exporter en PNG
python visualize_csv.py output/apt_101_2025-12-01.csv --export frames/
```

---

## Structure du Projet

```
data-generator/
├── generate.py           # Script principal
├── config.py             # Configuration appartements + météo
├── generators/           # Logique de chaque capteur
│   ├── temperature.py
│   ├── co2.py
│   ├── humidity.py
│   ├── pm25.py
│   ├── co.py
│   ├── cov.py
│   ├── presence.py
│   ├── window.py
│   └── weather.py
├── visualize_csv.py      # Visualisation thermique
├── spatial/              # Grille 2D des appartements
├── visualization/        # Export images
└── output/               # CSV générés
```
