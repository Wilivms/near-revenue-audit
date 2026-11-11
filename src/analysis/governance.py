"""HSP-029, the issuance cut, read on-chain from the House of Stake voting contract (vote.dao).

The proposal lowers NEAR's maximum issuance from 2.5% to 1.6% a year on a 24-month ramp. After
the vote it sits in a 14-day timelock; the proposal then foresees a 90-day grace period and a
protocol upgrade that validators must adopt. The earliest date the ramp can start therefore
follows from the chain: end of timelock + 90 days. The Monte Carlo uses that date.

`fetch()` saves the proposal to data/raw/governance/hsp029_<date>.json; `main()` runs offline.
Output: data/processed/governance_hsp029.json.
"""
from __future__ import annotations

import base64
import json
import sys

import pandas as pd
import requests

from ..ingest.sources import NEAR_RPC, RAW, _today
from .ledger import OUT

PROPOSAL_ID = 29
GRACE_DAYS = 90  # stated in the proposal; the ramp cannot start before timelock end + grace


def fetch() -> dict:
    args = base64.b64encode(json.dumps({"from_index": PROPOSAL_ID, "limit": 1}).encode()).decode()
    r = requests.post(NEAR_RPC, json={"jsonrpc": "2.0", "id": 1, "method": "query", "params": {
        "request_type": "call_function", "finality": "final", "account_id": "vote.dao",
        "method_name": "get_proposals", "args_base64": args}}, timeout=60).json()
    p = json.loads(bytes(r["result"]["result"]))[0]
    p["_block_height"] = r["result"]["block_height"]
    folder = RAW / "governance"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"hsp029_{_today()}.json").write_text(json.dumps(p))
    return p


def _ts(ns) -> pd.Timestamp | None:
    return pd.Timestamp(int(ns), unit="ns", tz="UTC") if ns and str(ns) != "0" else None


def summary() -> dict:
    p = json.loads(sorted((RAW / "governance").glob("hsp029_*.json"))[-1].read_text())
    votes = [int(v["total_venear"]) / 1e24 for v in p["votes"]]  # option order: for, against, abstain
    cast = sum(votes)
    snap_total = int(p["snapshot_and_state"]["total_venear"]) / 1e24
    voting_end = _ts(p["voting_start_time_ns"]) + pd.Timedelta(int(p["voting_duration_ns"]), unit="ns")
    timelock_end = voting_end + pd.Timedelta(int(p["timelock_duration_ns"]), unit="ns")
    return {
        "proposal_id": p["id"], "title": p["title"], "status": p["status"], "read_at_block": p.get("_block_height"),
        "venear_for": votes[0], "venear_against": votes[1], "venear_abstain": votes[2],
        "share_for_of_cast": votes[0] / cast, "voters": int(p["total_votes"]["total_votes"]),
        "venear_cast": cast, "venear_snapshot_total": snap_total, "turnout": cast / snap_total,
        "approval_threshold": int(p["approval_threshold_bps"]) / 1e4, "quorum_threshold": int(p["quorum_threshold_bps"]) / 1e4,
        "voting_started": str(_ts(p["voting_start_time_ns"])), "voting_ended": str(voting_end),
        "timelock_ends": str(timelock_end),
        "earliest_ramp_start": str((timelock_end + pd.Timedelta(days=GRACE_DAYS)).date()),
    }


def main(refresh: bool = False) -> None:
    if refresh:
        try:
            fetch()
        except Exception as e:  # noqa: BLE001
            print(f"WARNING vote.dao fetch failed, using the last snapshot: {e}")
    s = summary()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "governance_hsp029.json").write_text(json.dumps(s, indent=1))
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main(refresh="--refresh" in sys.argv)
