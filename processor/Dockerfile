FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Kafka compression codecs
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "-u", "main.py"]