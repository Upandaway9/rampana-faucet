from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.rpc.types import TxOpts
from solana.system_program import transfer, TransferParams
from spl.token.instructions import transfer_checked, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID
import os
import json
import base64
import time

app = Flask(__name__)
CORS(app)

# Load creator keypair from environment variable
def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = Pubkey.from_string("9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt")
FAUCET_AMOUNT = 1_000  # Tokens per request
DRIP_INTERVAL = 24 * 60 * 60  # 24 hours

# Simple in-memory store for rate limiting
last_drip_times = {}

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
def drip():
    data = request.get_json()
    wallet_address = data.get("wallet")

    if not wallet_address:
        return jsonify({"error": "Missing wallet address"}), 400

    now = time.time()
    last_time = last_drip_times.get(wallet_address)
    if last_time and now - last_time < DRIP_INTERVAL:
        return jsonify({"error": "You must wait before claiming again"}), 429

    try:
        recipient = Pubkey.from_string(wallet_address)
        recipient_token_account = get_associated_token_address(recipient, TOKEN_MINT_ADDRESS)

        tx = Transaction()
        tx.add(
            transfer_checked(
                source=get_associated_token_address(creator.pubkey(), TOKEN_MINT_ADDRESS),
                dest=recipient_token_account,
                owner=creator.pubkey(),
                amount=FAUCET_AMOUNT,
                decimals=0,  # Adjust if token has decimals
                mint=TOKEN_MINT_ADDRESS,
                program_id=TOKEN_PROGRAM_ID
            )
        )
        result = client.send_transaction(tx, creator, opts=TxOpts(skip_preflight=True))
        last_drip_times[wallet_address] = now
        return jsonify({"success": True, "tx_signature": result.value}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
