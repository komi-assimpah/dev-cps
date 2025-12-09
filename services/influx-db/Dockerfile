# InfluxDB sink consumer image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps for confluent-kafka (librdkafka)
RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka-dev \
    gcc g++ \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sink.py ./

# Default env (override in docker-compose)
ENV KAFKA_BOOTSTRAP="kafka:29092" \
    KAFKA_GROUP_ID="influx-sink" \
    TOPICS="TemperatureReadings,CO2,CO,COV,Humidity,PM25,Presence,Weather,Window" \
    INFLUX_URL="http://influxdb2:8086" \
    INFLUX_ORG="dev" \
    INFLUX_BUCKET="home" \
    INFLUX_TOKEN_FILE="/run/secrets/influxdb2-admin-token" \
    START_FROM_BEGINNING="true" \
    AUTO_COMMIT="false" \
    COMMIT_EACH_MESSAGE="false" \
    COMMIT_INTERVAL="1" \
    ALLOW_MISSING_TOPICS="true" \
    VERBOSE="false"

CMD ["python", "-u", "sink.py"]
