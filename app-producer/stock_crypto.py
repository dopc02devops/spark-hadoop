import logging
import requests
import datetime
import time
import json
import yfinance as yf
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)

# Alpha Vantage API Setup
ALPHA_VANTAGE_API_KEY = "ZUYRTNZ158SCBS2S"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# CoinGecko API Setup
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# Kafka Configuration
KAFKA_BROKER = "kafka-broker:29092"
FINANCIAL_TOPIC = "financial_data"
CRYPTO_TOPIC = "crypto_data"

# Kafka Producer Setup with Serialization Fix
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    acks='all',
    retries=3,
    retry_backoff_ms=500,
    linger_ms=100,
    batch_size=100,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),  # ✅ JSON Serializer
    key_serializer=lambda k: k.encode('utf-8') if k else None   # ✅ Key Serializer
)

# Kafka Admin Client
admin_client = KafkaAdminClient(bootstrap_servers=[KAFKA_BROKER])

def create_topic_if_not_exists(topic_name):
    """Create a Kafka topic if it doesn't exist."""
    topic_list = admin_client.list_topics()
    if topic_name not in topic_list:
        logging.info(f"Creating topic: {topic_name}")
        new_topic = NewTopic(topic_name, num_partitions=3, replication_factor=1)  # ✅ FIXED
        try:
            admin_client.create_topics([new_topic])
        except TopicAlreadyExistsError:
            logging.info(f"Topic {topic_name} already exists.")
    else:
        logging.info(f"Topic {topic_name} exists.")

def fetch_stock_data(symbols=["AAPL", "GOOGL", "MSFT"]):
    """Fetch real-time stock data from Yahoo Finance with fallback to Alpha Vantage"""
    stock_data_list = []
    
    try:
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if not data.empty:
                stock_data_list.append({
                    "symbol": symbol,
                    "price": data["Close"].iloc[-1],  
                    "volume": data["Volume"].iloc[-1],
                    "high_price": data["High"].iloc[-1],
                    "percentage_change": ((data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2]) * 100 if len(data) > 1 else None,
                    "time_now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
        if stock_data_list:
            logging.info("Fetched stock data from Yahoo Finance.")
            return stock_data_list
    except Exception as e:
        logging.error(f"Error fetching data from Yahoo Finance: {e}")
        logging.info("Falling back to Alpha Vantage.")

    for symbol in symbols:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        try:
            response = requests.get(ALPHA_VANTAGE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from Alpha Vantage: {e}")
            continue  
        
        logging.info(f"Raw response from Alpha Vantage for {symbol}: {data}")

        data = data.get("Global Quote", {})
        if data:
            price = data.get("05. price")
            previous_close = data.get("08. previous close")
            percentage_change = ((float(price) - float(previous_close)) / float(previous_close)) * 100 if price and previous_close else None
            stock_data_list.append({
                "symbol": data.get("01. symbol"),
                "price": price,
                "volume": data.get("06. volume"),
                "high_price": data.get("03. high"),
                "percentage_change": percentage_change,
                "time_now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    return stock_data_list

def fetch_crypto_data(cryptos=["bitcoin", "ethereum", "dogecoin"], currency="usd"):
    """Fetch real-time cryptocurrency price from CoinGecko"""
    params = {"ids": ",".join(cryptos), "vs_currencies": currency, "include_market_cap": "true", "include_24hr_change": "true"}
    try:
        response = requests.get(COINGECKO_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching crypto data from CoinGecko: {e}")
        return []  
    
    crypto_data_list = []
    for crypto in cryptos:
        if crypto in data:
            crypto_data_list.append({
                "symbol": crypto,
                "price": data[crypto].get(currency),
                "market_cap": data[crypto].get(f"{currency}_market_cap"),
                "24h_change": data[crypto].get(f"{currency}_24h_change"),
                "volume": "N/A",  
                "time_now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    return crypto_data_list

def send_to_kafka(data, topic):
    """Send JSON data to Kafka."""
    for entry in data:
        try:
            entry = {key: (value.item() if isinstance(value, (np.generic, np.ndarray)) else value) for key, value in entry.items()}
            producer.send(topic, value=entry, key=entry['symbol'])  # ✅ FIXED: No manual encoding
            logging.info(f"Sent to {topic}: {entry}")
        except Exception as e:
            logging.error(f"Error sending to {topic}: {e}")

    producer.flush()  # ✅ Ensure all messages are sent

def delivery_report(err, msg):
    """Delivery report callback to check if message is successfully delivered"""
    if err is not None:
        logging.error(f"Message delivery failed: {err}")
    else:
        logging.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def main():
    create_topic_if_not_exists(FINANCIAL_TOPIC)
    create_topic_if_not_exists(CRYPTO_TOPIC)

    print("🚀 Starting streaming...")

    while True:
        stock_data = fetch_stock_data()
        crypto_data = fetch_crypto_data()

        if stock_data:
            logging.info("Sending Stock Data to Kafka.")
            send_to_kafka(stock_data, FINANCIAL_TOPIC)

        if crypto_data:
            logging.info("Sending Crypto Data to Kafka.")
            send_to_kafka(crypto_data, CRYPTO_TOPIC)

        print("Waiting for next cycle...")
        time.sleep(150)

if __name__ == "__main__":
    main()
