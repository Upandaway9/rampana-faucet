from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import os
import json

app = Flask(__name__)
CORS(app)

# Correct path to the keypair file
CREATOR_KEYPAIR_PATH = os.path.join(os.path.dirname(__file__), "faucet-keypair.json")

def load_keypair(path):
    with open(path, 'r') as f:
        secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))

creator = load_keypair(CREATOR_KEYPAIR_PATH)
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"  # Your Rampana token mint

@app.route("/")
def health():
    return "Rampana Faucet is Live!"

@app.route("/claim", methods=["POST"])
def claim():
    data = request.get_json()
    wallet_address = data.get("wallet")
    if not wallet_address:
        return jsonify({"error": "Missing wallet address"}), 400

    try:
        # Airdrop a small amount of SOL to the wallet to ensure they can receive tokens
        response = client.request_airdrop(Pubkey.from_string(wallet_address), 1000000000)  # 0.001 SOL
        return jsonify({"success": True, "tx": response["result"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
