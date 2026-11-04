"""Confidential intents: the channel the Explorer API does not see (data read from NEAR's own Dune queries).

Dune's free plan has no API, so the figures were read from the public result tables of @near's
"NEAR Intents" dashboard and saved as text in data/raw/dune/ (query ids in each file header).

1. Volume: public vs confidential, monthly and daily (query 5179085).
2. Does confidential volume explain the September jump in captured revenue? Weekly regression,
   no intercept: captured = a x public volume + b x confidential volume.
3. H4.1: confidential TVL around the NEAR@3.33 snapshot (query 8644298).
4. Incentive cost: Drop 1 of NEAR@3.33 (333,333 NEAR) against the revenue the channel produced.

Outputs: data/processed/confidential_weekly.csv, confidential_tvl.csv, confidential_summary.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .ledger import OUT, RAW, near_price

DUNE = RAW / "dune"
SNAPSHOT = pd.Timestamp("2026-09-16")
DROP1_NEAR = 333_333


def _tokens(path):
    return " ".join(l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")).split()


def daily_volume() -> pd.DataFrame:
    rows = []
    for t in _tokens(DUNE / "volume_daily_5179085.txt"):
        d, v = t.split(":")
        p, c = v.split("/")
        rows.append((pd.Timestamp(f"2026-{d}"), float(p) * 1e6, float(c) * 1e6))
    return pd.DataFrame(rows, columns=["date", "public_usd", "confidential_usd"]).set_index("date")


def monthly_volume() -> pd.DataFrame:
    rows = []
    for t in _tokens(DUNE / "volume_monthly_5179085.txt"):
        m, v = t.split(":")
        p, c, n = v.split("/")
        rows.append((pd.Timestamp(f"20{m}-01"), float(p) * 1e6, float(c) * 1e6, int(n)))
    df = pd.DataFrame(rows, columns=["month", "public_usd", "confidential_usd", "days"]).set_index("month")
    df["confidential_share"] = df["confidential_usd"] / (df["public_usd"] + df["confidential_usd"]).replace(0, np.nan)
    return df


def confidential_tvl() -> pd.Series:
    vals = {pd.Timestamp(f"2026-{t.split(':')[0]}"): float(t.split(":")[1]) * 1e6 for t in _tokens(DUNE / "conf_tvl_8644298.txt")}
    return pd.Series(vals, name="confidential_tvl_usd").sort_index()


def weekly_regression() -> tuple[pd.DataFrame, dict]:
    v = daily_volume()
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)
    df = v.join(rev[["rebuilt_total_usd", "rebuilt_buybacks_usd", "rebuilt_fefundsadmin_usd"]], how="inner")
    w = df.resample("W-MON", label="left", closed="left").sum()
    days = df.resample("W-MON", label="left", closed="left").size()
    w = w[days == 7]  # complete weeks only
    w["take_bps"] = w["rebuilt_total_usd"] / (w["public_usd"] + w["confidential_usd"]) * 1e4
    w["confidential_share"] = w["confidential_usd"] / (w["public_usd"] + w["confidential_usd"])
    X = w[["public_usd", "confidential_usd"]].to_numpy()
    out = {"weeks": len(w), "first_week": str(w.index.min().date()), "last_week": str(w.index.max().date())}
    for col in ("rebuilt_total_usd", "rebuilt_buybacks_usd", "rebuilt_fefundsadmin_usd"):
        y = w[col].to_numpy()
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ coef
        out[col] = {"bps_public": float(coef[0] * 1e4), "bps_confidential": float(coef[1] * 1e4),
                    "r2": float(1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())}
    out["corr_confidential_vs_buyback_wallet"] = float(w["confidential_usd"].corr(w["rebuilt_buybacks_usd"]))
    out["corr_public_vs_buyback_wallet"] = float(w["public_usd"].corr(w["rebuilt_buybacks_usd"]))
    return w, out


def h41(tvl: pd.Series) -> dict:
    at = tvl.loc[SNAPSHOT]
    later = tvl.loc[SNAPSHOT + pd.Timedelta(days=30)]
    return {"tvl_at_snapshot_usd": float(at), "tvl_30d_after_usd": float(later), "peak_usd": float(tvl.max()),
            "peak_date": str(tvl.idxmax().date()), "last_usd": float(tvl.iloc[-1]), "last_date": str(tvl.index[-1].date()),
            "rejected": bool(later > at)}


def incentive_cost(monthly: pd.DataFrame, bps_conf: float) -> dict:
    """Drop 1 cost vs. revenue from confidential volume since the program launched (2026-06-15)."""
    price = near_price()
    conv_price = float(price.loc["2026-09-21"])  # first day NEAR closed >= $3.33 three days running (proxy for the 3-day VWAP)
    m = monthly.loc["2026-06-01":"2026-10-01"].copy()
    m.loc["2026-06-01", "confidential_usd"] *= 16 / 30  # program announced 2026-06-15
    conf_vol = float(m["confidential_usd"].sum())
    fee_total = json_fees()
    return {
        "drop1_near": DROP1_NEAR, "near_price_at_conversion": conv_price,
        "drop1_usd_at_conversion": DROP1_NEAR * conv_price,
        "confidential_volume_jun15_oct_usd": conf_vol,
        "captured_from_confidential_usd_regression": conf_vol * bps_conf / 1e4,
        "all_confidential_fees_usd_dune_alltime": fee_total,
        "confidential_fee_bps_dune_alltime": fee_total / 4159967393.75 * 1e4,
    }


def json_fees() -> float:
    for line in (DUNE / "fees_totals.txt").read_text().splitlines():
        if "6162606" in line:
            return float(line.split("confidential=")[1].split()[0])
    raise ValueError("confidential fees not found")


def main() -> None:
    monthly = monthly_volume()
    tvl = confidential_tvl()
    w, reg = weekly_regression()
    summary = {
        "regression": reg,
        "h41": h41(tvl),
        "incentive": incentive_cost(monthly, reg["rebuilt_total_usd"]["bps_confidential"]),
        "monthly_confidential_share": {str(k.date())[:7]: (None if pd.isna(v) else round(float(v), 4)) for k, v in monthly["confidential_share"].items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    w.to_csv(OUT / "confidential_weekly.csv")
    tvl.to_csv(OUT / "confidential_tvl.csv")
    (OUT / "confidential_summary.json").write_text(json.dumps(summary, indent=1))
    pd.set_option("display.width", 200)
    print(monthly.loc["2026-03-01":].assign(public_musd=lambda d: d.public_usd / 1e6, conf_musd=lambda d: d.confidential_usd / 1e6)[["public_musd", "conf_musd", "confidential_share"]].round(2).to_string())
    print(w[["public_usd", "confidential_usd", "confidential_share", "rebuilt_total_usd", "take_bps"]].round(2).to_string())
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
