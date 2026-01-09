FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app

USER app

ENV MQTT_BROKER=mosquitto
ENV MQTT_PORT=1883
ENV MODE=realtime
ENV INTERVAL=600
ENV SPEED=600

CMD ["python", "-u", "generate.py", "--mode", "realtime"]
