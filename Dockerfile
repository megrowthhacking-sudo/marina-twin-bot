FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# База знаний и sqlite-хранилище должны переживать рестарт контейнера —
# смонтируй /app/data как volume при желании сохранять историю между деплоями.


CMD ["python", "bot.py"]
