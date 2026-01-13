┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Modèle         │     │ Modèle         │     │ Modèle         │
│ Chauffage      │     │ Anomalies      │     │ Présence       │
└────────────────┘     └────────────────┘     └────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ↓
                      Orchestrateur (décision finale)





{
    "action": "START_NOW",           # Classification
    "temps_chauffe_estime": 18.5,    # Régression
    "confort_score": 0.92,           # Probabilité de confort à l'arrivée
    "energie_estimee_kwh": 0.45      # Estimation conso
}



ntrées/Sorties des modèles (Option A)
🔥 Modèle 1 : Préchauffage
python
# ENTRÉE
{
    "distance_km": 5.2,           # Distance utilisateur → maison
    "current_temp": 17.5,         # Température actuelle
    "target_temp": 21.0,          # Température souhaitée
    "external_temp": 8.0,         # Température extérieure
    "hour": 18,                   # Heure actuelle
    "heating_power": 1800         # Puissance chauffage (W)
}
# SORTIE
{
    "action": "START_HEATING",    # ou "WAIT" ou "ALREADY_WARM"
    "start_in_minutes": 0,        # Démarrer dans X minutes
    "estimated_ready_at": "18:35" # Température cible atteinte
}
🚨 Modèle 2 : Anomalies
python
# ENTRÉE
{
    "temperature": 45.2,          # Valeur capteur
    "humidity": 120,              # Valeur capteur
    "co2": 5000                   # Valeur capteur
}
# SORTIE
{
    "is_anomaly": true,
    "anomalies": [
        {"sensor": "temperature", "reason": "value_too_high"},
        {"sensor": "humidity", "reason": "impossible_value"}
    ]
}
🕐 Modèle 3 : Prédiction présence
python
# ENTRÉE
{
    "hour": 17,
    "day_of_week": 4,             # Vendredi
    "historical_presence": [0,0,0,1,1,1,...]  # 7 derniers jours
}
# SORTIE
{
    "predicted_presence": true,
    "probability": 0.87,
    "expected_arrival": "18:30"
}
Orchestrateur (combine les sorties)
python
# Reçoit les sorties des 3 modèles
presence = model_presence.predict(...)
anomaly = model_anomaly.detect(...)
heating = model_heating.decide(distance, presence, ...)
# Décision finale
if anomaly["is_anomaly"]:
    send_alert()
elif presence["predicted_presence"] and heating["action"] == "START_HEATING":
    start_heater()











## MODELE 1 Préchauffage

┌─────────────────────────────────────────────────────┐
│  1. Service GPS (API REST)                          │
│     → Reçoit position utilisateur                   │
│     → Calcule distance + temps estimé               │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────┐
│  2. Service Préchauffage                            │
│     → Lit température actuelle (MongoDB)            │
│     → Compare temps trajet vs temps chauffe         │
│     → Décide : START / WAIT                         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────┐
│  3. Actuateur (commande chauffage)                  │
│     → Envoie commande MQTT au chauffage             │
└─────────────────────────────────────────────────────┘