# HIVEQL

This project demonstrates the process of consuming financial and crypto data from Kafka streams, sending it to a backend API, and saving it to HDFS using Spark Streaming.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Setup](#docker-setup)
- [Python Virtual Environment Setup](#python-virtual-environment-setup)
- [Run the Application](#run-the-application)
- [Frontend Setup](#frontend-setup)
- [Testing the Application](#testing-the-application)
- [Backend API Information](#backend-api-information)

## Prerequisites

- Docker and Docker Compose installed on your system.
- Python 3.9 or higher installed.
- A working Kafka setup.
- HDFS for storage.


1. **Create a Virtual Environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   .\venv\Scripts\activate
2. **Start application:**

```sh
docker-compose up --build -d
docker-compose ps


This file contains all necessary steps to:

1. Set up the environment (Docker, Python, Virtualenv).
2. Run both the backend and frontend services.
3. Provides troubleshooting advice for common issues.
   
Make sure that all the services (Kafka, HDFS, and the backend Flask app) are running properly and your endpoints are accessible for a smooth experience!
