from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import os
import subprocess

def fetch_public_key():
    command = ["curl", "-X", "GET", "https://run.vast.ai/pubkey/"]
    result = subprocess.check_output(command, universal_newlines=True)
    print("public key:")
    print(result)

    return RSA.import_key(result)

def verify_signature(public_key, message, signature):
    h = SHA256.new(message.encode())
    try:
        pkcs1_15.new(public_key).verify(h, base64.b64decode(signature))
        return True
    except (ValueError, TypeError):
        return False