from flask import Flask, request, jsonify
from flask_cors import CORS
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.transaction import Transaction
from spl.token.instructions import transfer_checked, get_associated_token_address
from solana.keypair import Keypair
import base64
import os
import json

app = Flask(__name__)
CORS(app)

# Constants
SOLANA_RPC_URL = "https://api.devnet.solana.com"
TOKEN_MINT_ADDRESS = PublicKey("9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt")
TOKEN_DECIMALS = 9
AMOUNT_TO_SEND = 1_000 * (10 ** TOKEN_DECIMALS)

# Load the creator wallet keypair
CREATOR_KEYPAIR_PATH = os.path.expanduser("~/.config/solana/faucet-keypair.json")
with open(CREATOR_KEYPAIR_PATH, "r") as f:
    secret_key = json.load(f)
creator = Keypair.from_secret_key(bytes(secret_key))
creator_pubkey = creator.public_key

# Setup client
client = Client(SOLANA_RPC_URL)

@app.route("/")
def home():
    return "Rampana Faucet is Live!"

@app.route("/claim", methods=["POST"])
def claim():
    data = request.get_json()
    recipient_address = data.get("wallet")

    if not recipient_address:
        return jsonify({"error": "Missing wallet address"}), 400

    try:
        recipient_pubkey = PublicKey(recipient_address)
        recipient_ata = get_associated_token_address(recipient_pubkey, TOKEN_MINT_ADDRESS)
        sender_ata = get_associated_token_address(creator_pubkey, TOKEN_MINT_ADDRESS)

        # Create transfer transaction
        txn = Transaction().add(
            transfer_checked(
                source=sender_ata,
                dest=recipient_ata,
                owner=creator_pubkey,
                amount=AMOUNT_TO_SEND,
                decimals=TOKEN_DECIMALS,
                mint=TOKEN_MINT_ADDRESS,
            )
        )

        # Send transaction
        response = client.send_transaction(txn, creator)
        signature = response.get("result")

        if not signature:
            return jsonify({"error": "Transaction failed", "details": response}), 500

        return jsonify({"signature": signature})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
