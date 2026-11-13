"""Pillar 1 (v2) — rebuild NEAR's captured revenue from the three revenue wallets.

revenue.near.org and DefiLlama count as revenue every NEAR / wNEAR that enters one of
three wallets from outside (internal hops between them are excluded):
  - buybacks.multisignature.near     the buyback wallet
  - fefundsadmin.sputnik-dao.near    the front-end fund (a DAO treasury)
  - 1csfundsadmin.sputnik-dao.near   the 1Click fund (a DAO treasury)
We rebuild that series from raw NearBlocks data, check it against DefiLlama,
then separate what is merely *bought* from what is *retained* in each wallet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .ledger import OUT, RAW, llama_daily, near_price

WALLETS = {
    "buybacks.multisignature.near": "buybacks",
    "fefundsadmin.sputnik-dao.near": "fefundsadmin",
    "1csfundsadmin.sputnik-dao.near": "1csfundsadmin",
}
BUYBACK_START = "2026-02-23"


def _latest(source: str):
    return json.loads(sorted((RAW / source).glob("*.json"))[-1].read_text())


def native_flows(wallet: str) -> pd.DataFrame:
    rows, seen = [], set()
    for t in _latest(f"wallet_{WALLETS[wallet]}_txns"):
        key = t["receipt_id"]
        if key in seen or t["predecessor_account_id"] == "system":
            continue
        seen.add(key)
        if not (t.get("outcomes") or {}).get("status", True):
            continue  # failed receipt: no money moved
        for a in t.get("actions") or []:
            if a.get("action") != "TRANSFER":
                continue
            near = (a.get("deposit") or 0) / 1e24
            sender, receiver = t["predecessor_account_id"], t["receiver_account_id"]
            if receiver == wallet and sender != wallet:
                rows.append((t["block_timestamp"], wallet, "in", sender, near, "NEAR"))
            elif sender == wallet and receiver != wallet:
                rows.append((t["block_timestamp"], wallet, "out", receiver, near, "NEAR"))
    return pd.DataFrame(rows, columns=["ts", "wallet", "dir", "counterparty", "amount", "token"])


def ft_flows(wallet: str) -> pd.DataFrame:
    rows = []
    for t in _latest(f"wallet_{WALLETS[wallet]}_ft"):
        ft = t.get("ft") or {}
        dec = int(ft.get("decimals") or 0)
        amount = int(float(t.get("delta_amount") or 0)) / 10**dec if dec else 0.0
        if amount == 0:
            continue
        rows.append((
            t["block_timestamp"], wallet, "in" if amount > 0 else "out",
            t.get("involved_account_id") or "", abs(amount), ft.get("symbol") or ft.get("contract") or "?",
        ))
    return pd.DataFrame(rows, columns=["ts", "wallet", "dir", "counterparty", "amount", "token"])


def all_flows() -> pd.DataFrame:
    df = pd.concat([f(w) for w in WALLETS for f in (native_flows, ft_flows)], ignore_index=True)
    df["date"] = pd.to_datetime(df.ts.astype("int64"), unit="ns").dt.normalize()
    df["internal"] = df.counterparty.isin(WALLETS)
    df["is_near"] = df.token.isin(["NEAR", "wNEAR"])
    price = near_price()
    df["usd"] = df.amount * df.date.map(price)
    df.loc[~df.is_near, "usd"] = float("nan")  # other tokens valued separately if needed
    return df


def rebuild_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Daily captured revenue per DefiLlama's definition, next to DefiLlama's own series."""
    ext_in = df[(df.dir == "in") & df.is_near & ~df.internal]
    ours = ext_in.pivot_table(index="date", columns="wallet", values="usd", aggfunc="sum").fillna(0)
    ours.columns = [f"rebuilt_{WALLETS[c]}_usd" for c in ours.columns]
    ours["rebuilt_total_usd"] = ours.sum(axis=1)
    llama = pd.concat([
        llama_daily("llama_dailyRevenue", "llama_revenue_usd"),
        llama_daily("llama_dailyHoldersRevenue", "llama_holders_revenue_usd"),
    ], axis=1, sort=True)
    out = pd.concat([ours, llama], axis=1, sort=True).fillna(0)
    out.to_csv(OUT / "revenue_rebuilt_daily.csv")
    return out


if __name__ == "__main__":
    df = all_flows()
    OUT.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["ts"]).to_csv(OUT / "revenue_wallet_flows.csv", index=False)

    print("=== Native NEAR / wNEAR flows by wallet, direction and counterparty (NEAR) ===")
    near = df[df.is_near]
    g = near.groupby(["wallet", "dir", "counterparty"])["amount"].sum().round(0)
    print(g[g.abs() >= 1].to_string())

    print("\n=== Other tokens received / sent (top) ===")
    other = df[~df.is_near]
    print(other.groupby(["wallet", "dir", "token"])["amount"].agg(["count", "sum"]).round(2)
          .sort_values("count", ascending=False).head(20).to_string())

    r = rebuild_revenue(df)
    since = r.loc[BUYBACK_START:r.index.max() - pd.Timedelta(days=1)]  # the last day of the snapshot is partial
    rb, ll = since.rebuilt_total_usd.sum(), since.llama_holders_revenue_usd.sum()
    print(f"\n=== Reconciliation from {BUYBACK_START} to {since.index.max().date()} (complete days) ===")
    print(f"rebuilt from chain : ${rb:,.0f}")
    print(f"DefiLlama holders  : ${ll:,.0f}   (ratio {rb / ll:.3f})")
    by_wallet = since[[c for c in since.columns if c.startswith('rebuilt_') and c != 'rebuilt_total_usd']].sum()
    print((by_wallet / rb).round(3).to_string())
    m = since.resample("MS")[["rebuilt_total_usd", "llama_holders_revenue_usd"]].sum()
    m["ratio"] = m.rebuilt_total_usd / m.llama_holders_revenue_usd
    print(m.round(3).to_string())
