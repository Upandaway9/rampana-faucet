from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import os
import json

app = Flask(__name__)
CORS(app)

# Correct path to the keypair file for Render
CREATOR_KEYPAIR_PATH = "/opt/render/project/src/faucet-keypair.json"

def load_keypair(path):
    with open(path, 'r') as f:
        secret = json.load(f)
        return Keypair.from_bytes(bytes(secret))

creator = load_keypair(CREATOR_KEYPAIR_PATH)
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"

@app.route("/")
def health():
    return "Rampana Faucet is live!"

# (Optional) Add your distribution endpoint later here

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
