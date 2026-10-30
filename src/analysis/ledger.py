"""Pillar 1 — Ledger: reconcile reported holders revenue with on-chain buyback inflows."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
WALLET = "buybacks.multisignature.near"


def _latest(source: str):
    files = sorted((RAW / source).glob("*.json"))
    return json.loads(files[-1].read_text())


def llama_daily(source: str, column: str) -> pd.Series:
    chart = _latest(source)["totalDataChart"]
    s = pd.Series({pd.to_datetime(ts, unit="s").normalize(): v for ts, v in chart}, name=column)
    return s.sort_index()


def near_price() -> pd.Series:
    rows = _latest("near_price")
    # Round to the nearest UTC day: points sit a few seconds either side of midnight.
    s = pd.Series({pd.to_datetime(round(p["timestamp"] / 86400) * 86400, unit="s"): p["price"] for p in rows})
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    return s.reindex(full).interpolate().rename("near_usd")


def wallet_flows() -> pd.DataFrame:
    """One row per NEAR transfer into or out of the buyback wallet."""
    rows = []
    for t in _latest("buyback_txns"):
        for a in t.get("actions") or []:
            if a.get("action") != "TRANSFER" or t["predecessor_account_id"] == "system":
                continue
            near = (a.get("deposit") or 0) / 1e24
            inflow = t["receiver_account_id"] == WALLET and t["predecessor_account_id"] != WALLET
            outflow = t["predecessor_account_id"] == WALLET and t["receiver_account_id"] != WALLET
            if not (inflow or outflow):
                continue
            rows.append({
                "date": pd.to_datetime(int(t["block_timestamp"]), unit="ns").normalize(),
                "counterparty": t["predecessor_account_id"] if inflow else t["receiver_account_id"],
                "direction": "in" if inflow else "out",
                "near": near,
                "tx": t["transaction_hash"],
            })
    return pd.DataFrame(rows).drop_duplicates("tx")


def reconcile() -> pd.DataFrame:
    flows = wallet_flows()
    price = near_price()
    inflows = flows[(flows.direction == "in") & (flows.counterparty == "intents.near")]
    daily = inflows.groupby("date")["near"].sum().rename("buyback_near")

    df = pd.concat(
        [
            llama_daily("llama_dailyFees", "fees_usd"),
            llama_daily("llama_dailyRevenue", "revenue_usd"),
            llama_daily("llama_dailyHoldersRevenue", "holders_revenue_usd"),
            daily,
            price,
        ],
        axis=1,
    ).sort_index()
    df = df[df.index >= "2026-02-01"]
    df["buyback_near"] = df["buyback_near"].fillna(0)
    df[["fees_usd", "revenue_usd", "holders_revenue_usd"]] = df[
        ["fees_usd", "revenue_usd", "holders_revenue_usd"]
    ].fillna(0)
    df["buyback_usd"] = df["buyback_near"] * df["near_usd"]
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "ledger_daily.csv")
    return df


def summary(df: pd.DataFrame, flows: pd.DataFrame) -> dict:
    monthly = df.resample("MS")[["holders_revenue_usd", "buyback_usd", "buyback_near"]].sum()
    out = flows[flows.direction == "out"]
    inn = flows[flows.direction == "in"]
    first_in = inn[inn.counterparty == "intents.near"]["date"].min()
    first_rev = df[df.holders_revenue_usd > 0].index.min()
    return {
        "first_holders_revenue_day": str(first_rev.date()) if pd.notna(first_rev) else None,
        "first_intents_inflow_day": str(first_in.date()) if pd.notna(first_in) else None,
        "cum_holders_revenue_usd": round(df.holders_revenue_usd.sum()),
        "cum_buyback_usd_at_daily_price": round(df.buyback_usd.sum()),
        "cum_buyback_near": round(df.buyback_near.sum()),
        "coverage_ratio": round(df.buyback_usd.sum() / max(df.holders_revenue_usd.sum(), 1), 3),
        "inflow_counterparties": inn.groupby("counterparty")["near"].sum().round(0).to_dict(),
        "outflows_near": round(out["near"].sum(), 2),
        "outflow_counterparties": out.groupby("counterparty")["near"].sum().round(2).to_dict(),
        "monthly": monthly.round(0).reset_index().astype({"index": str}).to_dict("records")
        if "index" in monthly.reset_index().columns
        else monthly.round(0).assign(month=monthly.index.strftime("%Y-%m")).to_dict("records"),
    }


if __name__ == "__main__":
    df = reconcile()
    print(json.dumps(summary(df, wallet_flows()), indent=1, default=str))
