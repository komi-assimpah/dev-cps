# Dev-CPS — Pipeline IoT (Polytech Sophia)

Projet universitaire Polytech Sophia: pipeline d’ingestion et d’analytique de données IoT pour un immeuble d’appartements. Le flux va des capteurs (simulés) vers MQTT, Kafka, calcul de scores, stockage TimescaleDB, et visualisation Grafana pour deux profils d’utilisateurs: gérant et locataire.

## Aperçu

- Génération réaliste de données capteurs par appartement/pièce (température, humidité, CO₂, PM2.5, CO, TVOC, présence, ouverture fenêtre, conso énergie)
- Ingestion en temps réel via MQTT (Mosquitto)
- Bridge MQTT → Kafka avec nettoyage (valeurs nulles, filtre médian/outliers)
- Consumer Kafka → TimescaleDB avec calculs d’indicateurs (IAQ_2H, IIT_2H)
- Visualisation des scores et séries via Grafana (datasource provisionnée)
- Kafka UI pour observer les topics/partitions

```
[Capteurs simulés]
	 └─ data-generator → MQTT (building/APT_xxx/<room>/sensors)
		│
		└─ mqtt-kafka-bridge → Kafka (APT_10x.<room>)
			│
			└─ kafka-bdd-bridge → TimescaleDB (scores)
			    │
			    └─ Grafana (dashboards)
```

## Démarrage rapide

Prérequis: Docker et Docker Compose.

1) Lancer l’ensemble des services

```bash
docker compose up -d
```

Cela démarre: Mosquitto, Kafka (KRaft), Kafka UI, TimescaleDB (avec init SQL), Grafana, mqtt-kafka-bridge, kafka-bdd-bridge, data-generator (mode temps réel par défaut).

2) Accès utiles

- Kafka UI: http://localhost:8080
- Grafana: http://localhost:3000 (admin/admin par défaut)
- PostgreSQL/TimescaleDB: localhost:5432

3) Vérifier les données

- Topics MQTT publiés: `building/APT_101/+/sensors` (et autres APT_xxx si configurés)
- Topics Kafka consommés: `APT_10x.<room>` (ex: `APT_101.salon` → côté bridge le nom final suit `APT_10{ID}`)
- Table Timescale `scores` alimentée périodiquement par le consumer Kafka

4) Interagir avec la base (via le conteneur TimescaleDB)

```bash
docker exec -it mon-timescale psql -U monuser -d sensor_scores
```

Dans `psql`:

```
\dt                  -- lister les tables
SELECT * FROM scores ORDER BY time DESC LIMIT 20;
```

## Composants

- data-generator/ — Génère des données synthétiques réalistes
	- Mode batch (CSV) et temps réel (MQTT)
	- Publie sur `building/{apartment_id}/{room}/sensors` et `building/weather`
	- Paramètres via variables d’env ou CLI: `MODE`, `INTERVAL`, `SPEED`, `APARTMENT`, `MQTT_BROKER`
- mqtt-kafka-bridge/ — Abonne aux topics MQTT et publie sur Kafka
	- Nettoyage: remplacement des `None`, filtre médian (`scipy.signal.medfilt`), seuils dynamiques
	- Mapping topics: MQTT `building/APT_101/+/sensors` → Kafka `APT_10{APT_ID}.{room}`
- kafka-bdd-bridge/ — Calcule les indicateurs et écrit en BDD
	- IAQ_2H (qualité d’air) et IIT_2H (isolation) calculés sur fenêtres glissantes
	- Insertion dans TimescaleDB(table `scores`) avec clé `(time, appart_id)`
- grafana/ — Provision des datasources et dashboards
	- Datasource Postgres/Timescale préconfigurée
	- Dashboards chargés depuis `grafana_json_exports/`
- kafka-ui — Interface d’observation Kafka (topics, partitions)
- timescaledb — Stockage séries temporelles + hypertable `scores`
- mosquitto — Broker MQTT

## Données & scores

- Capteurs: `temperature (°C)`, `humidity (%)`, `co2 (ppm)`, `pm25 (µg/m³)`, `co (ppm)`, `tvoc (µg/m³)`
- Nettoyage (bridge MQTT→Kafka):
	- Valeurs nulles remplacées par dernière valeur connue
	- Filtre médian (fenêtre 5) + seuil dynamique via MAD pour outliers
- Agrégation (consumer Kafka):
	- Moyennes par timestamp après 5 échantillons/variable
	- Calcul IAQ_2H: scores CO₂/CO/PM2.5/TVOC avec coefficients dépendants des niveaux
	- Calcul IIT_2H: `conso_elec / (temp_moyenne * surface)`

Schéma BDD (TimescaleDB)

- Table `appartement(id, etage, orientation, surface)`
- Table `scores(time timestamptz, appart_id int, IAQ_2H double, IIT_2H double)`
- `scores` est une hypertable partitionnée sur `time`

## Configuration & variables

Extraits de `docker-compose.yml`:

- Kafka (KRaft), ports: 9092 (host), 29092 (inter-containers)
- TimescaleDB: cred `monuser/monpassword`, DB `sensor_scores`
- Grafana: provision `grafana/datasources`, dashboards `grafana_json_exports`
- data-generator:
	- `MODE=realtime`, `INTERVAL=600`, `SPEED=600` (→ 10min simulées = 1s réelle)
	- `APARTMENT=""` pour tous, sinon ex: `APT_101`
- mqtt-kafka-bridge:
	- `MQTT_BROKER=mosquitto`, `KAFKA_BROKER=kafka:29092`
- kafka-bdd-bridge:
	- `KAFKA_BROKER=kafka:29092`, `DB_HOST=timescaledb`, `POSTGRES_*`

## Utilisation avancée

- Générateur en mode CSV

```bash
cd data-generator
python generate.py --days 7
python generate.py --apartment APT_101 --days 1
```

- Générateur en mode temps réel (local hors Docker)

```bash
cd data-generator
python generate.py --mode realtime --mqtt-broker localhost --mqtt-port 1883 --interval 600 --speed 600
```

- Bridge MQTT→Kafka (local)

```bash
cd mqtt-kafka-bridge
python3 consumer.py 1  # APT_101
```

- Consumer Kafka→BDD (local)

```bash
cd kafka-bdd-bridge
python3 consumer.py 1  # APT_101
```

- Kafka: lister/créer/supprimer topics (outil CLI)

```bash
python3 services/kafka-configuration/topicgen.py --list
python3 services/kafka-configuration/topicgen.py MyTopic --partitions 3 --replication 1
python3 services/kafka-configuration/topicgen.py --delete MyTopic
```

## Visualisation Grafana

- Datasource par défaut: TimescaleDB (proxy vers `timescaledb:5432`)
- Dashboards importés depuis `grafana_json_exports/`
- Exemple de requête (explorateur Grafana):

```sql
SELECT time, IAQ_2H, IIT_2H FROM scores WHERE appart_id = 1 ORDER BY time DESC LIMIT 200;
```

## Dépannage

- Kafka non prêt: attendre que le healthcheck passe, voir Kafka UI
- Aucun message consommé:
	- Vérifier que data-generator publie bien (logs du conteneur)
	- Vérifier les topics dans Kafka UI (`APT_10x.<room>`) et correspondance MQTT
- BDD vide:
	- Vérifier `kafka-bdd-bridge` logs et la connexion `timescaledb`
- Grafana sans données:
	- Vérifier la datasource (statut), puis lancer une requête simple

## Développement

- Dépendances Python par composant (`requirements.txt` dans chaque dossier)
- Lancement en local recommandé via venv; ou utiliser Docker Compose
- Logs: consulter `docker logs <service>` pour diagnostiquer

## Notes

- Projet académique, non destiné à la production (auto-création topics Kafka, creds en clair)
- Les seuils/nettoyages sont paramétrables dans `mqtt-kafka-bridge/utils` et `data-generator/generators`

***

Anciennes commandes utiles:

- Consommer un topic Kafka pour un appartement

```bash
python3 consumer.py APT_ID
# exemple pour APT_101
python3 consumer.py 1
```

- Interagir avec la BDD dans un terminal

```bash
docker exec -it mon-timescale psql -U monuser -d sensor_scores
```

Dans `psql`:

```
\dt
```

On peut exécuter n'importe quelle requête SQL (terminer par `;`).