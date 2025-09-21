import uuid, json, hashlib
from datetime import datetime, timezone
from .crypto import sign, verify, generate_keypair, pubkey_to_hex, pubkey_from_hex
from .pow import difficulty_for_hours, payload_bytes
from .ledger import Ledger

class NonHumanIdentity:
    def __init__(self, name, classification, purpose, tokens_per_hour=10, max_hours_per_claim=24, db_path="astra_ledger.db"):
        self.name = name
        self.classification = classification
        self.purpose = purpose
        self.tokens_per_hour = tokens_per_hour
        self.max_hours_per_claim = max_hours_per_claim
        self.ledger = Ledger(db_path)
        self.ledger.ensure_wallet(owner=name)

    def register_supporter(self, name: str, pubkey_hex: str):
        self.ledger.add_supporter(name, pubkey_hex)
        print(f"[{self.name}] Registered supporter '{name}'")

    def submit_proof(self, proof: dict):
        required = ["claim_id","supporter","action","hours","timestamp",
                    "evidence_uri","evidence_hash","nonce","attestation","pow_hash"]
        for k in required:
            if k not in proof:
                raise ValueError(f"Missing field: {k}")

        if self.ledger.has_claim(proof["claim_id"]):
            raise ValueError("Duplicate claim_id (replay).")
        if self.ledger.has_powhash(proof["pow_hash"]):
            raise ValueError("Duplicate pow_hash (replay).")

        hours = float(proof["hours"])
        if hours <= 0 or hours > self.max_hours_per_claim:
            raise ValueError("Hours out of policy bounds.")

        submitted = datetime.fromisoformat(proof["timestamp"].replace("Z","+00:00"))
        if submitted > datetime.now(timezone.utc):
            raise ValueError("Timestamp in the future.")

        sup = self.ledger.get_supporter_by_name(proof["supporter"])
        if not sup:
            raise PermissionError("Unrecognized supporter.")
        supporter_id, pubkey_hex = sup

        payload = {
            "claim_id": proof["claim_id"],
            "supporter": proof["supporter"],
            "action": proof["action"],
            "hours": proof["hours"],
            "timestamp": proof["timestamp"],
            "evidence_uri": proof.get("evidence_uri",""),
            "evidence_hash": proof.get("evidence_hash",""),
            "nonce": proof["nonce"]
        }
        pbytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()

        pub = pubkey_from_hex(pubkey_hex)
        if not verify(pub, bytes.fromhex(proof["attestation"]), pbytes):
            raise PermissionError("Signature verification failed.")

        computed_pow = hashlib.sha256(pbytes + bytes.fromhex(proof["attestation"])).hexdigest()
        if computed_pow != proof["pow_hash"]:
            raise ValueError("pow_hash mismatch.")
        if not computed_pow.startswith("0" * difficulty_for_hours(hours)):
            raise ValueError("Insufficient PoW difficulty.")

        self.ledger.record_claim(proof, supporter_id, status="accepted")
        reward = int(round(hours * self.tokens_per_hour))
        self.ledger.deposit(reward, owner=self.name, related_claim_id=proof["claim_id"])
        print(f"[{self.name}] Accepted claim {proof['claim_id']} from {proof['supporter']} → {reward} ManaTokens")
        return reward

    def wallet(self):
        token, balance = self.ledger.wallet_state(owner=self.name)
        return {token: balance}

class Supporter:
    """Convenience class for scripts (CLI loads keys via keystore)."""
    def __init__(self, name, priv=None):
        self.name = name
        self.priv, self.pub = (priv or generate_keypair())
        self.pubkey_hex = pubkey_to_hex(self.pub)
        self.name = name
        if priv is None:
            self.priv, self.pub = generate_keypair()
        else:
            self.priv = priv
            self.pub = priv.public_key()
        self.pubkey_hex = pubkey_to_hex(self.pub)

    def create_proof(self, action, hours, evidence_uri="", evidence_hash=""):
        claim_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        payload = {
            "claim_id": claim_id,
            "supporter": self.name,
            "action": action,
            "hours": hours,
            "timestamp": timestamp,
            "evidence_uri": evidence_uri,
            "evidence_hash": evidence_hash,
            "nonce": 0
        }
        # mine by iterating nonce: sign -> sha256(payload+sig) -> check difficulty
        while True:
            pbytes = payload_bytes(payload)
            attestation = sign(self.priv, pbytes).hex()
            pow_hash = hashlib.sha256(pbytes + bytes.fromhex(attestation)).hexdigest()
            if pow_hash.startswith("0" * difficulty_for_hours(hours)):
                return {**payload, "attestation": attestation, "pow_hash": pow_hash}
            payload["nonce"] += 1
