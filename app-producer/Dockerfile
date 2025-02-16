# Use Python 3.9 as the base image
FROM python:3.9

# Install cron and other dependencies
RUN apt-get update && apt-get install -y cron && apt-get clean

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script and cron job
COPY stock_crypto.py .

# Make the Python script executable
RUN chmod +x stock_crypto.py

CMD ["python", "stock_crypto.py"]
