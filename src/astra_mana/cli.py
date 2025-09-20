import argparse, json, hashlib
from pathlib import Path
from .core import NonHumanIdentity, Supporter
from .crypto import pubkey_to_hex
from .keystore import save_private_key, load_private_key, DEFAULT_DIR

def main():
    p = argparse.ArgumentParser(prog="astra-mana", description="Astra Mana: verifiable stewardship claims → token rewards")
    sub = p.add_subparsers(dest="cmd", required=True)

    # init astra
    s_init = sub.add_parser("init", help="Initialize Astra (creates DB & wallet)")
    s_init.add_argument("--name", default="Astra")
    s_init.add_argument("--classif", default="Spirit of a Grave Tree")
    s_init.add_argument("--purpose", default="Realm Defender")
    s_init.add_argument("--db", default="astra_ledger.db")
    s_init.add_argument("--tph", type=int, default=10, help="Tokens per hour")
    s_init.add_argument("--max-hours", type=float, default=24.0)

    # register supporter
    s_reg = sub.add_parser("register", help="Register supporter public key with Astra")
    s_reg.add_argument("--db", default="astra_ledger.db")
    s_reg.add_argument("--supporter", required=True, help="Supporter name")
    s_reg.add_argument("--pubkey-hex", required=True)

    # generate keys and save to keystore
    s_keys = sub.add_parser("gen-keys", help="Generate a supporter keypair and save private key to keystore")
    s_keys.add_argument("--supporter", required=True, help="Supporter name")
    s_keys.add_argument("--key-dir", default=str(DEFAULT_DIR))
    s_keys.add_argument("--password", default=None, help="Optional password for PEM (demo only)")

    # create proof (loads private key from keystore)
    s_proof = sub.add_parser("create-proof", help="Create a signed+mined proof JSON")
    s_proof.add_argument("--supporter", required=True)
    s_proof.add_argument("--action", required=True)
    s_proof.add_argument("--hours", type=float, required=True)
    s_proof.add_argument("--evidence-uri", default="")
    s_proof.add_argument("--evidence-hash", default="")
    s_proof.add_argument("--key-dir", default=str(DEFAULT_DIR))
    s_proof.add_argument("--password", default=None)
    s_proof.add_argument("--out", default="proof.json")

    # submit proof to Astra
    s_submit = sub.add_parser("submit-proof", help="Verify proof and mint tokens")
    s_submit.add_argument("--db", default="astra_ledger.db")
    s_submit.add_argument("--proof-json", required=True)
    s_submit.add_argument("--name", default="Astra")
    s_submit.add_argument("--classif", default="Spirit of a Grave Tree")
    s_submit.add_argument("--purpose", default="Realm Defender")
    s_submit.add_argument("--tph", type=int, default=10)
    s_submit.add_argument("--max-hours", type=float, default=24.0)

    # show wallet
    s_wallet = sub.add_parser("wallet", help="Show Astra wallet")
    s_wallet.add_argument("--db", default="astra_ledger.db")
    s_wallet.add_argument("--name", default="Astra")
    s_wallet.add_argument("--classif", default="Spirit")
    s_wallet.add_argument("--purpose", default="Realm Defender")

    args = p.parse_args()

    if args.cmd == "init":
        astra = NonHumanIdentity(args.name, args.classif, args.purpose, tokens_per_hour=args.tph, max_hours_per_claim=args.max_hours, db_path=args.db)
        print(f"Initialized {args.name} → DB: {args.db} | TPH={args.tph} | MAX_HOURS={args.max_hours}")

    elif args.cmd == "gen-keys":
        # generate and save
        sup = Supporter(args.supporter)
        path = save_private_key(sup.priv, args.supporter, key_dir=Path(args.key_dir), password=args.password)
        print(json.dumps({
            "supporter": args.supporter,
            "keystore_path": str(path),
            "pubkey_hex": sup.pubkey_hex
        }, indent=2))

    elif args.cmd == "register":
        astra = NonHumanIdentity("Astra", "Spirit", "Realm Defender", db_path=args.db)
        astra.register_supporter(args.supporter, args.pubkey_hex)

    elif args.cmd == "create-proof":
        priv = load_private_key(args.supporter, key_dir=Path(args.key_dir), password=args.password)
        sup = Supporter(args.supporter, priv=priv)
        proof = sup.create_proof(args.action, args.hours, args.evidence_uri, args.evidence_hash)
        with open(args.out, "w") as f:
            json.dump(proof, f, indent=2)
        print(f"Wrote {args.out}")

    elif args.cmd == "submit-proof":
        astra = NonHumanIdentity(args.name, args.classif, args.purpose, tokens_per_hour=args.tph, max_hours_per_claim=args.max_hours, db_path=args.db)
        with open(args.proof_json, "r") as f:
            proof = json.load(f)
        reward = astra.submit_proof(proof)
        print(json.dumps({"reward": reward, "wallet": astra.wallet()}, indent=2))

    elif args.cmd == "wallet":
        astra = NonHumanIdentity(args.name, args.classif, args.purpose, db_path=args.db)
        print(json.dumps(astra.wallet(), indent=2))
