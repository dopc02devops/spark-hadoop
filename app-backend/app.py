import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask import render_template

# ✅ Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
CORS(app)

# Store data in memory for demonstration (use a DB for production)
data_store = {
    'financial_data': [],
    'crypto_data': []
}

@app.route('/report')
def index():
    # Just render the page, no need to trigger update here as it's already scheduled
    return render_template('index.html', 
                           financial_data=data_store['financial_data'], 
                           crypto_data=data_store['crypto_data'])

@app.route('/api/financial', methods=['GET'])
def get_financial_data():
    return jsonify(data_store['financial_data'])

@app.route('/api/crypto', methods=['GET'])
def get_crypto_data():
    return jsonify(data_store['crypto_data'])

@app.route('/api/update', methods=['POST'])

def update_data():
    data = request.get_json()
    logging.info(f"Received data: {data}")

    # Check if the data is in the expected format
    if not data or 'topic' not in data or 'data' not in data:
        logging.error("Invalid data received. Expected 'topic' and 'data' fields.")
        return jsonify({'status': 'error', 'message': 'Invalid data received. Expected "topic" and "data" fields.'}), 400

    # Extract topic and data
    topic = data['topic']
    payload = data['data']
    
    # Process and store financial data
    if topic == 'financial':
        data_store['financial_data'].append(payload)
        logging.info(f"Updated financial_data: {data_store['financial_data']}")
    elif topic == 'crypto':
        data_store['crypto_data'].append(payload)
        logging.info(f"Updated crypto_data: {data_store['crypto_data']}")
    else:
        logging.warning(f"Unknown topic received: {topic}")

    return jsonify({'status': 'success'}), 200



if __name__ == '__main__':
    # ✅ Run Flask app with logging
    logging.info("Starting Flask API on port 6500...")
    app.run(host='0.0.0.0', port=6500, debug=True)
