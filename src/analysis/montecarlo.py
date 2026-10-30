"""Pillar 5 — Valuation: does NEAR become net deflationary before end-2027? (H5.1)

Model, one path = one possible future from 2026-11-01 to 2027-12-31:
- Intents daily volume and the NEAR price move together. Their daily log changes are drawn by
  **joint block bootstrap** from history (30-day blocks), which keeps the volatility, the
  autocorrelation and the volume–price correlation seen in the data.
- NEAR captured per day = volume × take rate / price. The take rate is a scenario input
  (captured revenue in bps of volume), because it moved by 2x in 2026 for reasons not yet confirmed.
- Issuance = measured net issuance rate (archival-RPC supply, Feb–Oct 2026) × current supply.
- A month is net deflationary when NEAR captured > NEAR issued that month.

Identity used as a check: captured NEAR / issued NEAR = annual captured revenue / (rate × market cap).
NEAR is net deflationary iff market cap / annual captured revenue < 1 / rate (≈ 40x).

Outputs (data/processed/): montecarlo_scenarios.csv (one row per scenario),
montecarlo_paths_base.csv (monthly quantiles of the base case),
montecarlo_paths_all.csv (monthly quantiles of every scenario) and
montecarlo_sensitivity.csv (volume x take rate table at today's price).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .ledger import OUT, RAW, llama_daily, near_price

START = pd.Timestamp("2026-11-01")
END = pd.Timestamp("2027-12-31")
BLOCK = 30
N_PATHS = 10_000
SEED = 20261101


@dataclass
class Scenario:
    name: str
    take_bps: float              # NEAR captured, bps of total Intents volume
    window_days: int | None      # history used for the bootstrap (None = since 2025-03-01)
    demean_volume: bool = False  # remove the historical volume drift, keep its volatility
    demean_price: bool = True    # no price drift by default: the model is not a price forecast
    retired_share: float = 1.0   # share of captured NEAR counted as retired (buyback wallet ≈ 0.6)


def history() -> pd.DataFrame:
    vol = llama_daily("llama_volume", "volume_usd")
    price = near_price()
    df = pd.concat([vol, price], axis=1, sort=True).dropna()
    df = df[df.index >= "2025-03-01"]
    # 7-day mean volume: daily volume is spiky (whale swaps), the smoothed series is what persists.
    df["volume_7d"] = df["volume_usd"].rolling(7).mean()
    df = df.dropna()
    df["dlog_vol"] = np.log(df["volume_7d"]).diff()
    df["dlog_price"] = np.log(df["near_usd"]).diff()
    return df.dropna()


def calibration() -> dict:
    """Starting point and issuance rate, all from committed data."""
    h = history()
    supply = json.loads(sorted((RAW / "chain_state").glob("*.json"))[-1].read_text())
    sm = pd.read_csv(OUT / "supply_monthly.csv", parse_dates=["date"])
    sm = sm[sm["date"] >= "2026-02-01"]
    days = sm["date"].dt.days_in_month.sum()
    issuance_per_day = sm["net_issuance_near"].sum() / days
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    last30 = h.index[-30:]
    take_last30 = rev.reindex(last30).sum() / h.loc[last30, "volume_usd"].sum() * 1e4
    mayaug = h.loc["2026-05-01":"2026-08-31"].index
    take_mayaug = rev.reindex(mayaug).sum() / h.loc[mayaug, "volume_usd"].sum() * 1e4
    supply0 = supply["total_supply_near"]
    return {
        "volume0": float(h["volume_7d"].iloc[-30:].mean()),
        "price0": float(h["near_usd"].iloc[-1]),
        "supply0": supply0,
        "issuance_rate": issuance_per_day * 365 / supply0,
        "take_last30_bps": float(take_last30),
        "take_mayaug_bps": float(take_mayaug),
        "history_end": str(h.index[-1].date()),
    }


def simulate(sc: Scenario, cal: dict, n_paths: int = N_PATHS, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    h = history()
    if sc.window_days:
        h = h.iloc[-sc.window_days:]
    steps = h[["dlog_vol", "dlog_price"]].to_numpy().copy()
    if sc.demean_volume:
        steps[:, 0] -= steps[:, 0].mean()
    if sc.demean_price:
        steps[:, 1] -= steps[:, 1].mean()
    dates = pd.date_range(START, END, freq="D")
    n_days = len(dates)
    n_blocks = -(-n_days // BLOCK)
    starts = rng.integers(0, len(steps) - BLOCK, size=(n_paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(n_paths, -1)[:, :n_days]
    draws = steps[idx]                                    # (paths, days, 2)
    log_vol = np.log(cal["volume0"]) + np.cumsum(draws[:, :, 0], axis=1)
    log_px = np.log(cal["price0"]) + np.cumsum(draws[:, :, 1], axis=1)
    vol, px = np.exp(log_vol), np.exp(log_px)
    captured = vol * sc.take_bps / 1e4 / px * sc.retired_share   # NEAR per day
    issued = cal["supply0"] * cal["issuance_rate"] / 365          # NEAR per day (supply drift < 0.3%/yr ignored)

    month = dates.to_period("M")
    months = month.unique()
    cap_m = np.stack([captured[:, month == m].sum(axis=1) for m in months], axis=1)
    iss_m = np.array([issued * (month == m).sum() for m in months])
    ratio = cap_m / iss_m                                          # (paths, months)
    defl = ratio > 1
    y2027 = np.array([m.year == 2027 for m in months])
    first = np.where(defl.any(axis=1), defl.argmax(axis=1), -1)
    median_ratio = np.median(ratio, axis=0)
    return {
        "scenario": sc,
        "months": months,
        "ratio": ratio,
        "summary": {
            **asdict(sc),
            "median_offset_2027": float(np.median(cap_m[:, y2027].sum(axis=1) / iss_m[y2027].sum())),
            "p10_offset_2027": float(np.quantile(cap_m[:, y2027].sum(axis=1) / iss_m[y2027].sum(), 0.10)),
            "p90_offset_2027": float(np.quantile(cap_m[:, y2027].sum(axis=1) / iss_m[y2027].sum(), 0.90)),
            "p_any_deflationary_month": float(defl.any(axis=1).mean()),
            "p_2027_net_deflationary": float((cap_m[:, y2027].sum(axis=1) > iss_m[y2027].sum()).mean()),
            "median_path_deflationary_month": str(months[np.argmax(median_ratio > 1)]) if (median_ratio > 1).any() else "",
            "median_first_deflationary_month": str(months[int(np.median(first[first >= 0]))]) if (first >= 0).any() else "",
            "median_volume_dec2027_musd": float(np.median(vol[:, -31:].mean(axis=1)) / 1e6),
            "median_net_supply_change_m_near": float(np.median(iss_m.sum() - cap_m.sum(axis=1)) / 1e6),
        },
    }


def scenarios(cal: dict) -> list[Scenario]:
    now, low = round(cal["take_last30_bps"], 2), round(cal["take_mayaug_bps"], 2)
    return [
        Scenario("base: take now, 365d history", now, 365),
        Scenario("take back to May–Aug level", low, 365),
        Scenario("take now, zero volume drift", now, 365, demean_volume=True),
        Scenario("take now, 180d history (bull)", now, 180),
        Scenario("take now, full history since Mar-2025 (hyper-growth)", now, None),
        Scenario("take now, price keeps its 365d drift", now, 365, demean_price=False),
        Scenario("base, buyback wallet only counted as retired", now, 365, retired_share=0.6),
        Scenario("take doubles again (11 bps)", round(2 * now, 2), 365),
    ]


def sensitivity(cal: dict) -> pd.DataFrame:
    """Two-way table, no randomness: share of issuance offset at today's price,
    for a given daily volume and take rate (the identity behind the simulation)."""
    issued_per_day = cal["supply0"] * cal["issuance_rate"] / 365
    vols = [135, 250, 500, 750, 1000, 1500]
    takes = [round(cal["take_mayaug_bps"], 1), round(cal["take_last30_bps"], 1), 8.0, 11.0, 15.0]
    grid = {f"{t} bps": [v * 1e6 * t / 1e4 / cal["price0"] / issued_per_day for v in vols] for t in takes}
    return pd.DataFrame(grid, index=pd.Index([f"${v}M/day" for v in vols], name="volume"))


def main() -> None:
    cal = calibration()
    print("calibration:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in cal.items()})
    print(f"identity check: deflation needs mcap / annual captured revenue < {1 / cal['issuance_rate']:.1f}x")
    rows, base, paths = [], None, []
    for sc in scenarios(cal):
        res = simulate(sc, cal)
        rows.append(res["summary"])
        base = base or res
        qs = np.quantile(res["ratio"], [0.1, 0.5, 0.9], axis=0)
        paths.append(pd.DataFrame({"scenario": sc.name, "month": res["months"].astype(str),
                                   "p10": qs[0], "median": qs[1], "p90": qs[2]}))
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "montecarlo_scenarios.csv", index=False)
    q = np.quantile(base["ratio"], [0.1, 0.5, 0.9], axis=0)
    pd.DataFrame({"month": base["months"].astype(str), "p10": q[0], "median": q[1], "p90": q[2]}) \
        .to_csv(OUT / "montecarlo_paths_base.csv", index=False)
    pd.concat(paths).to_csv(OUT / "montecarlo_paths_all.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 20)
    cols = ["name", "take_bps", "median_offset_2027", "p10_offset_2027", "p90_offset_2027",
            "p_any_deflationary_month", "p_2027_net_deflationary", "median_path_deflationary_month",
            "median_volume_dec2027_musd", "median_net_supply_change_m_near"]
    print(out[cols].round(3).to_string(index=False))
    sens = sensitivity(cal)
    sens.to_csv(OUT / "montecarlo_sensitivity.csv")
    print(f"share of issuance offset at today's price (${cal['price0']:.2f}); >= 1.00 means net deflationary:")
    print(sens.round(2).to_string())
    print("base case, captured / issued by month (p10, median, p90):")
    print(pd.DataFrame(q.T, index=base["months"].astype(str), columns=["p10", "median", "p90"]).round(3).to_string())


if __name__ == "__main__":
    main()
