# Bridge MQTT KAFKA

Recupere les infos de l'appartement, s'abonne aux topics MQTT
```
building/APT_10x/<room>/sensors
```
Nettoie ensuite les data, enleve les valeurs nulles, et applique un filtre median pour retirer les outliers, puis les publies sur les topics Kafka
```
APT_10x/<room>
```