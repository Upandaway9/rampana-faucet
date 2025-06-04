from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS from all origins

@app.route('/')
def home():
    return 'Rampana Faucet is Live!'

@app.route('/claim', methods=['POST'])
def claim():
    data = request.get_json()
    wallet = data.get('wallet') if data else None

    if not wallet:
        return jsonify({"success": False, "message": "Wallet address is required."}), 400

    # Mock success response
    return jsonify({"success": True, "message": f"1,000 RAMP sent to {wallet}!"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
