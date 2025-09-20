from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization

def generate_keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return priv, pub

def sign(priv: Ed25519PrivateKey, message: bytes) -> bytes:
    return priv.sign(message)

def verify(pub: Ed25519PublicKey, signature: bytes, message: bytes) -> bool:
    try:
        pub.verify(signature, message)
        return True
    except Exception:
        return False

def pubkey_to_hex(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return raw.hex()

def pubkey_from_hex(h: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(h))
