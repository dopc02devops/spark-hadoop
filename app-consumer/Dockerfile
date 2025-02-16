# Use Ubuntu 20.04 as the base image
FROM ubuntu:20.04

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install required system dependencies (Java 11, wget, and other required tools)
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    software-properties-common \
    wget \
    curl \
    libsnappy1v5 \
    libzstd1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Manually add Python 3.8 repository and install Python
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.9 python3.9-distutils python3.9-venv && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3.9 get-pip.py && \
    rm get-pip.py && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for Java and Python
ENV JAVA_HOME=/usr
ENV PATH=$JAVA_HOME/bin:$PATH
ENV PATH="/usr/bin/python3.9:$PATH"
ENV PYTHONPATH="/usr/bin/python3.9"
ENV PYSPARK_PYTHON=python3.9
ENV PYSPARK_DRIVER_PYTHON=python3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies with increased timeout & retries
RUN python3.9 -m pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt \
    && rm -rf /root/.cache/pip  # Remove pip cache after installing

# Create a directory for Spark and download required Kafka JAR
RUN mkdir -p /opt/spark/jars && \
    wget -P /opt/spark/jars https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10_2.11/2.4.6/spark-streaming-kafka-0-10_2.11-2.4.6.jar \
    && rm -rf /var/lib/apt/lists/*  # Remove any apt lists that may be cached

# Copy the Python script
COPY spark_consumer.py .

# Make the script executable
RUN chmod +x spark_consumer.py

# Set Python 3.8 as the default python version
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

# Run the consumer script
CMD ["python", "spark_consumer.py"]
