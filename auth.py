from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import os

PUBLIC_KEY_FILENAME = "public_key.pem"

def format_public_key():
    if "PUBLIC_KEY_CONTENTS" in os.environ:
        key_contents = os.environ["PUBLIC_KEY_CONTENTS"]
        with open(PUBLIC_KEY_FILENAME, "w") as f:
            f.write("-----BEGIN PUBLIC KEY-----")
            f.write("\n")
            f.write(key_contents)
            f.write("\n")
            f.write("-----END PUBLIC KEY-----")
        return True
    else:
        return False

def load_public_key():
    with open(PUBLIC_KEY_FILENAME, "r") as f:
        return RSA.import_key(f.read())

def verify_signature(public_key, message, signature):
    h = SHA256.new(message.encode())
    try:
        pkcs1_15.new(public_key).verify(h, base64.b64decode(signature))
        return True
    except (ValueError, TypeError):
        return False