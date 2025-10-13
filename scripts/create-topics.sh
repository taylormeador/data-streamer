#!/bin/bash

echo "Creating Kafka topics..."

docker exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --topic iot-sensor-data

docker exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --topic iot-sensor-data-validated

echo "Topics created!"
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092