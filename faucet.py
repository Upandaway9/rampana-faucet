from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import os
import json
import base64

app = Flask(__name__)
CORS(app)

# Load keypair from base64-encoded environment variable
def load_keypair_from_env():
    encoded = os.environ.get("CREATOR_KEYPAIR_B64")  # ✅ changed here
    if not encoded:
        raise ValueError("Missing CREATOR_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"  # Your Rampana token mint

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

# (Optional) Add more routes here for distributing tokens...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
