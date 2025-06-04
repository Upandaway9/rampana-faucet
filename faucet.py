from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Rampana Faucet is Live!'

@app.route('/claim', methods=['POST'])
def claim():
    data = request.get_json()
    wallet = data.get('wallet') if data else None

    if not wallet:
        return jsonify({"success": False, "message": "Wallet address is required."}), 400

    # Placeholder response with fake transaction signature
    return jsonify({
        "success": True,
        "message": f"1,000 RAMP sent to {wallet}!",
        "signature": "mock-signature-123456789"
    }), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
