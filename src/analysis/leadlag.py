"""The track's own hypothesis: is NEAR Intents volume a better signal of real usage than price?

Two questions, on weekly data (Monday to Sunday, complete weeks only):

1. Does usage lead the price? Correlation between this week's change in a usage series and the
   change in NEAR's price k weeks later (k = 1..4), with NEAR's price adjusted for BTC (the residual
   of a regression on BTC returns), so a market-wide move does not count as a NEAR signal.
   Usage series: NEAR Intents volume (DefiLlama), L1 transactions and L1 active accounts (NearBlocks).
   Twelve tests in total, Holm-corrected. The reverse direction (price leading usage) is tested too.
2. Which series tracks NEAR's captured revenue? Correlation of weekly changes with the weekly
   change in revenue reaching the three wallets (since the fee switch).

p-values: two-sided, from the t distribution of a Pearson correlation; with overlapping weekly
changes and few points they are indicative, which is why Holm's correction is applied.

Inputs: data/raw/llama_volume, near_price, btc_price, nearblocks_charts (fetched by `fetch()`).
Output: data/processed/leadlag.csv, leadlag_summary.json.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
import pandas as pd
import requests

from ..ingest.sources import RAW, _today
from .ledger import OUT, llama_daily, near_price

LAGS = (1, 2, 3, 4)
START = "2024-11-04"  # first Monday with BTC and NEAR prices in the snapshots


def fetch() -> None:
    r = requests.get("https://api.nearblocks.io/v1/charts", timeout=120)
    r.raise_for_status()
    rows = [{k: x[k] for k in ("date", "txns", "active_accounts", "new_accounts", "txn_fee_usd")} for x in r.json()["charts"]]
    folder = RAW / "nearblocks_charts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_today()}.json").write_text(json.dumps(rows))


def _btc() -> pd.Series:
    rows = json.loads(sorted((RAW / "btc_price").glob("*.json"))[-1].read_text())
    s = pd.Series({pd.to_datetime(round(p["timestamp"] / 86400) * 86400, unit="s"): p["price"] for p in rows})
    return s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D")).interpolate()


def _chain() -> pd.DataFrame:
    rows = json.loads(sorted((RAW / "nearblocks_charts").glob("*.json"))[-1].read_text())
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df[["txns", "active_accounts"]].astype(float)


def _p_value(r: float, n: int) -> float:
    if n < 4 or abs(r) >= 1:
        return 0.0 if abs(r) >= 1 else 1.0
    t = r * math.sqrt((n - 2) / (1 - r * r))
    # two-sided p from Student's t via the regularized incomplete beta (no scipy dependency)
    x = (n - 2) / (n - 2 + t * t)
    return float(_betainc((n - 2) / 2, 0.5, x))


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b), continued fraction (Numerical Recipes 6.4)."""
    if x <= 0 or x >= 1:
        return 0.0 if x <= 0 else 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x > (a + 1) / (a + b + 2):
        return 1 - _betainc(b, a, 1 - x)
    c, d = 1.0, 1 - (a + b) * x / (a + 1)
    d = 1 / d if abs(d) > 1e-30 else 1e30
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for num in (m * (b - m) * x / ((a + m2 - 1) * (a + m2)), -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))):
            d = 1 + num * d
            d = 1 / d if abs(d) > 1e-30 else 1e30
            c = 1 + num / c if abs(1 + num / c) > 1e-30 else 1e-30
            h *= d * c
    return math.exp(lbeta) * h / a


def _holm(p: list[float]) -> list[float]:
    order = np.argsort(p)
    adj, running = [0.0] * len(p), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj


def weekly() -> pd.DataFrame:
    vol = llama_daily("llama_volume", "intents_volume")
    px, btc, chain = near_price(), _btc(), _chain()
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    d = pd.concat([vol, px.rename("near"), btc.rename("btc"), chain, rev.rename("revenue")], axis=1).loc[START:]
    end = min(vol.index.max(), px.index.max(), chain.index.max())
    d = d.loc[:end]
    sums = d[["intents_volume", "txns", "active_accounts", "revenue"]].resample("W-MON", label="left", closed="left").sum(min_count=7)
    last = d[["near", "btc"]].resample("W-MON", label="left", closed="left").last()
    n_days = d["near"].resample("W-MON", label="left", closed="left").count()
    w = pd.concat([sums, last], axis=1)[n_days == 7]
    g = np.log(w.replace(0, np.nan)).diff()
    beta = g["near"].cov(g["btc"]) / g["btc"].var()
    g["near_vs_btc"] = g["near"] - beta * g["btc"]
    g.attrs["beta"] = float(beta)
    return g.dropna(subset=["intents_volume", "near_vs_btc"])


def tests(g: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for series in ("intents_volume", "txns", "active_accounts"):
        for k in LAGS:
            for direction, x, y in (("usage leads price", g[series], g["near_vs_btc"].shift(-k)),
                                    ("price leads usage", g["near_vs_btc"], g[series].shift(-k))):
                xy = pd.concat([x, y], axis=1).dropna()
                r = float(xy.iloc[:, 0].corr(xy.iloc[:, 1]))
                rows.append({"series": series, "direction": direction, "lag_weeks": k, "n": len(xy), "r": r, "p": _p_value(r, len(xy))})
    t = pd.DataFrame(rows)
    t["p_holm"] = np.nan
    for direction in t.direction.unique():
        idx = t.index[t.direction == direction]
        t.loc[idx, "p_holm"] = _holm(t.loc[idx, "p"].tolist())
    return t


def tracking(g: pd.DataFrame) -> dict:
    s = g.loc["2026-03-02":].dropna(subset=["revenue"])
    return {c: float(s[c].corr(s["revenue"])) for c in ("intents_volume", "txns", "active_accounts", "near_vs_btc")} | {"weeks": len(s)}


def main(refresh: bool = False) -> None:
    if refresh:
        try:
            fetch()
        except Exception as e:  # noqa: BLE001
            print(f"WARNING NearBlocks charts fetch failed, using the last snapshot: {e}")
    g = weekly()
    t = tests(g)
    chain = _chain()
    yoy = lambda s: float(s.iloc[-30:].sum() / s.iloc[-395:-365].sum() - 1)  # noqa: E731
    vol = llama_daily("llama_volume", "v")
    summary = {
        "weeks": len(g), "first_week": str(g.index.min().date()), "last_week": str(g.index.max().date()), "beta_near_btc": g.attrs["beta"],
        "significant_after_holm": int((t.p_holm < 0.05).sum()), "tests": len(t),
        "best_usage_leads_price": t[t.direction == "usage leads price"].sort_values("p").iloc[0][["series", "lag_weeks", "r", "p", "p_holm"]].to_dict(),
        "tracks_captured_revenue_weekly_r": tracking(g),
        "yoy_30d": {"intents_volume": yoy(vol.loc[:chain.index.max()]), "l1_txns": yoy(chain["txns"]), "l1_active_accounts": yoy(chain["active_accounts"])},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "leadlag.csv", index=False)
    (OUT / "leadlag_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(t.round(3).to_string(index=False))
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main(refresh="--refresh" in sys.argv)
