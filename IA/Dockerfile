FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY heating_service.py .
COPY heating_predictor.py .
COPY geolocation_service.py .
COPY heating_model.json .

CMD ["python", "heating_service.py", "--kafka"]
