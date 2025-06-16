from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import transfer, TransferParams
from solana.rpc.types import TxOpts
import os
import json
import base64

app = Flask(__name__)
CORS(app)

# Load keypair from environment variable
def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()
client = Client("https://api.devnet.solana.com")

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
def drip():
    try:
        data = request.get_json()
        recipient = Pubkey.from_string(data["wallet"])

        tx = Transaction()
        tx.add(
            transfer(
                TransferParams(
                    from_pubkey=creator.pubkey(),
                    to_pubkey=recipient,
                    lamports=1000000  # 0.001 SOL for testing
                )
            )
        )

        result = client.send_transaction(tx, creator, opts=TxOpts(skip_preflight=True))
        return jsonify({"success": True, "signature": result["result"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
