"""Relative valuation: NEAR against tokens whose holders receive protocol revenue (buybacks, burns, fee share).

Multiple = market cap / annualised holders revenue (last 30 days x 365/30), both from public APIs:
- holders revenue: DefiLlama /overview/fees?dataType=dailyHoldersRevenue, summed over each parent protocol;
- market cap: CoinGecko /coins/markets (circulating), with fully diluted value for reference.

Also: NEAR Intents' share of volume among cross-chain swap venues that report to DefiLlama.

Snapshots go to data/raw/comps/<date>.json so the table can be re-run offline.
Output: data/processed/comps.csv, data/processed/crosschain_share.csv.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests

from ..ingest.sources import RAW, _today
from .ledger import OUT

# token id on CoinGecko -> DefiLlama parent protocol (holders revenue is reported per sub-protocol)
PEERS = {
    "near": "parent#near-protocol",
    "hyperliquid": "parent#hyperliquid",
    "pump-fun": "parent#pump",
    "uniswap": "parent#uniswap",
    "aave": "parent#aave",
    "sky": "parent#maker",
    "jupiter-exchange-solana": "parent#jupiter",
    "pancakeswap-token": "parent#pancakeswap",
    "aerodrome-finance": "parent#aero-protocol",
    "curve-dao-token": "parent#curve-finance",
    "raydium": "parent#raydium",
    "lido-dao": "parent#lido",
    "thorchain": "parent#thorchain",
    "jito-governance-token": "parent#jito",
    "dydx-chain": "parent#dydx",
    "gmx": "parent#gmx",
    "chainflip": "parent#chainflip",
    "ethena": "parent#ethena",
}
# Cross-chain swap venues on DefiLlama's dexs dashboard (native-asset swaps across chains)
CROSSCHAIN = ["near-intents", "thorchain-dex", "chainflip-amm", "maya-protocol"]


def _get(url: str, params: dict | None = None, retries: int = 4):
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(url)


def fetch() -> dict:
    hr = _get("https://api.llama.fi/overview/fees", {"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true",
                                                      "dataType": "dailyHoldersRevenue"})
    mc = _get("https://api.coingecko.com/api/v3/coins/markets", {"vs_currency": "usd", "ids": ",".join(PEERS)})
    vols = {}
    for slug in CROSSCHAIN:
        try:
            vols[slug] = _get(f"https://api.llama.fi/summary/dexs/{slug}", {"excludeTotalDataChartBreakdown": "true"})["totalDataChart"]
        except Exception as e:  # a venue missing from DefiLlama is skipped, and noted in the output
            vols[slug] = {"error": str(e)}
        time.sleep(1)
    payload = {
        "holders_revenue": [{k: p.get(k) for k in ("name", "parentProtocol", "category", "total30d", "total1y")} for p in hr["protocols"]],
        "markets": [{k: m.get(k) for k in ("id", "symbol", "market_cap", "fully_diluted_valuation", "current_price")} for m in mc],
        "crosschain_volume": vols,
    }
    folder = RAW / "comps"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_today()}.json").write_text(json.dumps(payload))
    return payload


def latest() -> dict:
    return json.loads(sorted((RAW / "comps").glob("*.json"))[-1].read_text())


def comps(payload: dict) -> pd.DataFrame:
    hr = pd.DataFrame(payload["holders_revenue"])
    by_parent = hr.groupby("parentProtocol")["total30d"].sum()
    rows = []
    for m in payload["markets"]:
        parent = PEERS[m["id"]]
        rev30 = float(by_parent.get(parent, 0.0) or 0.0)
        annual = rev30 * 365 / 30
        rows.append({
            "token": m["symbol"].upper(), "market_cap_usd": m["market_cap"], "fdv_usd": m["fully_diluted_valuation"],
            "holders_revenue_30d_usd": rev30, "annualised_usd": annual,
            "mcap_to_holders_revenue": m["market_cap"] / annual if annual > 0 else None,
            "fdv_to_holders_revenue": (m["fully_diluted_valuation"] or m["market_cap"]) / annual if annual > 0 else None,
        })
    return pd.DataFrame(rows).sort_values("mcap_to_holders_revenue", na_position="last")


def crosschain_share(payload: dict) -> pd.DataFrame:
    frames = {}
    for slug, chart in payload["crosschain_volume"].items():
        if isinstance(chart, list):
            frames[slug] = pd.Series({pd.to_datetime(ts, unit="s"): v for ts, v in chart})
    df = pd.DataFrame(frames).fillna(0.0)
    m = df.resample("MS").sum()
    m = m[m.index >= "2025-06-01"]
    share = m.div(m.sum(axis=1), axis=0)
    share.columns = [f"{c}_share" for c in share.columns]
    return pd.concat([m, share], axis=1)


def main(refresh: bool | None = None) -> None:
    # offline by default: `make comps` reads the committed snapshot; `make refresh` (REFRESH=1) fetches a new one
    refresh = os.environ.get("REFRESH") == "1" if refresh is None else refresh
    try:
        payload = fetch() if refresh else latest()
    except Exception as e:  # noqa: BLE001
        print(f"WARNING comps fetch failed, using the last snapshot: {e}")
        payload = latest()
    c = comps(payload)
    s = crosschain_share(payload)
    OUT.mkdir(parents=True, exist_ok=True)
    c.to_csv(OUT / "comps.csv", index=False)
    s.to_csv(OUT / "crosschain_share.csv")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    show = c.copy()
    for col in ("market_cap_usd", "fdv_usd", "holders_revenue_30d_usd", "annualised_usd"):
        show[col] = (show[col] / 1e6).round(1)
    print(show.round(1).to_string(index=False))
    print(s.filter(like="_share").round(3).to_string())


if __name__ == "__main__":
    main()
