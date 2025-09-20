# Astra Mana
Environmental Stewardship Token Demo (PoW + Verifiable Claims)

---

## What is this?
Astra Mana is a **teaching project** that shows how environmental work 
(e.g., tree planting, habitat restoration, invasive species removal) 
can be recorded as **verifiable claims** and rewarded with 
cryptocurrency-like tokens.

The demo uses:

- **Ed25519 signatures** – to prove the claim came from a registered supporter
- **Proof-of-Work (PoW)** – to add a small cost to claims (anti-spam)
- **SQLite ledger** – to store supporters, claims, tokens, and transactions
- **Command Line Interface (CLI)** – to walk through the full lifecycle

This project is **not a blockchain**, but it mimics blockchain ideas 
in a classroom-friendly way.

---

## Requirements
- Python 3.10+
- Git
- GitHub account (only for contributing)

---

## Quickstart
This is the **fastest way** to see Astra Mana in action.

# 1. Clone and enter the repo
git clone https://github.com/<YOURNAME>/astra-mana.git
cd astra-mana

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install locally
pip install -e .

# 4. Initialize Astra (creates astra.db and wallet)
astra-mana init --db astra.db --tph 10 --max-hours 24

# 5. Generate a supporter keypair (Taylor)
astra-mana gen-keys --supporter Taylor
# Copy the pubkey_hex from the output

# 6. Register Taylor with Astra
astra-mana register --db astra.db --supporter Taylor --pubkey-hex <PASTE_PUBKEY_HEX>

# 7. Create a proof (signed + mined)
astra-mana create-proof \
  --supporter Taylor \
  --action "Removed invasive species and mulched native saplings" \
  --hours 3.5 \
  --evidence-uri https://example.org/proofs/taylor-2025-09-19.pdf \
  --out proof.json

# 8. Submit the proof to Astra (verify + mint tokens)
astra-mana submit-proof --db astra.db --proof-json proof.json

# 9. Check Astra’s wallet
astra-mana wallet --db astra.db
