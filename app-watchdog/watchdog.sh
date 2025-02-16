#!/bin/bash

# Target container to restart if Kafka goes down
TARGET_CONTAINER="consumer-app"
KAFKA_CONTAINER="kafka-broker"

echo "🚀 Watchdog started. Monitoring $KAFKA_CONTAINER..."

while true; do
    # Check if Kafka is running
    if ! docker ps | grep -q "$KAFKA_CONTAINER"; then
        echo "⚠️ $KAFKA_CONTAINER is down or restarting! Restarting $TARGET_CONTAINER..."
        
        # Restart the consumer container
        docker restart $TARGET_CONTAINER
        
        echo "✅ Restarted $TARGET_CONTAINER at $(date)"
    else
        echo "✅ $KAFKA_CONTAINER is running. No action needed."
    fi
    
    sleep 10  # Adjust this if needed (check every 10 seconds)
done
