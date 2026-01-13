# TODO:Je crois le fichier est un peu flopesque faut que je modifie
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir confluent-kafka pymongo


COPY . .

ENV PYTHONPATH=/app

COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]