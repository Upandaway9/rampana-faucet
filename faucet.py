from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Program, Wallet
from anchorpy.provider import create_http_client
from solana.rpc.types import TxOpts
from spl.token.instructions import transfer_checked, get_associated_token_address, create_associated_token_account
import os
import json
import base64
import asyncio

TOKEN_MINT_ADDRESS = "9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt"

app = Flask(__name__)
CORS(app)

def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    return Keypair.from_bytes(decoded)

creator_kp = load_keypair_from_env()
creator_pub = creator_kp.pubkey()
client = Client("https://api.devnet.solana.com", commitment=Confirmed)

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
def drip():
    data = request.get_json()
    if "wallet" not in data:
        return jsonify({"success": False, "error": "Missing wallet address"}), 400

    recipient = Pubkey.from_string(data["wallet"])

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_tokens(recipient))
        return jsonify({"success": True, "signature": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

async def send_tokens(recipient: Pubkey):
    from spl.token.constants import TOKEN_PROGRAM_ID
    from solana.transaction import Transaction

    mint = Pubkey.from_string(TOKEN_MINT_ADDRESS)
    sender_token_account = get_associated_token_address(creator_pub, mint)
    recipient_token_account = get_associated_token_address(recipient, mint)

    tx = Transaction()

    resp = client.get_account_info(recipient_token_account)
    if resp["result"]["value"] is None:
        tx.add(create_associated_token_account(creator_pub, recipient, mint))

    tx.add(transfer_checked(
        program_id=TOKEN_PROGRAM_ID,
        source=sender_token_account,
        mint=mint,
        dest=recipient_token_account,
        owner=creator_pub,
        amount=1_000_000,  # amount in base units (adjust for decimals)
        decimals=6  # replace with your token's decimals
    ))

    resp = client.send_transaction(tx, creator_kp, opts=TxOpts(skip_preflight=True))
    return resp["result"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
