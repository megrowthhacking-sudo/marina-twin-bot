FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# База знаний и sqlite-хранилище должны переживать рестарт контейнера.
# ВАЖНО: не используем Docker-инструкцию VOLUME — Railway её не поддерживает
# ("dockerfile invalid: docker VOLUME ... is not supported, use Railway Volumes").
# Постоянное хранилище подключается отдельно через Railway Volumes (в панели
# Railway: Volume -> mount path /app/data) или через docker run -v для VPS.

CMD ["python", "bot.py"]
