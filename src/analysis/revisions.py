"""Do the sources revise the past? The aggregators do; the chain does not.

Every `make refresh` keeps a dated snapshot of each source (data/raw/<source>/<date>.json), so the
same day can be read as each source reported it on several dates. This step compares them:

1. DefiLlama (NEAR Intents fees, revenue, holders revenue, volume) and NEAR's own dashboard
   (revenue.near.org: gross fees and volume): for every day reported in an earlier snapshot, how much
   the latest snapshot changed it, by the day's age when it was first read (1 = the day before the
   snapshot). A series is "settled" after k days if no day read at least k days old moved by 1% or more.
2. The revenue rebuilt here from the three revenue wallets (NearBlocks receipts): the same rebuild run
   on each dated wallet snapshot, compared day by day with the latest one, for every complete day.

So a figure built on a provisional day can be named, and the window of each headline number can be
checked against it. Output: data/processed/source_revisions.json.
"""
from __future__ import annotations

import json

import pandas as pd

from . import revenue_wallets as rw
from .ledger import OUT, RAW

LLAMA = {"llama_dailyFees": "gross fees", "llama_dailyRevenue": "revenue", "llama_dailyHoldersRevenue": "holders revenue",
         "llama_volume": "volume"}
SETTLED = 0.01  # a day counts as settled once no later snapshot moves it by 1% or more


def _dated(source: str) -> list[tuple[str, dict]]:
    return [(f.stem[:10], json.loads(f.read_text())) for f in sorted((RAW / source).glob("*.json"))]


def _llama(payload: dict) -> pd.Series:
    return pd.Series({pd.to_datetime(t, unit="s").normalize(): float(v) for t, v in payload.get("totalDataChart") or []})


def _official(payload: dict, key: str, field: str) -> pd.Series:
    return pd.Series({pd.Timestamp(r["date_at"]): float(r[field] or 0) for r in payload.get(key) or []})


def compare(snaps: dict[str, pd.Series]) -> dict:
    """Each day of each earlier snapshot against the latest snapshot, grouped by the day's age."""
    dates = sorted(snaps)
    latest = snaps[dates[-1]]
    rows = []
    for d in dates[:-1]:
        s = snaps[d]
        for day, v in s.items():
            if day not in latest.index or day >= pd.Timestamp(d):
                continue  # the snapshot's own day is always partial
            new = float(latest[day])
            rel = (new / v - 1) if v else (0.0 if new == 0 else float("inf"))
            rows.append({"snapshot": d, "day": day, "age": (pd.Timestamp(d) - day).days, "first": v, "latest": new, "rel": rel})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"pairs": 0}
    df["abs"] = df["rel"].abs()
    by_age = {}
    for age, g in df.groupby(df["age"].clip(upper=7)):
        by_age["7+" if age == 7 else str(age)] = {"pairs": len(g), "moved_1pct": int((g["abs"] >= SETTLED).sum()),
                                                 "max_abs_change": round(float(g["abs"].replace(float("inf"), 1e9).max()), 6)}
    moved = df[df["abs"] >= SETTLED]
    settled = int(moved["age"].max()) + 1 if len(moved) else 1
    big = moved.sort_values("abs", ascending=False).head(6)
    return {"pairs": len(df), "snapshots": dates, "by_age": by_age, "settled_after_days": settled,
            "largest": [{"day": str(r.day.date()), "read_on": r.snapshot, "first": round(r.first, 2), "latest": round(r.latest, 2),
                         "factor": round(r.latest / r.first, 2) if r.first else None} for r in big.itertuples()]}


def rebuilt_near(snapshot: str) -> pd.Series:
    """NEAR entering the three wallets from outside, per day, rebuilt from the wallet files dated up to `snapshot`."""
    def upto(source: str):
        files = [f for f in sorted((RAW / source).glob("*.json")) if f.stem[:10] <= snapshot]
        return json.loads(files[-1].read_text())
    keep = rw._latest
    rw._latest = upto
    try:
        df = pd.concat([f(w) for w in rw.WALLETS for f in (rw.native_flows, rw.ft_flows)], ignore_index=True)
    finally:
        rw._latest = keep
    df["date"] = pd.to_datetime(df.ts.astype("int64"), unit="ns").dt.normalize()
    ext = df[(df["dir"] == "in") & df["token"].isin(["NEAR", "wNEAR"]) & ~df["counterparty"].isin(rw.WALLETS)]
    return ext.groupby("date")["amount"].sum()


def rebuilt() -> dict:
    dates = sorted({f.stem[:10] for f in (RAW / "wallet_buybacks_txns").glob("*.json")})
    snaps = {d: rebuilt_near(d) for d in dates}
    out = compare(snaps)
    out["unit"] = "NEAR received from outside the three wallets, per day (no price involved)"
    return out


def main() -> dict:
    res = {"rule": f"a series is settled after k days if no day read at least k days old moved by {SETTLED:.0%} or more in a later snapshot",
           "defillama": {}, "near_dashboard": {}}
    for src, name in LLAMA.items():
        res["defillama"][name] = compare({d: _llama(p) for d, p in _dated(src)})
    off = _dated("near_revenue")
    res["near_dashboard"]["gross fees"] = compare({d: _official(p, "totalFeesSeries", "fees_usd") for d, p in off})
    res["near_dashboard"]["volume"] = compare({d: _official(p, "intentVolumeSeries", "volume_usd") for d, p in off})
    res["rebuilt_from_wallets"] = rebuilt()
    (OUT / "source_revisions.json").write_text(json.dumps(res, indent=1))
    fees, rb = res["defillama"]["gross fees"], res["rebuilt_from_wallets"]
    print(f"revisions: DefiLlama gross fees settle after {fees['settled_after_days']} day(s); largest change x{fees['largest'][0]['factor']} "
          f"({fees['largest'][0]['day']} read on {fees['largest'][0]['read_on']})" if fees.get("largest") else "revisions: no DefiLlama fee revisions")
    print(f"revisions: wallet rebuild, {rb['pairs']} day readings over {len(rb['snapshots'])} snapshots, "
          f"{sum(v['moved_1pct'] for v in rb['by_age'].values())} moved by 1% or more")
    return res


if __name__ == "__main__":
    main()
