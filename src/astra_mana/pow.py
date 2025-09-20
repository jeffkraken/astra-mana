import hashlib, json

def difficulty_for_hours(hours: float) -> int:
    if hours <= 1: return 1
    if hours <= 3: return 2
    if hours <= 8: return 3
    return 4  # cap for demo

def payload_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()

def mine(payload: dict, attestation_hex: str, difficulty: int):
    nonce = 0
    payload = {**payload}
    while True:
        payload["nonce"] = nonce
        pbytes = payload_bytes(payload)
        pow_hash = hashlib.sha256(pbytes + bytes.fromhex(attestation_hex)).hexdigest()
        if pow_hash.startswith("0" * difficulty):
            return nonce, pow_hash
        nonce += 1

