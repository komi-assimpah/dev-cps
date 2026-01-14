# PROOF OF CONCEPT - PROJET DEV-CPS

AUTHORS : KOMI ASSIMPAH Jean-Paul - FLANDIN François - MALMASSARY Louis

## 1. Avant-propos

L'objectif de ce POC est de montrer que les pipelines :
- de l'appartement au service utilisateur (modele ia et stockage local) 
- de l'appartement au service client (calcul de scores et monitoring) 

Fonctionnent pour un appartement et pourraient être déployés pour d'autres appartements d'un même immeuble.

## 2. Comment utiliser ce POC

Tout d'abord, il faudra installer `docker` et `docker compose`

Ensuite, le système entier peut etre demarré et utilisé avec une simple commande
```bash
docker compose up -d
```

Le premier demarrage devrait prendre un peu de temps


### 2.1 Endpoints

mais fini par exposer plusieurs endpoints, utiles pour comprendre ce qu'il se passe :

[localhost:8081](http://localhost:8081/) - MongoDB
Permet de voir le contenu des collections MongoDB, la collection qui nous interesse ici est : `iot_building/sensor_apt_101`
- il faudra entrer des credentials
  - username : admin
  - password : pass

[localhost:3000](http://localhost:3000/) - Grafana
Permet d'acceder a grafana, le monitoring client, qui permet d'observer l'evolution des scores de qualité de l'air et d'isolation thermique
- pour entrer dans grafana :
  - username : admin
  - password : admin
- pour ajouter la base de donnees `timescaleDB` au dahsboard
  - aller dans `connections > datasources > TimescaleDB`
    - dans `Authentication > password` et entrer `monpassword`
    - cliquer sur Save & test
      - Si le cadre devient vert, tout est bon
      - Sinon recliquer sur Save & test

[localhost:8080](http://localhost:8080/) - KafkaUI
Permet d'acceder aux topics Kafka et leurs contenus

### 2.2 Intéragir avec la Base de Données TimescaleDB

```bash
docker exec -it mon-timescale psql -U monuser -d sensor_scores
```

Afficher les tables
```bash
\dt
```

Afficher le contenu de la table `scores`
```sql
SELECT * FROM scores;
```

## 3. Architecture

![Schéma de l'architecture de ce POC](architecture.png)

### 3.1 Explication des composants

#### Data Generator

Génération réaliste de données capteurs par appartement/pièce (température, humidité, CO₂, PM2.5, CO, TVOC, présence, ouverture fenêtre, conso énergie)

Envoie les donnees dans deux topics : `building/{apt}/{room}/sensors`

#### Cleaners (pour scores & pour user)

Recoivent les donnees du topic `building/{apt}/{room}/sensors`, et nettoient les données avec ce pipeline :
- Nettoyage des valeurs nulles (répète la donnée précédente)
- Vérifie que la donnée est bien comprise dans l'intervale de mesure du capteur (répète la donnée précédente)
- Applique ensuite un filtre médian pour filtrer les outliers

Le consumer pour le score regroupe et traite les donnees utiles pour le consumer kafka de calcul de score, puis les publie sur le topic kafka `<apt>.<room>.score_data`
Le consumer pour le user regroupe et traite les donnees supplementaires inutiles pour le consumer kafka de calcul de score, puis les publie sur le topic kafka `<apt>.<room>.extra_data`