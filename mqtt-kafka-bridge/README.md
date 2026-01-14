# Bridges MQTT KAFKA

## Cleaners (pour scores & pour user) - Consumer MQTT / Producer Kafka

Recoivent les donnees du topic `building/{apt}/{room}/sensors`, et nettoient les données avec ce pipeline :
- Nettoyage des valeurs nulles (répète la donnée précédente)
- Vérifie que la donnée est bien comprise dans l'intervale de mesure du capteur (répète la donnée précédente)
- Applique ensuite un filtre médian pour filtrer les outliers

Le consumer pour le score regroupe et traite les donnees utiles pour le consumer kafka de calcul de score, puis les publie sur le topic kafka `<apt>.<room>.score_data`
Le consumer pour le user regroupe et traite les donnees supplementaires inutiles pour le consumer kafka de calcul de score, puis les publie sur le topic kafka `<apt>.<room>.extra_data`