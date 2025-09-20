import sqlite3, uuid
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class Ledger:
    def __init__(self, path="astra_ledger.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS supporters(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            pubkey_hex TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS claims(
            claim_id TEXT PRIMARY KEY,
            supporter_id TEXT NOT NULL,
            action TEXT, hours REAL, timestamp TEXT,
            evidence_uri TEXT, evidence_hash TEXT,
            nonce INTEGER, pow_hash TEXT, attestation_hex TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(supporter_id) REFERENCES supporters(id)
        );
        CREATE TABLE IF NOT EXISTS wallet(
            owner TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            balance INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions(
            id TEXT PRIMARY KEY,
            type TEXT, token TEXT, amount INTEGER,
            owner TEXT, timestamp TEXT,
            related_claim_id TEXT
        );
        """)
        self.conn.commit()

    # supporters
    def add_supporter(self, name: str, pubkey_hex: str):
        sid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO supporters(id,name,pubkey_hex,created_at) VALUES(?,?,?,?)",
            (sid, name, pubkey_hex, utcnow())
        )
        self.conn.commit()
        return sid

    def get_supporter_by_name(self, name: str):
        cur = self.conn.execute("SELECT id,pubkey_hex FROM supporters WHERE name=?", (name,))
        return cur.fetchone()  # (id, pubkey_hex) or None

    # claims
    def record_claim(self, claim: dict, supporter_id: str, status="pending"):
        self.conn.execute("""
            INSERT INTO claims(claim_id,supporter_id,action,hours,timestamp,
                               evidence_uri,evidence_hash,nonce,pow_hash,attestation_hex,
                               status,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            claim["claim_id"], supporter_id, claim["action"], claim["hours"], claim["timestamp"],
            claim.get("evidence_uri",""), claim.get("evidence_hash",""),
            claim["nonce"], claim["pow_hash"], claim["attestation"],
            status, utcnow()
        ))
        self.conn.commit()

    def mark_claim(self, claim_id: str, status: str):
        self.conn.execute("UPDATE claims SET status=? WHERE claim_id=?", (status, claim_id))
        self.conn.commit()

    def has_claim(self, claim_id: str) -> bool:
        return self.conn.execute("SELECT 1 FROM claims WHERE claim_id=?", (claim_id,)).fetchone() is not None

    def has_powhash(self, h: str) -> bool:
        return self.conn.execute("SELECT 1 FROM claims WHERE pow_hash=?", (h,)).fetchone() is not None

    # wallet/tx
    def ensure_wallet(self, owner="Astra", token="ManaToken"):
        if not self.conn.execute("SELECT 1 FROM wallet WHERE owner=?", (owner,)).fetchone():
            self.conn.execute("INSERT INTO wallet(owner,token,balance) VALUES(?,?,?)",
                              (owner, token, 0))
            self.conn.commit()

    def deposit(self, amount: int, owner="Astra", token="ManaToken", related_claim_id=None):
        self.conn.execute("UPDATE wallet SET balance = balance + ? WHERE owner=?", (amount, owner))
        self.conn.execute("""
            INSERT INTO transactions(id,type,token,amount,owner,timestamp,related_claim_id)
            VALUES(?,?,?,?,?,?,?)
        """, (str(uuid.uuid4()), "deposit", token, amount, owner, utcnow(), related_claim_id))
        self.conn.commit()

    def wallet_state(self, owner="Astra"):
        row = self.conn.execute("SELECT token,balance FROM wallet WHERE owner=?", (owner,)).fetchone()
        return row if row else ("ManaToken", 0)
