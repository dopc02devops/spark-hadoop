import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# ✅ Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
CORS(app)

# Store data in memory for demonstration (use a DB for production)
data_store = {
    'financial_data': [],
    'crypto_data': []
}

@app.route('/api/financial', methods=['GET'])
def get_financial_data():
    return jsonify(data_store['financial_data'])

@app.route('/api/crypto', methods=['GET'])
def get_crypto_data():
    return jsonify(data_store['crypto_data'])

@app.route('/api/update', methods=['POST'])
def update_data():
    data = request.get_json()
    logging.info(f"Received : {data['topic']} data")

    if not data:
        logging.error("Invalid request: JSON expected")
        return jsonify({'error': 'Invalid request, JSON expected'}), 400

    if 'topic' not in data:
        logging.error("Missing required field: 'topic'")
        return jsonify({'error': "Missing required field: 'topic'"}), 400

    if 'data' not in data:
        logging.error("Missing required field: 'data'")
        return jsonify({'error': "Missing required field: 'data'"}), 400

    if data['topic'] == 'financial':
        data_store['financial_data'].append(data['data'])
        logging.info(f"Updated financial_data: {data_store['financial_data']}")
        print(f"Updated financial_data: {data_store['financial_data']}")
    elif data['topic'] == 'crypto':
        data_store['crypto_data'].append(data['data'])
        logging.info(f"Updated crypto_data: {data_store['crypto_data']}")
        print(f"Updated crypto_data: {data_store['crypto_data']}")
    else:
        logging.error("Invalid 'topic' value, must be 'financial' or 'crypto'")
        return jsonify({'error': "Invalid 'topic' value, must be 'financial' or 'crypto'"}), 400

    return jsonify({'status': 'success', 'received_data': data['topic']}), 200

if __name__ == '__main__':
    # ✅ Run Flask app with logging
    logging.info("Starting Flask API on port 6500...")
    app.run(host='0.0.0.0', port=6500, debug=True)
