FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN touch bot.log materials.db && \
    chmod 644 bot.log materials.db

CMD ["python", "main.py"]