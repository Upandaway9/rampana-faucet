from flask import Flask, request, jsonify
from flask_cors import CORS
from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
from solana.system_program import transfer, TransferParams
from solders.pubkey import Pubkey
import base58
import os

app = Flask(__name__)
CORS(app)

# Load the creator's keypair from a local file
CREATOR_KEYPAIR_PATH = os.path.expanduser("~/.config/solana/faucet-keypair.json")

def load_keypair(path):
    with open(path, 'r') as f:
        secret = f.read().strip().strip('[]').split(',')
        secret = list(map(int, secret))
        return Keypair.from_secret_key(bytes(secret))

creator = load_keypair(CREATOR_KEYPAIR_PATH)
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"  # Replace with your actual token address

@app.route("/")
def health():
    return "Rampana Faucet is Live!"

@app.route("/claim", methods=["POST"])
def claim():
    data = request.get_json()
    recipient_address = data.get("wallet")
    if not recipient_address:
        return jsonify({"error": "Missing wallet address"}), 400

    try:
        # Transfer 1,000 tokens (remember 9 decimals, so 1000000000 base units)
        tx = client.request_airdrop(Pubkey.from_string(recipient_address), 1000000000)
        if "result" in tx:
            return jsonify({"success": True, "tx": tx["result"]})
        else:
            return jsonify({"success": False, "error": tx}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
