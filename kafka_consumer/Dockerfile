FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir confluent-kafka pymongo

COPY mongoDB-consumer.py .

CMD ["python", "mongoDB-consumer.py"]
