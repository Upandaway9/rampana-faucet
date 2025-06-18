from flask import Flask, request, jsonify
from flask_cors import CORS
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.hash import Hash
from spl.token.instructions import get_associated_token_address, create_associated_token_account, transfer_checked
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
import os
import json
import base64
import traceback  # Added for error debugging

app = Flask(__name__)
CORS(app)

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
def drip():
    try:
        data = request.get_json()
        wallet = data.get("wallet")

        if not wallet:
            return jsonify({"success": False, "error": "Missing wallet address"}), 400

        recipient = Pubkey.from_string(wallet)
        faucet_ata = get_associated_token_address(creator.pubkey(), TOKEN_MINT_ADDRESS)
        recipient_ata = get_associated_token_address(recipient, TOKEN_MINT_ADDRESS)

        # Create recipient ATA (if not exists)
        ata_ix = create_associated_token_account(
            payer=creator.pubkey(),
            owner=recipient,
            mint=TOKEN_MINT_ADDRESS
        )

        # Transfer 1000 Rampana tokens (0 decimals)
        transfer_ix = transfer_checked(
            TOKEN_PROGRAM_ID,
            faucet_ata,
            TOKEN_MINT_ADDRESS,
            recipient_ata,
            creator.pubkey(),
            1000,
            0
        )

        # Get recent blockhash
        recent_blockhash_resp = client.get_latest_blockhash(Confirmed)
        recent_blockhash = recent_blockhash_resp.value.blockhash

        # Build transaction
        message = MessageV0.try_compile(
            payer=creator.pubkey(),
            instructions=[ata_ix, transfer_ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash
        )
        tx = VersionedTransaction(message, [creator])

        # Send it
        tx_sig = client.send_transaction(tx, opts={"skip_preflight": True, "preflight_commitment": "confirmed"})

        return jsonify({"success": True, "signature": tx_sig["result"]})

    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
