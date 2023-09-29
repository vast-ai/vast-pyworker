from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import os

PUBLIC_KEY_FILENAME = "public_key.pem"

# def format_public_key():
#     key_contents = os.environ["PUBLIC_KEY_CONTENTS"]
#     with open(PUBLIC_KEY_FILENAME, "w") as f:
#         f.write(key_contents)

def load_public_key():
    return RSA.import_key(os.environ["PUBLIC_KEY_CONTENTS"])

def verify_signature(public_key, message, signature):
    h = SHA256.new(message.encode())
    try:
        pkcs1_15.new(public_key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False