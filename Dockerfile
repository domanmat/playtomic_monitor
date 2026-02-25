FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py scanner.py db.py filters.py alerts.py monitor.py ./
COPY filters.sql ./

ENV DB_PATH=/app/data/playtomic.db

CMD ["python", "-u", "monitor.py"]
