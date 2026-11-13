"""Daily 1Click update for the live dashboard bundle (GitHub Action only; needs the partner key).

The per-swap 1Click data comes from the NEAR Intents Explorer API, which needs a partner key and whose
terms do not allow archiving or redistributing it. So the daily refresh, when the repository secret
INTENTS_JWT is set:

1. collects the last 31 days of 1Click swaps into the runner's own disk (deleted when the job ends;
   nothing per-swap is committed),
2. recomputes from them, with the same functions as `make swaps`, the outputs that only need recent
   swaps: the 30-day integrator shares, revenue by asset, fee-schedule test, sender quality, NEAR's share
   of the fee pool, the daily aggregates and the weekly series for weeks wholly inside the window,
3. merges them over the committed outputs (older days and weeks, and the analyses that need older
   history, such as retention, keep their committed values).

The workflow then rebuilds `dashboard/live.json` from them and restores every committed file, so the
documents and `make check-clean` stay on the frozen snapshot. Without the key this exits doing nothing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pandas as pd

from . import swaps
from .ledger import OUT

DAYS = 31
COLLECT_MINUTES = 140  # a full 31-day collection took 96 min on 13 Nov 2026 (one request per 5.5 s)


def main() -> int:
    if not os.environ.get("INTENTS_JWT"):
        print("oneclick_live: no INTENTS_JWT in the environment; 1Click figures stay as committed.")
        return 0
    today = pd.Timestamp.now(tz="UTC").normalize()
    since = today - pd.Timedelta(days=DAYS)
    try:  # bounded, so a slow API day skips 1Click instead of killing the whole job (and the day's live.json)
        r = subprocess.run([sys.executable, "-m", "src.ingest.intents_explorer", "--since", since.isoformat(),
                            "--until", today.isoformat()], timeout=COLLECT_MINUTES * 60)
    except subprocess.TimeoutExpired:
        print(f"oneclick_live: collection took over {COLLECT_MINUTES} min; 1Click figures stay as committed.")
        return 0
    if r.returncode != 0:
        print("oneclick_live: collection failed; 1Click figures stay as committed.")
        return 0
    df = swaps.load()
    df = df[(df["ts"] >= since) & (df["ts"] < today)]
    if df.empty:
        print("oneclick_live: no swaps collected; 1Click figures stay as committed.")
        return 0
    print(f"oneclick_live: {len(df):,} swaps, {df['ts'].min()} to {df['ts'].max()}")

    fs = swaps.fee_shares(df)
    fs.head(25).to_csv(OUT / "fee_shares_last30d.csv")
    swaps.revenue_by_asset(df).to_csv(OUT / "revenue_by_asset_last30d.csv")
    (OUT / "oneclick_fee_policy.json").write_text(json.dumps(swaps.fee_policy(df), indent=1))
    (OUT / "oneclick_quality.json").write_text(json.dumps(swaps.quality(df), indent=1))

    nov = json.loads((OUT / "oneclick_november.json").read_text())
    last30 = swaps.november(df)["last30"]
    collected_before = nov["last30"]["swaps_collected"]
    new = int((df["ts"] > pd.Timestamp(nov["last30"]["to"], tz="UTC") + pd.Timedelta(days=1)).sum())
    last30["swaps_collected"] = collected_before + new
    nov["last30"] = last30  # the fixed October and November windows keep their committed values
    (OUT / "oneclick_november.json").write_text(json.dumps(nov, indent=1))

    daily = pd.read_csv(OUT / "oneclick_daily.csv", keep_default_na=False)
    fresh = swaps.daily_aggregates(df, start=str(since.date()))
    first = str(fresh["day"].min())
    pd.concat([daily[daily["day"] < first], fresh], ignore_index=True).to_csv(OUT / "oneclick_daily.csv", index=False)

    weekly = pd.read_csv(OUT / "swaps_weekly.csv")
    w = swaps.weekly(df)
    w = w[pd.to_datetime(w["period_start"]) >= since.tz_localize(None)]  # weeks wholly inside the window
    if not w.empty:
        keep = weekly[pd.to_datetime(weekly["period_start"]) < pd.to_datetime(w["period_start"]).min()]
        pd.concat([keep, w], ignore_index=True).to_csv(OUT / "swaps_weekly.csv", index=False)
    print(f"oneclick_live: updated through {df['ts'].max().date()}; integrators keep "
          f"{1 - last30['near_share_of_fee_pool']:.1%} of the fee pool over the last 30 days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
