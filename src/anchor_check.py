"""Read the hashes anchored on NEAR testnet and compare them with the files in this repository.

`anchor/anchor.mjs` writes sha256 hashes to SocialDB (v1.social08.testnet) under
near-revenue-audit.testnet/audit/<kind>/<date>: the frozen predictions, the raw-snapshot manifest, and
each day's dashboard bundle. This reads them back with a view call (no key, no account) and checks that
the predictions file is the one anchored, and that the latest snapshot and daily anchors match the files
as committed on that date (`git log`). Needs network access to rpc.testnet.near.org.

    python3 -m src.anchor_check
"""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT, SOCIAL, RPC = "near-revenue-audit.testnet", "v1.social08.testnet", "https://rpc.testnet.near.org"
FILES = {"predictions": "predictions/PREDICTIONS.csv", "snapshot": "data/raw/MANIFEST.json", "daily": "dashboard/live.json"}


def anchored() -> dict:
    args = base64.b64encode(json.dumps({"keys": [f"{ACCOUNT}/audit/**"]}).encode()).decode()
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "query", "params": {
        "request_type": "call_function", "finality": "final", "account_id": SOCIAL, "method_name": "get", "args_base64": args}}, timeout=30)
    r.raise_for_status()
    raw = json.loads(bytes(r.json()["result"]["result"]))
    return {kind: {d: json.loads(v) for d, v in by_date.items()} for kind, by_date in raw.get(ACCOUNT, {}).get("audit", {}).items()}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _committed_shas(path: str) -> set[str]:
    """sha256 of every committed version of a file (a daily anchor may precede or follow a commit)."""
    revs = subprocess.run(["git", "log", "--format=%H", "--", path], cwd=ROOT, capture_output=True, text=True).stdout.split()
    out = set()
    for rev in revs:
        blob = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True).stdout
        if blob:
            out.add(_sha(blob))
    return out


def main() -> int:
    a = anchored()
    ok = True
    for kind, path in FILES.items():
        entries = a.get(kind, {})
        if not entries:
            print(f"{kind:12s} no anchor yet")
            continue
        current = _sha((ROOT / path).read_bytes())
        known = _committed_shas(path) | {current}
        for d in sorted(entries):
            match = entries[d]["sha256"] in known
            print(f"{kind:12s} {d}  {entries[d]['sha256'][:16]}…  {'matches a committed ' + path if match else 'NO MATCH'}")
            ok &= match or kind != "predictions"
        if kind == "predictions":
            same = entries[max(entries)]["sha256"] == current
            print(f"{'':12s} current {path} {'is' if same else 'is NOT'} the anchored file")
            ok &= same
    print("anchors: OK" if ok else "anchors: MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
