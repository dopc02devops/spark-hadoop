import os
import logging
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, FloatType
from kafka.errors import KafkaTimeoutError, KafkaError  # Handle both KafkaTimeoutError and KafkaError
from kafka import KafkaAdminClient
import requests

# Configuration Constants
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka-broker:29092")  # Default to 'kafka-broker:29092' if not set in environment
FINANCIAL_TOPIC = os.getenv("FINANCIAL_TOPIC", "financial_data")
CRYPTO_TOPIC = os.getenv("CRYPTO_TOPIC", "crypto_data")

# User or Environment Specific Paths
HDFS_URI = os.getenv("HDFS_URI", "hdfs://namenode:9000")
USER_PATH = os.getenv("USER_PATH", "/user/spark")
CHECKPOINT_PATH = os.getenv("CHECKPOINT_PATH", "/user/spark/checkpoints")

# Ensure JAVA_HOME is set (if not set, you might want to do it dynamically)
os.environ["JAVA_HOME"] = "/usr"

# Define the backend API endpoint
BACKEND_API_URL = "http://backend:6500/api/update"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaSparkConsumer")

# Define schema for financial data
financial_schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", FloatType()) \
    .add("volume", FloatType()) \
    .add("high_price", FloatType()) \
    .add("percentage_change", FloatType()) \
    .add("time_now", StringType())

# Define schema for crypto data (Updated to use 'coin' instead of 'symbol')
crypto_schema = StructType() \
    .add("coin", StringType()) \
    .add("price", FloatType()) \
    .add("market_cap", FloatType()) \
    .add("24h_change", FloatType()) \
    .add("volume", FloatType()) \
    .add("time_now", StringType())

# Start Spark Session
spark = SparkSession.builder \
    .appName("KafkaSparkConsumer") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2") \
    .config("spark.sql.adaptive.enabled", "false") \
    .master("local[*]") \
    .getOrCreate()

logger.info(f"🚀 Spark session started successfully ✅")

# Retry mechanism for reading Kafka stream
def read_kafka_stream_with_retry(topic, schema, max_retries=5, retry_interval=5):
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"📡 Subscribing to Kafka topic: {topic}, Attempt {attempt + 1}")
            return spark.readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", KAFKA_BROKER) \
                .option("subscribe", topic) \
                .option("startingOffsets", "earliest") \
                .load() \
                .selectExpr("CAST(value AS STRING)") \
                .select(from_json(col("value"), schema).alias("data")) \
                .select("data.*")
        except KafkaTimeoutError as e:
            attempt += 1
            logger.error(f"❌ KafkaTimeoutError: Attempt {attempt} failed while reading from {topic}. Error: {e}")
            if attempt < max_retries:
                logger.info(f"⏳ Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Max retry attempts reached for {topic}. Giving up.")
                raise
        except KafkaError as e:
            logger.error(f"❌ KafkaError: Error reading from {topic}. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error reading from Kafka topic {topic}: {e}")
            raise

# Check if Kafka topic exists before subscribing
def check_topic_exists(broker, topic):
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=broker)
        topics = admin_client.list_topics()
        return topic in topics
    except KafkaError as e:
        logger.error(f"❌ Error checking Kafka topic {topic}: {e}")
        return False

# Read data from Kafka topics with retry
if check_topic_exists(KAFKA_BROKER, FINANCIAL_TOPIC):
    financial_data = read_kafka_stream_with_retry(FINANCIAL_TOPIC, financial_schema)
else:
    logger.error(f"❌ Kafka topic {FINANCIAL_TOPIC} does not exist")
    exit(1)

if check_topic_exists(KAFKA_BROKER, CRYPTO_TOPIC):
    crypto_data = read_kafka_stream_with_retry(CRYPTO_TOPIC, crypto_schema)
else:
    logger.error(f"❌ Kafka topic {CRYPTO_TOPIC} does not exist")
    exit(1)

# Function to send data to the backend API
def send_to_backend(data):
    payload = {
        "topic": data["topic"],
        "data": data  # Wrap data inside "data" key
    }
    try:
        response = requests.post(BACKEND_API_URL, json=payload)
        logger.info(f"🔄 Sending {data['topic']} data to backend: {payload}")
        logger.info(f"🔍 Backend Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logger.info("✅ Data successfully sent to backend")
        else:
            logger.error(f"❌ Error sending data to backend: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Failed to send data to backend: {e}")

# Function to process and send each batch of streaming data to backend
def process_batch(batch_df, batch_id):
    logger.info(f"📦 Processing batch {batch_id} with {batch_df.count()} records")
    batch_df.show(truncate=False)  # Show batch data

    def process_row(row):
        # Log the row to help debug the issue
        logger.info(f"Processing row: {row}")
        
        # Check if the row is financial or crypto based on the field present
        if 'symbol' in row:  # Check for financial data
            topic = 'financial'
            data = {
                'symbol': row['symbol'],
                'price': row['price'],
                'volume': row['volume'],
                'time_now': row['time_now'],
                'topic': topic
            }
        elif 'coin' in row:  # Check for crypto data
            topic = 'crypto'
            data = {
                'coin': row['coin'],
                'price': row['price'],
                'volume': row['volume'],
                'time_now': row['time_now'],
                'topic': topic
            }
        else:
            logger.error(f"Unknown data type for row: {row}")
            return  # Skip row if neither 'symbol' nor 'coin' is found

        # Send the processed data to the backend
        send_to_backend(data)

    # Process each row in the batch
    batch_df.foreach(process_row)


# Output to Parquet in HDFS format
def write_to_parquet(df, name):
    try:
        logger.info(f"📝 Starting streaming query for {name} to Parquet")
        return df.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("checkpointLocation", f"{HDFS_URI}{CHECKPOINT_PATH}/{name}") \
            .option("path", f"{HDFS_URI}{USER_PATH}/{name}") \
            .start()
    except Exception as e:
        logger.error(f"❌ Error starting streaming query for {name}: {e}")
        raise

# Send data to backend before writing to HDFS
financial_data.writeStream.foreachBatch(process_batch).start()
crypto_data.writeStream.foreachBatch(process_batch).start()

# Write financial data and crypto data to Parquet in HDFS
financial_query = write_to_parquet(financial_data, "financial_data")
crypto_query = write_to_parquet(crypto_data, "crypto_data")

# Await termination
try:
    financial_query.awaitTermination()
    crypto_query.awaitTermination()
except KeyboardInterrupt:
    logger.info(f"⏹️ Streaming queries interrupted ❌")
finally:
    spark.stop()
    logger.info(f"🚀 Spark session stopped ✅")
