FROM ubuntu:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    docker.io curl jq && \
    apt-get clean

# Set working directory
WORKDIR /app
COPY . .
# Ensure script has execution permission
RUN chmod +x /app/watchdog.sh
