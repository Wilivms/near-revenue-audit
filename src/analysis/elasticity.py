"""Do 1Click volumes react to fees? Two tests, on the integrators that route through 1Click.

The take is NEAR's lever (REPORT section 2), and F18 shows NEAR keeps about 6% of what a user pays. Raising
it only works if volume does not leave. Fee changes on NEAR itself are rare and mixed with the airdrop, so
this uses the integrators, who set their own fees and sometimes change them:

1. Within an integrator: every clean step in an integrator's fee (the volume-weighted fee moves by 3 bps or
   more between two 10-day windows that are each stable) and the integrator's volume change against all
   of 1Click over the same days. Done for the integrators' app fee and for NEAR's fee on their flow.
2. Across integrators: for the integrators with $1M or more in 14 Aug-12 Sep, their fee then against how
   their volume grew by 14 Oct-12 Nov, relative to all 1Click (Spearman rank correlation).

`collect()` saves daily volume and volume-weighted fees by integrator, under a one-way pseudonym, to
data/raw/oneclick_aggregates/integrator_fees_<last day>.json (`make elasticity-collect`); `main()` runs
offline (`make elasticity`).
"""
from __future__ import annotations

import glob
import hashlib
import json

import numpy as np
import pandas as pd

from .leadlag import _p_value
from .ledger import OUT, RAW

FOLDER = RAW / "oneclick_aggregates"
WIN = 10


def collect(since: str = "2026-08-14") -> dict:
    from . import swaps
    files = [f for f in sorted(glob.glob(str(swaps.DATA / "swaps_*.csv.gz"))) if f.split("swaps_")[1][:10] >= since]
    real = swaps.glob.glob
    swaps.glob.glob = lambda pattern: files
    try:
        df = swaps.load()
    finally:
        swaps.glob.glob = real
    df = df[(df["ts"] >= since) & (df["ref"] != "(none)")]
    df["day"] = df["ts"].dt.strftime("%Y-%m-%d")
    df["fee_x"] = df["total_bps"] * df["usd"]
    df["near_x"] = df["near_bps"] * df["usd"]
    g = df.groupby(["ref", "day"]).agg(usd=("usd", "sum"), fee_x=("fee_x", "sum"), near_x=("near_x", "sum"), swaps=("usd", "size")).reset_index()
    g["id"] = g["ref"].map(lambda r: hashlib.sha256(f"near-revenue-audit:{r}".encode()).hexdigest()[:10])
    rows = [[r.day, r.id, round(r.usd, 2), round(r.fee_x / r.usd, 3) if r.usd else None, round(r.near_x / r.usd, 3) if r.usd else None, int(r.swaps)]
            for r in g.itertuples()]
    last = str(df["day"].max())
    out = {"note": "daily 1Click volume and volume-weighted fees (bps: all app fees, NEAR's part) by integrator under a one-way pseudonym",
           "columns": ["day", "id", "usd", "fee_bps", "near_bps", "swaps"], "rows": rows}
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / f"integrator_fees_{last}.json").write_text(json.dumps(out))
    print(f"elasticity: saved integrator_fees_{last}.json ({len(rows):,} integrator-days)")
    return out


def _steps(p: pd.DataFrame, total: pd.Series, col: str, days: list[str]) -> list[dict]:
    out = []
    for iid, x in p.groupby("id"):
        x = x.set_index("day").reindex(days)
        if x["usd"].sum() < 500_000:
            continue
        best = None
        for i in range(WIN, len(days) - WIN):
            pre, post = x.iloc[i - WIN:i], x.iloc[i:i + WIN]
            if pre["usd"].notna().sum() < 7 or post["usd"].notna().sum() < 7:
                continue
            fpre = float((pre[col] * pre["usd"]).sum() / pre["usd"].sum())
            fpost = float((post[col] * post["usd"]).sum() / post["usd"].sum())
            d = fpost - fpre
            tol = 0.25 * abs(d) + 0.5
            if abs(d) >= 3 and pre[col].std() < tol and post[col].std() < tol and (best is None or abs(d) > abs(best["fee_change_bps"])):
                rel = np.log(post["usd"].sum() / pre["usd"].sum()) - np.log(total.iloc[i:i + WIN].sum() / total.iloc[i - WIN:i].sum())
                best = {"id": iid, "day": days[i], "fee_before_bps": fpre, "fee_change_bps": d, "volume_before_usd": float(pre["usd"].sum()),
                        "relative_volume_change": float(np.expm1(rel))}
        if best:
            out.append(best)
    return out


def main() -> dict:
    f = sorted(FOLDER.glob("integrator_fees_*.json"))[-1]
    agg = json.loads(f.read_text())
    p = pd.DataFrame(agg["rows"], columns=agg["columns"])
    days = list(pd.date_range(p["day"].min(), p["day"].max()).strftime("%Y-%m-%d"))
    total = p.groupby("day")["usd"].sum().reindex(days).fillna(0)
    within = {"app_fee": _steps(p, total, "fee_bps", days), "near_fee": _steps(p, total, "near_bps", days)}
    a = p[(p["day"] >= "2026-08-14") & (p["day"] <= "2026-09-12")]
    b = p[(p["day"] >= "2026-10-14") & (p["day"] <= "2026-11-12")]
    A = a.groupby("id").apply(lambda x: pd.Series({"usd": x["usd"].sum(), "fee": (x["fee_bps"] * x["usd"]).sum() / x["usd"].sum()}))
    A = A[A["usd"] >= 1e6]
    A["after"] = b.groupby("id")["usd"].sum().reindex(A.index).fillna(0)
    A["growth"] = np.log((A["after"] + 1e4) / (A["usd"] + 1e4)) - np.log(b["usd"].sum() / a["usd"].sum())
    rho = float(A["fee"].rank().corr(A["growth"].rank()))  # Spearman: Pearson on ranks (no scipy needed)
    pv = _p_value(rho, len(A))
    bands = pd.cut(A["fee"], [-1, 10, 30, 60, 10_000], labels=["0-10 bps", "10-30 bps", "30-60 bps", "60+ bps"])
    by = {str(k): {"integrators": int(len(g)), "volume_before_usd": float(g["usd"].sum()), "median_relative_growth": float(np.expm1(g["growth"].median()))}
          for k, g in A.groupby(bands, observed=True)}
    ups = [e for k in within for e in within[k] if e["fee_change_bps"] > 0]
    downs = [e for k in within for e in within[k] if e["fee_change_bps"] < 0]
    res = {"within": within, "fee_rises": len(ups), "fee_cuts": len(downs),
           "fee_rises_median_volume": float(np.median([e["relative_volume_change"] for e in ups])) if ups else None,
           "fee_cuts_median_volume": float(np.median([e["relative_volume_change"] for e in downs])) if downs else None,
           "cross_section": {"integrators": int(len(A)), "spearman": float(rho), "p": float(pv), "by_fee_band": by},
           "note": "few clean fee steps; volumes move with bursts and deals far more than with fees of this size"}
    (OUT / "elasticity.json").write_text(json.dumps(res, indent=1))
    print(f"elasticity: {len(ups)} fee rises (median relative volume {res['fee_rises_median_volume']:+.0%}), {len(downs)} cuts "
          f"(median {res['fee_cuts_median_volume']:+.0%}); across {len(A)} integrators, fee vs growth Spearman {rho:+.2f} (p = {pv:.2f})")
    for k, v in by.items():
        print(f"  {k:10s} {v['integrators']:3d} integrators  ${v['volume_before_usd'] / 1e6:7.1f}M  median growth vs 1Click {v['median_relative_growth']:+.0%}")
    return res


if __name__ == "__main__":
    import sys
    collect() if "--collect" in sys.argv else main()
