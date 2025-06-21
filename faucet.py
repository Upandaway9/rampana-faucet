from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.hash import Hash
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from spl.token.instructions import (
    get_associated_token_address,
    create_associated_token_account,
    transfer_checked,
    TransferCheckedParams
)
from spl.token.constants import TOKEN_PROGRAM_ID

import os
import base64
import traceback

app = Flask(__name__)
CORS(app)

# Rate limiter: 1 request per IP per day
limiter = Limiter(get_remote_address, app=app, default_limits=["1 per day"])

client = Client("https://api.devnet.solana.com")
TOKEN_MINT_ADDRESS = Pubkey.from_string("9tc7JNiGyTpPqzgaJMJnQWhLsuPWusVXRR7HgQ3ng5xt")

def load_keypair_from_env():
    encoded = os.environ.get("FAUCET_KEYPAIR_B64")
    if not encoded:
        raise ValueError("Missing FAUCET_KEYPAIR_B64 environment variable")
    decoded = base64.b64decode(encoded)
    if len(decoded) != 64:
        raise ValueError("Decoded keypair must be 64 bytes")
    return Keypair.from_bytes(decoded)

creator = load_keypair_from_env()

@app.route("/")
def health():
    return "Rampana Faucet is alive!"

@app.route("/drip", methods=["POST"])
@limiter.limit("1 per day")
def drip():
    try:
        data = request.get_json()
        wallet = data.get("wallet")
        if not wallet:
            return jsonify({"success": False, "error": "Missing wallet address"}), 400

        recipient = Pubkey.from_string(wallet)
        faucet_ata = get_associated_token_address(creator.pubkey(), TOKEN_MINT_ADDRESS)
        recipient_ata = get_associated_token_address(recipient, TOKEN_MINT_ADDRESS)

        ata_ix = create_associated_token_account(
            payer=creator.pubkey(),
            owner=recipient,
            mint=TOKEN_MINT_ADDRESS
        )

        transfer_ix = transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=faucet_ata,
                mint=TOKEN_MINT_ADDRESS,
                dest=recipient_ata,
                owner=creator.pubkey(),
                amount=1000,
                decimals=0,
                signers=[]
            )
        )

        blockhash_obj = client.get_latest_blockhash(Confirmed)
        recent_blockhash = blockhash_obj.value.blockhash

        message = MessageV0.try_compile(
            payer=creator.pubkey(),
            instructions=[ata_ix, transfer_ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash
        )

        tx = VersionedTransaction(message, [creator])
        response = client.send_transaction(tx, opts={"skip_preflight": True, "preflight_commitment": "confirmed"})

        return jsonify({"success": True, "signature": str(response.value)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
