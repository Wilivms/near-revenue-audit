"""The protocol treasury's NEAR in 2026: was it sold? A supply question the buyback figures leave out.

10% of NEAR's issuance goes to the protocol treasury (treasury.near). F3 compares buybacks with all new
NEAR, as if all of it could reach the market. In April and May 2026 the treasury moved 30.17M NEAR out,
about nine times the NEAR the revenue wallets have received since the fee switch. Followed hop by hop on
NEAR's BigQuery dataset (`sql/treasury_walk.sql`, result in data/raw/bigquery/treasury_walk_<date>.csv),
this reads where it went: staked, unstaked, pooled with the NEAR Foundation endowment, and staked again.

Output: data/processed/treasury.json.
"""
from __future__ import annotations

import json

import pandas as pd

from .ledger import OUT, RAW


def main() -> dict:
    w = pd.read_csv(sorted((RAW / "bigquery").glob("treasury_walk_*.csv"))[-1])
    out = pd.read_csv(sorted((RAW / "bigquery").glob("treasury_out_*.csv"))[-1])
    out = out[out["near"] >= 100_000]
    moved = float(out["near"].sum())
    stake = w[w["method"] == "deposit_and_stake"]
    first_stake = stake[stake["destination"].isin(["p2p-org.poolv1.near", "figment.poolv1.near"]) & (stake["first_day"] == "2026-07-31")]
    unstake = w[w["sender"].isin(["p2p-org.poolv1.near", "figment.poolv1.near"]) & (w["destination"] == first_stake["sender"].iloc[0])]
    last = stake[stake["destination"].str.startswith("cnear-")]
    endow = float(w[(w["sender"] == "nfendowment03.near") & (w["destination"] == "d549d25ebc8dcd705ee1aac7d961fc31b07fa52e8d59ba56ddd788f09d6cec46")]["near"].sum())
    bq = json.loads((OUT / "bigquery_crosscheck.json").read_text())
    captured = float(bq["revenue"]["near_bigquery"])
    res = {"moved_out_2026_near": moved, "moved_months": sorted(out["month"].unique().tolist()),
           "staked_first_near": float(first_stake["near"].sum()), "staked_first_day": "2026-07-31",
           "unstaked_near": float(unstake["near"].sum()), "unstaked_day": str(unstake["first_day"].min()),
           "foundation_endowment_joined_near": endow,
           "staked_again_near": float(last["near"].sum()), "staked_again_days": [str(last["first_day"].min()), str(last["last_day"].max())],
           "staked_again_pools": sorted(last["destination"].unique().tolist()),
           "captured_by_revenue_wallets_near": captured, "moved_over_captured": moved / captured,
           "note": "main paths of moves of 100,000 NEAR or more; the last hop read from NearBlocks; balances read by RPC on 14 Nov 2026"}
    (OUT / "treasury.json").write_text(json.dumps(res, indent=1))
    print(f"treasury: {moved / 1e6:.2f}M NEAR moved out in {', '.join(res['moved_months'])} ({res['moved_over_captured']:.1f}x the NEAR the revenue "
          f"wallets received since the fee switch); {res['staked_first_near'] / 1e6:.2f}M staked on 31 Jul, unstaked on {res['unstaked_day']}, "
          f"pooled with {endow / 1e6:.0f}M from the Foundation endowment and {res['staked_again_near'] / 1e6:.1f}M staked again on {res['staked_again_days'][0]}–{res['staked_again_days'][1][5:]}")
    return res


if __name__ == "__main__":
    main()
