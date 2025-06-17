from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from spl.token.instructions import transfer_checked, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID
import os
import json
import base64

app = Flask(__name__)
CORS(app)

# Load keypair from base64-encoded environment variable
def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()
client = Client("https://api.devnet.solana.com")

TOKEN_MINT_ADDRESS = Pubkey.from_string("9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt")  # Rampana token

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
def drip():
    try:
        data = request.get_json()
        recipient_str = data.get("wallet")
        if not recipient_str:
            return jsonify({"success": False, "error": "Missing wallet address"}), 400

        recipient = Pubkey.from_string(recipient_str)
        sender_ata = get_associated_token_address(creator.pubkey(), TOKEN_MINT_ADDRESS)
        recipient_ata = get_associated_token_address(recipient, TOKEN_MINT_ADDRESS)

        # Prepare the transfer instruction (1000 Rampana with 6 decimals = 1_000_000)
        ix = transfer_checked(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_ata,
            mint=TOKEN_MINT_ADDRESS,
            dest=recipient_ata,
            owner=creator.pubkey(),
            amount=1_000_000,
            decimals=6
        )

        # Get recent blockhash
        recent_blockhash = client.get_latest_blockhash()["result"]["value"]["blockhash"]

        tx = Transaction(recent_blockhash=recent_blockhash, fee_payer=creator.pubkey())
        tx.add(ix)
        tx_signed = tx.sign([creator])

        # Send the transaction
        response = client.send_transaction(tx_signed, creator)

        return jsonify({"success": True, "tx_signature": response["result"]})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
