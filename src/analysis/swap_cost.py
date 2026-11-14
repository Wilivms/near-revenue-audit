"""What a 1Click swap costs the user, and who gets it: integrators, NEAR, or solvers and networks.

"Follow $100" follows the fee pool. This follows the user's money: for every 1Click swap the Explorer API
reports the dollar value sent and the dollar value delivered, so the full cost of a swap is
1 - delivered / sent. The fees in the swap record split it: the integrators' app fees, NEAR's fee (the part
paid to NEAR's revenue wallets), and the rest, by difference: the solver's spread, the networks' gas and
withdrawal costs, and price moves between quote and delivery.

Two steps, like the rest of the 1Click work:
- `collect()` reads the private per-swap data (partner key) and saves only daily sums by swap size to
  data/raw/oneclick_aggregates/swap_cost_<last day>.json (`make swap-cost-collect`);
- `main()` works offline from that file (`make swap-cost`).

Swaps whose delivered value is more than 5% above or 20% below what was sent are left out as mispriced
records (0.9% of swaps, 0.001% of volume over the last 30 days).
"""
from __future__ import annotations

import glob
import json

import pandas as pd

from .ledger import OUT, RAW

FOLDER = RAW / "oneclick_aggregates"
BUCKETS = [0, 10, 30, 100, 300, 1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000, float("inf")]
LABELS = ["under $10", "$10-30", "$30-100", "$100-300", "$300-1k", "$1k-3k", "$3k-10k", "$10k-30k", "$30k-100k", "$100k-300k",
          "$300k-1M", "over $1M"]


def collect(since: str = "2026-08-14") -> dict:
    from . import swaps
    files = [f for f in sorted(glob.glob(str(swaps.DATA / "swaps_*.csv.gz"))) if f.split("swaps_")[1][:10] >= since]
    cols, real = swaps.COLS, swaps.glob.glob
    swaps.COLS = cols + ["amount_out_usd"]
    swaps.glob.glob = lambda pattern: files
    try:
        df = swaps.load()
    finally:
        swaps.COLS, swaps.glob.glob = cols, real
    df = df[df["ts"] >= since]
    df["out_usd"] = pd.to_numeric(df["amount_out_usd"], errors="coerce")
    ok = (df["usd"] > 0) & df["out_usd"].notna()
    cost = 1 - df["out_usd"] / df["usd"]
    keep = ok & (cost > -0.05) & (cost < 0.20)
    df["bucket"] = pd.cut(df["usd"], BUCKETS, labels=LABELS, right=True).astype(str)
    df["day"] = df["ts"].dt.strftime("%Y-%m-%d")
    k = df[keep]
    g = k.groupby(["day", "bucket"]).agg(swaps=("usd", "size"), in_usd=("usd", "sum"), out_usd=("out_usd", "sum"),
                                         app_fees_usd=("fee_usd", "sum"), near_usd=("near_usd", "sum")).reset_index()
    dropped = df[ok & ~keep].groupby("day").agg(swaps=("usd", "size"), in_usd=("usd", "sum")).reset_index()
    last = str(df["day"].max())
    out = {"note": "daily sums of 1Click swaps by size (NEAR Intents Explorer API); no swap, address or integrator",
           "rule": "kept if delivered value is between 5% above and 20% below the value sent",
           "rows": g.round(4).to_dict("records"), "dropped": dropped.round(4).to_dict("records"),
           "no_value": int((~ok).sum())}
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / f"swap_cost_{last}.json").write_text(json.dumps(out))
    print(f"swap_cost: saved swap_cost_{last}.json ({len(k):,} swaps kept, {int((ok & ~keep).sum()):,} left out)")
    return out


def _split(g: pd.DataFrame) -> dict:
    v = g["in_usd"].sum()
    cost, fees, near = 1 - g["out_usd"].sum() / v, g["app_fees_usd"].sum() / v, g["near_usd"].sum() / v
    return {"swaps": int(g["swaps"].sum()), "volume_usd": float(v), "cost_bps": cost * 1e4, "integrators_bps": (fees - near) * 1e4,
            "near_bps": near * 1e4, "solvers_networks_bps": (cost - fees) * 1e4, "near_share_of_cost": near / cost if cost else None}


def main() -> dict:
    f = sorted(FOLDER.glob("swap_cost_*.json"))[-1]
    agg = json.loads(f.read_text())
    d = pd.DataFrame(agg["rows"])
    end = pd.Timestamp(d["day"].max())  # collected after the day ended, as for the other 1Click outputs
    w30 = d[d["day"] >= str((end - pd.Timedelta(days=29)).date())]
    drop = pd.DataFrame(agg["dropped"])
    drop30 = drop[(drop["day"] >= str((end - pd.Timedelta(days=29)).date())) & (drop["day"] <= str(end.date()))]
    res = {"from": str((end - pd.Timedelta(days=29)).date()), "to": str(end.date()), "last30": _split(w30),
           "by_size": {b: _split(w30[w30["bucket"] == b]) for b in LABELS if (w30["bucket"] == b).any()},
           "by_month": {m: _split(g) for m, g in d.groupby(d["day"].str[:7]) if g["day"].nunique() >= 14},
           "left_out_last30": {"swaps": int(drop30["swaps"].sum()), "share_of_volume": float(drop30["in_usd"].sum() / (w30["in_usd"].sum() + drop30["in_usd"].sum()))},
           "source_file": f.name}
    (OUT / "swap_cost.json").write_text(json.dumps(res, indent=1))
    s = res["last30"]
    print(f"swap_cost: {res['from']} to {res['to']}, {s['swaps']:,} swaps: a user pays {s['cost_bps']:.1f} bps: integrators "
          f"{s['integrators_bps']:.1f}, NEAR {s['near_bps']:.1f}, solvers and networks {s['solvers_networks_bps']:.1f} "
          f"(NEAR keeps {s['near_share_of_cost']:.1%} of what users pay)")
    for b, x in res["by_size"].items():
        print(f"  {b:12s} {x['swaps']:>8,} swaps  cost {x['cost_bps']:6.1f}  integrators {x['integrators_bps']:5.1f}  NEAR {x['near_bps']:4.1f}  rest {x['solvers_networks_bps']:5.1f}")
    for m, x in res["by_month"].items():
        print(f"  {m}  cost {x['cost_bps']:6.1f}  integrators {x['integrators_bps']:5.1f}  NEAR {x['near_bps']:4.1f}  rest {x['solvers_networks_bps']:5.1f}")
    return res


if __name__ == "__main__":
    import sys
    collect() if "--collect" in sys.argv else main()
