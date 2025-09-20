#Demo-grade file keystore (PEM). For class use only—teach that real deployments should encrypt or use a KMS.
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

DEFAULT_DIR = Path.home() / ".astra_mana" / "keys"

def save_private_key(priv: Ed25519PrivateKey, name: str, key_dir: Path = DEFAULT_DIR, password: Optional[str] = None) -> Path:
    key_dir.mkdir(parents=True, exist_ok=True)
    path = key_dir / f"{name}.pem"
    enc = serialization.NoEncryption() if not password else serialization.BestAvailableEncryption(password.encode())
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc
    )
    with open(path, "wb") as f:
        f.write(pem)
    return path

def load_private_key(name: str, key_dir: Path = DEFAULT_DIR, password: Optional[str] = None) -> Ed25519PrivateKey:
    path = key_dir / f"{name}.pem"
    with open(path, "rb") as f:
        data = f.read()
    return serialization.load_pem_private_key(data, password.encode() if password else None)

