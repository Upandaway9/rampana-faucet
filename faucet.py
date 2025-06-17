from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction  # ← USE solders version!
from solana.rpc.api import Client
from spl.token.instructions import (
    transfer_checked,
    get_associated_token_address,
    create_associated_token_account
)
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
import os
import json
import base64
import asyncio

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"
DECIMALS = 6

app = Flask(__name__)
CORS(app)

def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()
creator_pubkey = creator.pubkey()
client = Client("https://api.devnet.solana.com", commitment=Confirmed)

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
def drip():
    data = request.get_json()
    if "wallet" not in data:
        return jsonify({"success": False, "error": "Missing wallet address"}), 400

    try:
        recipient_pubkey = Pubkey.from_string(data["wallet"])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sig = loop.run_until_complete(send_token(recipient_pubkey))
        return jsonify({"success": True, "signature": sig})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

async def send_token(recipient_pubkey):
    mint = Pubkey.from_string(TOKEN_MINT_ADDRESS)
    source_ata = get_associated_token_address(creator_pubkey, mint)
    dest_ata = get_associated_token_address(recipient_pubkey, mint)

    tx = Transaction()

    info = client.get_account_info(dest_ata)
    if not info["result"]["value"]:
        tx.add(create_associated_token_account(creator_pubkey, recipient_pubkey, mint))

    tx.add(transfer_checked(
        program_id=TOKEN_PROGRAM_ID,
        source=source_ata,
        mint=mint,
        dest=dest_ata,
        owner=creator_pubkey,
        amount=1_000_000,  # 1 Rampana (with 6 decimals)
        decimals=DECIMALS,
        signers=[]
    ))

    result = client.send_transaction(tx, creator, opts=TxOpts(skip_preflight=True))
    return result["result"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
