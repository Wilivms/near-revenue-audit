"""The holder's view: what owning NEAR has cost in risk, and what it pays or dilutes per year.

Risk (daily closes, DefiLlama coins, same day-rounding as near_price): annualised volatility,
Sortino, max drawdown and days under water, 95% daily CVaR, correlation and beta to BTC
(full period and rolling 90 days).

Yield (one year, at today's price and take rate):
- issuance from archival-RPC supply (supply.py); share of supply staked from the RPC `validators` call;
- buyback "yield" = annualised NEAR captured / supply (NEAR leaving circulation if retained);
- net supply growth = issuance - buyback; staker gross reward = issuance / staked share
  (before validator commission, which typically takes 5-10% of it).

Outputs: data/processed/token_risk.csv, token_beta_rolling.csv, holder_yield.csv.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import requests

from ..ingest.sources import LLAMA_COINS, NEAR_RPC, RAW, _get, _today
from .ledger import OUT, near_price

START_UNIX = 1730419200  # 2024-11-01


def fetch_btc() -> None:
    import time
    days = int((time.time() - START_UNIX) // 86400) + 1
    prices = []
    for offset in range(0, days, 300):
        payload = _get(f"{LLAMA_COINS}/chart/coingecko:bitcoin",
                       {"start": START_UNIX + offset * 86400, "span": min(300, days - offset), "period": "1d", "searchWidth": 600})
        prices.extend(payload["coins"]["coingecko:bitcoin"]["prices"])
    unique = {round(p["timestamp"] / 86400): p for p in prices}
    folder = RAW / "btc_price"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_today()}.json").write_text(json.dumps(sorted(unique.values(), key=lambda p: p["timestamp"])))


def fetch_stake() -> None:
    r = requests.post(NEAR_RPC, json={"jsonrpc": "2.0", "id": 1, "method": "validators", "params": [None]}, timeout=60).json()
    v = r["result"]["current_validators"]
    b = requests.post(NEAR_RPC, json={"jsonrpc": "2.0", "id": 1, "method": "block", "params": {"finality": "final"}}, timeout=60).json()
    payload = {"validators": len(v), "total_stake_near": sum(int(x["stake"]) for x in v) / 1e24,
               "total_supply_near": int(b["result"]["header"]["total_supply"]) / 1e24, "block": b["result"]["header"]["height"]}
    folder = RAW / "stake"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_today()}.json").write_text(json.dumps(payload))


def _latest(source: str):
    return json.loads(sorted((RAW / source).glob("*.json"))[-1].read_text())


def btc_price() -> pd.Series:
    rows = _latest("btc_price")
    s = pd.Series({pd.to_datetime(round(p["timestamp"] / 86400) * 86400, unit="s"): p["price"] for p in rows})
    return s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D")).interpolate().rename("btc_usd")


def _metrics(r: pd.Series) -> dict:
    ann = np.sqrt(365)
    wealth = np.exp(r.cumsum())
    peak = wealth.cummax()
    dd = wealth / peak - 1
    under = (dd < 0).astype(int)
    longest = int(under.groupby((under == 0).cumsum()).sum().max())
    downside = r[r < 0].std() * ann
    q = r.quantile(0.05)
    return {
        "days": len(r),
        "total_return": float(np.exp(r.sum()) - 1),
        "annualised_vol": float(r.std() * ann),
        "sortino": float(r.mean() * 365 / downside) if downside > 0 else np.nan,
        "max_drawdown": float(dd.min()),
        "longest_underwater_days": longest,
        "daily_cvar_95": float(-r[r <= q].mean()),
    }


def risk() -> tuple[pd.DataFrame, pd.DataFrame]:
    px = pd.concat([near_price(), btc_price()], axis=1, sort=True).dropna()
    px = px[px.index < pd.Timestamp(_today())]  # complete days only
    r = np.log(px).diff().dropna()
    rows = []
    for label, start in (("since Nov 2024", r.index.min()), ("last 365 days", r.index.max() - pd.Timedelta(days=364))):
        rr = r[r.index >= start]
        for asset, col in (("NEAR", "near_usd"), ("BTC", "btc_usd")):
            m = _metrics(rr[col])
            m.update({"asset": asset, "window": label})
            if asset == "NEAR":
                m["corr_to_btc"] = float(rr["near_usd"].corr(rr["btc_usd"]))
                m["beta_to_btc"] = float(rr["near_usd"].cov(rr["btc_usd"]) / rr["btc_usd"].var())
            rows.append(m)
    roll = pd.DataFrame({
        "beta_90d": r["near_usd"].rolling(90).cov(r["btc_usd"]) / r["btc_usd"].rolling(90).var(),
        "corr_90d": r["near_usd"].rolling(90).corr(r["btc_usd"]),
        "vol_90d": r["near_usd"].rolling(90).std() * np.sqrt(365),
    }).dropna()
    return pd.DataFrame(rows), roll


def holder_yield() -> pd.DataFrame:
    stake = _latest("stake")
    sm = pd.read_csv(OUT / "supply_monthly.csv", parse_dates=["date"])
    sm = sm[sm["date"] >= "2026-02-01"]
    issuance = sm["net_issuance_near"].sum() / sm["date"].dt.days_in_month.sum() * 365 / stake["total_supply_near"]
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    price = near_price()
    last30 = rev.index.max() - pd.Timedelta(days=29)
    bought_30d_near = (rev[rev.index >= last30] / price.reindex(rev[rev.index >= last30].index)).sum()
    buyback = bought_30d_near * 365 / 30 / stake["total_supply_near"]
    staked = stake["total_stake_near"] / stake["total_supply_near"]
    rows = [
        ("NEAR issuance, % of supply a year", issuance),
        ("Buybacks at the last 30 days' pace, % of supply a year", buyback),
        ("Net supply growth, % a year", issuance - buyback),
        ("Share of supply staked", staked),
        ("Staker gross reward, % a year (before commission)", issuance / staked),
        ("Unstaked holder: change in share of supply, % a year", -(issuance - buyback)),
    ]
    return pd.DataFrame(rows, columns=["measure", "value"])


def main(refresh: bool = True) -> None:
    if refresh:
        for f in (fetch_btc, fetch_stake):
            try:
                f()
            except Exception as e:  # noqa: BLE001
                print(f"WARNING {f.__name__} failed, using the last snapshot: {e}")
    r, roll = risk()
    y = holder_yield()
    OUT.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT / "token_risk.csv", index=False)
    roll.to_csv(OUT / "token_beta_rolling.csv")
    y.to_csv(OUT / "holder_yield.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(r.round(3).to_string(index=False))
    print(roll.iloc[::30].round(2).to_string())
    print(y.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
