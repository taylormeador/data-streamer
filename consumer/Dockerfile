FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for confluent-kafka
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/

COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer/*.py .

# Use -u for unbuffered output so logs show up immediately
CMD ["python", "-u", "main.py"]
