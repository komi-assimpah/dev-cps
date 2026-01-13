# Module IA - Préchauffage Intelligent

## Structure

```
IA/
├── extract_data.py      # Extraction des sessions depuis les CSV
├── train_model.py       # Entraînement du modèle XGBoost
├── heating_service.py   # Service d'inférence
├── requirements.txt     # Dépendances Python
└── xgboost_cours.md     # Documentation XGBoost
```

## Comment utiliser

### 1. Installer les dépendances

```bash
cd IA
pip install -r requirements.txt
```

### 2. Générer les données (mode batch)

```bash
cd ../data-generator
python generate.py --mode batch --days 7 --output ../IA/data
```

Cela génère 7 jours de données hivernales (Nice, 6-14°C) dans `IA/data/`.

### 3. Extraire les sessions de chauffage

```bash
cd ../IA
python extract_data.py
```

### 4. Entraîner le modèle

```bash
python train_model.py
```

### 5. Tester le service

```bash
python heating_service.py
```

## Architecture

```
data-generator (batch)
        │
        ▼
   CSV files (./data-generator/data/)
        │
        ▼
extract_data.py → training_data.csv
        │
        ▼
train_model.py → heating_model.json
        │
        ▼
heating_service.py (inférence)
        │
        ▼
{action, temps_chauffe, confort, energie}
```

## Entrée/Sortie du modèle

### Entrée
- `delta_temp`: Différence température cible - actuelle
- `temp_ext`: Température extérieure
- `hour`: Heure de la journée
- `temp_start`: Température de départ

### Sortie
- `action`: START_NOW, WAIT, ou NO_ACTION
- `temps_chauffe_minutes`: Temps estimé pour chauffer
- `confort_score`: Probabilité de confort à l'arrivée (0-1)
- `energie_estimee_kwh`: Consommation électrique estimée
