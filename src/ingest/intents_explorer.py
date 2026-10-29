"""Collect per-swap data from the NEAR Intents Explorer API (1Click swaps).

- Walks backwards in time from now to --since, 1000 swaps per request,
  one request every 5.5 s (the API allows one per 5 s per partner).
- Resumable: progress is checkpointed, re-running continues where it stopped.
- Keeps only the fields the analysis needs. Sender addresses are replaced by a
  salted hash: we need to count returning users, not to identify them.

Output: data/intents/swaps_<YYYY-MM-DD>.csv.gz, one file per UTC day of swaps.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import requests

from .sources import ROOT, intents_jwt

URL = "https://explorer.near-intents.org/api/v0/transactions"
OUT = ROOT / "data" / "intents"
STATE = OUT / "_checkpoint.json"
SALT = "near-revenue-audit"
FIELDS = [
    "created_at", "status", "origin_asset", "destination_asset",
    "amount_in_usd", "amount_out_usd", "referral", "app_fee_bps",
    "app_fee_recipients", "deposit_type", "recipient_type", "sender_hash",
    "refund_reason", "deposit_address", "deposit_memo",
]


def _row(t: dict) -> dict:
    fees = t.get("appFees") or []
    senders = t.get("senders") or []
    first = senders[0] if senders else ""
    return {
        "created_at": t["createdAt"],
        "status": t["status"],
        "origin_asset": t["originAsset"],
        "destination_asset": t["destinationAsset"],
        "amount_in_usd": t.get("amountInUsd"),
        "amount_out_usd": t.get("amountOutUsd"),
        "referral": t.get("referral") or "",
        "app_fee_bps": sum(f.get("fee", 0) for f in fees),
        "app_fee_recipients": "|".join(f.get("recipient", "") for f in fees),
        "deposit_type": t.get("depositType"),
        "recipient_type": t.get("recipientType"),
        "sender_hash": hashlib.sha256((SALT + first).encode()).hexdigest()[:16] if first else "",
        "refund_reason": t.get("refundReason") or "",
        "deposit_address": t.get("depositAddress") or "",
        "deposit_memo": t.get("depositMemo") or "",
    }


def _append(rows: list[dict]) -> None:
    by_day = defaultdict(list)
    for r in rows:
        by_day[r["created_at"][:10]].append(r)
    for day, items in by_day.items():
        path = OUT / f"swaps_{day}.csv.gz"
        new = not path.exists()
        with gzip.open(path, "at", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerows(items)


def collect(since: str, max_requests: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    headers = {"Authorization": f"Bearer {intents_jwt()}"}
    for i in range(max_requests):
        params = {
            "numberOfTransactions": 1000,
            "direction": "next",
            "statuses": "SUCCESS,REFUNDED,FAILED",
        }
        if state.get("last_address"):
            params["lastDepositAddress"] = state["last_address"]
            if state.get("last_memo"):
                params["lastDepositMemo"] = state["last_memo"]
        r = requests.get(URL, params=params, headers=headers, timeout=90)
        if r.status_code == 429:
            time.sleep(15)
            continue
        if r.status_code >= 500:
            time.sleep(30)
            continue
        r.raise_for_status()
        batch = r.json()
        if not batch:
            print("no more data", flush=True)
            break
        _append([_row(t) for t in batch])
        last = batch[-1]
        state = {
            "last_address": last.get("depositAddress"),
            "last_memo": last.get("depositMemo"),
            "oldest_seen": last["createdAt"],
            "requests": state.get("requests", 0) + 1,
            "rows": state.get("rows", 0) + len(batch),
        }
        STATE.write_text(json.dumps(state))
        if i % 20 == 0:
            print(f"{state['rows']} swaps, back to {state['oldest_seen']}", flush=True)
        if last["createdAt"] < since:
            print("reached", since, flush=True)
            break
        time.sleep(5.5)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--since", default="2026-02-01T00:00:00Z")
    p.add_argument("--max-requests", type=int, default=10_000)
    a = p.parse_args()
    collect(a.since, a.max_requests)
