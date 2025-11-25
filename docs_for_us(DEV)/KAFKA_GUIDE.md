# Guide Kafka pour débutants

## Qu'est-ce que Kafka ?

**Apache Kafka** est une plateforme de streaming distribuée qui permet de :
- **Publier** et **consommer** des flux de messages en temps réel
- **Stocker** ces messages de manière fiable et durable
- **Traiter** les flux de données au fil de l'eau

### Analogie simple : Kafka = Système postal numérique

Imaginez un bureau de poste ultra-rapide qui :
- Reçoit des lettres (messages) de différents expéditeurs (producteurs)
- Les classe dans des boîtes aux lettres nommées (topics)
- Permet à plusieurs personnes (consommateurs) de lire ces lettres
- Garde les lettres pendant un certain temps (rétention)

---

## Concepts clés de Kafka

### 1. **Topic** (Sujet)
Un "canal" ou "catégorie" de messages.

**Exemple :**
- Topic `commandes` : tous les messages de commandes e-commerce
- Topic `logs` : tous les logs applicatifs
- Topic `capteurs-temperature` : données IoT de capteurs

```
Topic: "commandes"
├── Message 1: {"id": 1, "produit": "Laptop", "prix": 899}
├── Message 2: {"id": 2, "produit": "Souris", "prix": 25}
└── Message 3: {"id": 3, "produit": "Clavier", "prix": 75}
```

### 2. **Producer** (Producteur)
Application qui **envoie** des messages dans un topic.

**Exemple en Python :**
```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Envoyer un message
producer.send('commandes', {'id': 1, 'produit': 'Laptop', 'prix': 899})
```

### 3. **Consumer** (Consommateur)
Application qui **lit** des messages depuis un topic.

**Exemple en Python :**
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'commandes',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Lire les messages
for message in consumer:
    print(f"Commande reçue: {message.value}")
```

### 4. **Partition**
Un topic est divisé en **partitions** pour paralléliser le traitement.

```
Topic "commandes" avec 3 partitions :

Partition 0: [msg1, msg4, msg7, ...]
Partition 1: [msg2, msg5, msg8, ...]
Partition 2: [msg3, msg6, msg9, ...]
```

**Avantages :**
- Plusieurs consommateurs peuvent lire en parallèle
- Meilleure performance et scalabilité

### 5. **Broker**
Le serveur Kafka qui stocke et distribue les messages.

Dans notre configuration, vous avez **1 broker** (pour développement).
En production, on utilise plusieurs brokers (3 ou 5) pour la redondance.

### 6. **Consumer Group**
Groupe de consommateurs qui se partagent les partitions d'un topic.

```
Topic avec 3 partitions :

Consumer Group "traitement-commandes" :
├── Consumer 1 → lit Partition 0
├── Consumer 2 → lit Partition 1
└── Consumer 3 → lit Partition 2
```

**Avantages :**
- Charge répartie entre plusieurs consommateurs
- Si un consommateur tombe, les autres continuent

---

## Architecture de votre environnement

```
┌─────────────────────────────────────────────────────────────┐
│                    Votre Machine (localhost)                │
│                                                             │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐     │
│  │  MongoDB   │      │   Kafka    │      │ Kafka-UI   │     │
│  │  :27017    │      │   :9092    │      │  :8080     │     │
│  └────────────┘      └─────┬──────┘      └─────┬──────┘     │
│                             │                    │          │
│                             │  kafka:29092       │          │
│                             └────────────────────┘          │
│                        (réseau Docker interne)              │
└─────────────────────────────────────────────────────────────┘

Votre code Python/Java/etc.
      │
      │ localhost:9092
      ▼
   Kafka Broker
```

### Ports à retenir

| Service | Port | Usage |
|---------|------|-------|
| **Kafka** | 9092 | Se connecter depuis votre machine |
| **Kafka** | 9093 | Controller KRaft (interne) |
| **Kafka-UI** | 8080 | Interface web (http://localhost:8080) |
| **MongoDB** | 27017 | Base de données |

---

## Mode KRaft vs Zookeeper

Votre configuration utilise **KRaft** (architecture moderne).

### Ancienne architecture (Zookeeper)
```
┌─────────────┐
│  Zookeeper  │ ← Gère les métadonnées
└──────┬──────┘
       │
┌──────▼──────┐
│    Kafka    │ ← Stocke les messages
└─────────────┘
```

### Nouvelle architecture (KRaft) - Votre config
```
┌─────────────────────┐
│  Kafka avec KRaft   │ ← Tout en un !
│  (métadonnées +     │
│   messages)         │
└─────────────────────┘
```

**Avantages de KRaft :**
- Plus simple (1 service au lieu de 2)
- Plus rapide au démarrage
- Architecture du futur (Zookeeper sera supprimé dans Kafka 4.0)

---

## Démarrage rapide

### 1. Lancer l'environnement
```bash
# Démarrer tous les services
docker compose up -d

# Vérifier que tout tourne
docker compose ps

# Voir les logs de Kafka
docker compose logs -f kafka
```

### 2. Accéder à l'interface web
Ouvrez votre navigateur : **http://localhost:8080**

Vous verrez :
- Le cluster "local"
- Les topics existants
- Les brokers actifs

### 3. Créer votre premier topic

**Option A : Via l'interface web**
1. Allez sur http://localhost:8080
2. Cliquez sur "Topics" → "Add a Topic"
3. Nom : `test-topic`, Partitions : 3

**Option B : Via la ligne de commande**
```bash
docker exec -it kafka_broker bash

kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --partitions 3 \
  --replication-factor 1
```

### 4. Envoyer des messages

**Via la ligne de commande :**
```bash
docker exec -it kafka_broker bash

kafka-console-producer --bootstrap-server localhost:9092 --topic test-topic
# Tapez vos messages, un par ligne
> Hello Kafka
> Mon premier message
> Ctrl+C pour quitter
```

### 5. Lire les messages

**Via la ligne de commande :**
```bash
docker exec -it kafka_broker bash

kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --from-beginning
```

**Via l'interface web :**
1. Allez sur http://localhost:8080
2. Cliquez sur votre topic
3. Onglet "Messages"

---

## Exemples de code

### Python (avec kafka-python)

**Installation :**
```bash
pip install kafka-python
```

**Producteur :**
```python
from kafka import KafkaProducer
import json
import time

# Créer un producteur
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Envoyer des messages
for i in range(10):
    data = {
        'id': i,
        'temperature': 20 + i,
        'timestamp': time.time()
    }
    producer.send('capteurs-temperature', value=data)
    print(f"Message envoyé : {data}")
    time.sleep(1)

producer.flush()
producer.close()
```

**Consommateur :**
```python
from kafka import KafkaConsumer
import json

# Créer un consommateur
consumer = KafkaConsumer(
    'capteurs-temperature',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # Lire depuis le début
    group_id='mon-groupe',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Lire les messages
print("En attente de messages...")
for message in consumer:
    print(f"Reçu : {message.value}")
    print(f"  Partition : {message.partition}")
    print(f"  Offset : {message.offset}")
```

### JavaScript (avec kafkajs)

**Installation :**
```bash
npm install kafkajs
```

**Producteur :**
```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'mon-app',
  brokers: ['localhost:9092']
});

const producer = kafka.producer();

async function run() {
  await producer.connect();

  await producer.send({
    topic: 'test-topic',
    messages: [
      { value: 'Hello Kafka from Node.js!' }
    ]
  });

  await producer.disconnect();
}

run();
```

**Consommateur :**
```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'mon-app',
  brokers: ['localhost:9092']
});

const consumer = kafka.consumer({ groupId: 'mon-groupe' });

async function run() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'test-topic', fromBeginning: true });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      console.log({
        value: message.value.toString(),
        partition,
        offset: message.offset
      });
    }
  });
}

run();
```

---

## Commandes utiles

### Gestion des topics

```bash
# Entrer dans le conteneur Kafka
docker exec -it kafka_broker bash

# Lister tous les topics
kafka-topics --list --bootstrap-server localhost:9092

# Créer un topic
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic mon-topic \
  --partitions 3 \
  --replication-factor 1

# Décrire un topic (voir ses partitions, etc.)
kafka-topics --describe --bootstrap-server localhost:9092 --topic mon-topic

# Supprimer un topic
kafka-topics --delete --bootstrap-server localhost:9092 --topic mon-topic
```

### Gestion des messages

```bash
# Produire des messages (console interactive)
kafka-console-producer --bootstrap-server localhost:9092 --topic mon-topic

# Consommer depuis le début
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic mon-topic \
  --from-beginning

# Consommer avec affichage de la clé et des métadonnées
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic mon-topic \
  --from-beginning \
  --property print.key=true \
  --property print.partition=true \
  --property print.offset=true
```

### Gestion des consumer groups

```bash
# Lister les groupes de consommateurs
kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Voir les détails d'un groupe
kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group mon-groupe \
  --describe

# Réinitialiser les offsets (relire depuis le début)
kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group mon-groupe \
  --topic mon-topic \
  --reset-offsets --to-earliest \
  --execute
```

---

## Configuration expliquée

### Variables importantes du docker-compose

| Variable | Valeur | Explication |
|----------|--------|-------------|
| `KAFKA_NODE_ID` | 1 | Identifiant unique du broker |
| `KAFKA_PROCESS_ROLES` | broker,controller | Double rôle (stockage + coordination) |
| `KAFKA_AUTO_CREATE_TOPICS_ENABLE` | true | Crée automatiquement les topics |
| `KAFKA_LOG_RETENTION_HOURS` | 168 | Messages gardés 7 jours |
| `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR` | 1 | Pas de réplication (1 seul broker) |
| `CLUSTER_ID` | MkU3... | ID unique du cluster (NE PAS CHANGER) |

### Connexion depuis votre code

**Depuis votre machine (Python, Java, Node.js, etc.) :**
```
bootstrap_servers = 'localhost:9092'
```

**Depuis un autre conteneur Docker :**
```
bootstrap_servers = 'kafka:29092'
```

---

## Cas d'usage courants

### 1. Messaging entre microservices
```
Service A → [Topic: commandes] → Service B
                                → Service C (notifications)
                                → Service D (facturation)
```

### 2. Collecte de logs
```
Application 1 → [Topic: logs] → ELK Stack
Application 2 ↗                 (Elasticsearch)
Application 3 ↗
```

### 3. Event Sourcing
```
Actions utilisateur → [Topic: events] → Base de données
                                      → Analytics
                                      → Audit log
```

### 4. IoT et capteurs
```
Capteur 1 → [Topic: temperature] → Traitement temps réel
Capteur 2 ↗                       → Stockage MongoDB
Capteur 3 ↗                       → Alertes
```

---

## Bonnes pratiques

### Nommage des topics
- ✅ `commandes-creees`, `logs-application`, `capteurs-temperature`
- ❌ `topic1`, `test`, `data`

### Partitionnement
- 1 partition = 1 consommateur max
- 3-5 partitions pour débuter
- Ajuster selon le volume

### Consumer groups
- Utilisez toujours un `group_id` pour vos consommateurs
- Même group_id = charge partagée
- Group_id différents = tous reçoivent tous les messages

### Gestion des erreurs
```python
# Toujours gérer les exceptions
try:
    producer.send('topic', value=data).get(timeout=10)
except Exception as e:
    print(f"Erreur : {e}")
    # Logger, réessayer, etc.
```

---

## Dépannage

### Kafka ne démarre pas
```bash
# Voir les logs détaillés
docker compose logs kafka

# Vérifier le healthcheck
docker compose ps
```

### Cannot connect to localhost:9092
```bash
# Vérifier que Kafka est bien démarré
docker compose ps

# Vérifier les ports
netstat -an | grep 9092

# Attendre que Kafka soit vraiment prêt (40s au démarrage)
docker compose logs -f kafka | grep "started"
```

### Topic not found
```bash
# Si AUTO_CREATE_TOPICS_ENABLE=true, le topic se crée automatiquement
# Sinon, créez-le manuellement :
kafka-topics --create --bootstrap-server localhost:9092 --topic mon-topic --partitions 3 --replication-factor 1
```

### Réinitialiser complètement
```bash
# Arrêter et supprimer TOUTES les données
docker compose down -v

# Redémarrer
docker compose up -d
```

---

## Aller plus loin

### Documentation officielle
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Documentation](https://docs.confluent.io/)

### Bibliothèques clientes
- **Python** : kafka-python, confluent-kafka-python
- **Java** : kafka-clients (officiel)
- **Node.js** : kafkajs
- **Go** : confluent-kafka-go
- **.NET** : Confluent.Kafka

### Concepts avancés à explorer
- Kafka Streams (traitement de flux)
- Kafka Connect (connecteurs vers bases de données)
- Schema Registry (gestion des schémas Avro/JSON)
- Transactions et exactly-once semantics
- Sécurité (SSL/TLS, SASL, ACLs)

---

## Support et ressources

### Commandes Docker Compose

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Voir les logs
docker compose logs -f [service]

# Redémarrer un service
docker compose restart [service]

# Supprimer les données
docker compose down -v
```

### Kafka-UI
Interface web : **http://localhost:8080**
- Dashboard avec métriques
- Gestion des topics
- Visualisation des messages
- Monitoring des consommateurs

### Kafka CLI (ligne de commande)
```bash
# Entrer dans le conteneur
docker exec -it kafka_broker bash

# Toutes les commandes kafka-* sont disponibles
kafka-topics --help
kafka-console-producer --help
kafka-console-consumer --help
```

---

## Questions fréquentes

**Q : Quelle différence entre Kafka et RabbitMQ ?**
- Kafka = streaming de haute performance, persistance, replay
- RabbitMQ = messagerie traditionnelle, accusés de réception, routing complexe

**Q : Kafka garde les messages combien de temps ?**
- Dans cette config : 7 jours (168h)
- Configurable avec `KAFKA_LOG_RETENTION_HOURS`

**Q : Combien de consommateurs par partition ?**
- 1 partition = 1 consommateur par consumer group
- Mais plusieurs groups peuvent lire la même partition

**Q : Kafka c'est rapide ?**
- Oui ! Peut gérer des millions de messages/seconde
- Latence < 10ms en général

**Q : Puis-je relire les anciens messages ?**
- Oui ! C'est la force de Kafka
- Les messages persistent pendant la durée de rétention

---

**Bonne découverte de Kafka !** 🚀

Si vous avez des questions, consultez la documentation officielle ou explorez l'interface web à http://localhost:8080
