"""Collect per-swap data from the NEAR Intents Explorer API (1Click swaps).

- Walks backwards in time from now to --since, 1000 swaps per request,
  one request every 5.5 s (the API allows one per 5 s per partner).
- Resumable: progress is checkpointed, re-running continues where it stopped.
- Keeps only the fields the analysis needs. Sender addresses are replaced by a
  salted hash: we need to count returning users, not to identify them.

Output: data/intents_v2/swaps_<YYYY-MM-DD>.csv.gz, one file per UTC day of swaps.
v2 keeps each fee recipient's own share (`app_fees` = "recipient:bps|recipient:bps"),
which is what separates NEAR's take from integrators' fees.

Coverage: this API returns 1Click swaps only (about 28% of the total Intents volume
reported by DefiLlama for 2026-10-15..28). Swaps routed directly through intents.near,
including confidential ones, are not in it.
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
OUT = ROOT / "data" / "intents_v2"
STATE = OUT / "_checkpoint.json"
SALT = "near-revenue-audit"
FIELDS = [
    "created_at", "status", "origin_asset", "destination_asset",
    "amount_in_usd", "amount_out_usd", "referral", "app_fee_bps",
    "app_fee_recipients", "app_fees", "deposit_type", "recipient_type", "sender_hash",
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
        "app_fees": "|".join(f"{f.get('recipient', '')}:{f.get('fee', 0)}" for f in fees),
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


def collect(since: str, max_requests: int, until: str | None = None) -> None:
    """Walk back from `until` (or now) to `since`. Each window keeps its own checkpoint."""
    OUT.mkdir(parents=True, exist_ok=True)
    state_file = STATE if until is None else OUT / f"_checkpoint_{until[:10]}.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    headers = {"Authorization": f"Bearer {intents_jwt()}"}
    for i in range(max_requests):
        params = {
            "numberOfTransactions": 1000,
            "direction": "next",
            "statuses": "SUCCESS,REFUNDED,FAILED",
        }
        if until and not state.get("last_address"):
            params["endTimestamp"] = until
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
        state_file.write_text(json.dumps(state))
        if i % 20 == 0:
            print(f"{state['rows']} swaps, back to {state['oldest_seen']}", flush=True)
        if last["createdAt"] < since:
            print("reached", since, flush=True)
            break
        time.sleep(5.5)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--since", default="2026-08-15T00:00:00Z")
    p.add_argument("--until", default=None, help="window end (ISO). Omit to start from now.")
    p.add_argument("--max-requests", type=int, default=10_000)
    p.add_argument("--sample-weeks", action="store_true",
                   help="collect one week per month, Feb–Jul 2026 (days 8–14), one window after another")
    a = p.parse_args()
    if a.sample_weeks:
        for month in range(2, 8):
            start, end = f"2026-{month:02d}-08T00:00:00Z", f"2026-{month:02d}-15T00:00:00Z"
            print("window", start, "->", end, flush=True)
            collect(start, a.max_requests, until=end)
    else:
        collect(a.since, a.max_requests, until=a.until)
