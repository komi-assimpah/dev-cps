FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    librdkafka-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

COPY start_kafka_bdd_bridge.sh .
RUN chmod +x start_kafka_bdd_bridge.sh

CMD ["./start_kafka_bdd_bridge.sh"]
