# Je crois le fichier est un peu flopesque faut que je modifie
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

COPY start_kafka_bdd_bridge.sh .
RUN chmod +x start_kafka_bdd_bridge.sh

CMD ["./start_kafka_bdd_bridge.sh"]

# CMD ["python", "consumer_to_score_computation.py", "1"]
# CMD ["python", "consumer_to_user_storage.py", "1"]