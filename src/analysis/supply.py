"""Pillar 2 — Supply: measured issuance (archival RPC) vs buybacks (NearBlocks)."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

from .ledger import OUT

ARCHIVAL = "https://archival-rpc.mainnet.near.org"
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "raw" / "supply_history" / "blocks.json"


def _header(block_id, attempts: int = 30):
    """Block header at `block_id`. Some heights are skipped on NEAR: try the previous ones."""
    for i in range(attempts):
        params = {"finality": "final"} if block_id == "final" else {"block_id": block_id - i}
        r = requests.post(ARCHIVAL, json={"jsonrpc": "2.0", "id": 1, "method": "block", "params": params}, timeout=30)
        if r.status_code == 429:
            time.sleep(3)
            continue
        body = r.json()
        if "result" in body:
            h = body["result"]["header"]
            return {"height": h["height"], "ts": int(h["timestamp"]) / 1e9, "supply": int(h["total_supply"]) / 1e24}
        time.sleep(0.2)
    raise RuntimeError(f"No block found near {block_id}: {body.get('error')}")


def sample_supply(start: str = "2025-10-01", step_days: int = 7) -> pd.DataFrame:
    """Total supply roughly every `step_days`, found by walking block heights back from now."""
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else []
    if cache:
        # Refresh only (`make refresh` sets REFRESH=1): add the current final block when the cache is more than
        # 3 days old (issuance is close to linear, so the gap is interpolated). Offline runs never touch the
        # network or the committed snapshot, whatever the date, so `make check-clean` gives the same result.
        if os.environ.get("REFRESH") == "1" and time.time() - max(p["ts"] for p in cache) > 3 * 86400:
            try:
                cache.append(_header("final"))
                CACHE.write_text(json.dumps(cache))
            except Exception as e:  # noqa: BLE001
                print(f"WARNING supply: could not read the final block, using the cache: {e}")
        return pd.DataFrame(cache)
    now = _header("final")
    rate = 1.65  # blocks per second, refined after each sample
    points, target = [now], now["ts"]
    stop = pd.Timestamp(start).timestamp()
    while target > stop:
        target -= step_days * 86400
        guess = int(now["height"] - (now["ts"] - target) * rate)
        p = _header(guess)
        rate = (now["height"] - p["height"]) / (now["ts"] - p["ts"])
        points.append(p)
        time.sleep(0.3)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(points))
    return pd.DataFrame(points)


def monthly() -> pd.DataFrame:
    """Monthly issuance vs NEAR captured by the 3 revenue wallets (and by the buyback wallet alone)."""
    from .revenue_wallets import all_flows

    s = sample_supply()
    s["date"] = pd.to_datetime(s.ts, unit="s")
    s = s.set_index("date").sort_index()["supply"]
    daily = s.resample("D").last().interpolate()
    issuance = daily.diff().rename("net_issuance_near")

    flows = all_flows()
    ext_in = flows[(flows.dir == "in") & flows.is_near & ~flows.internal]
    captured = ext_in.groupby("date")["amount"].sum().rename("captured_near_3_wallets")
    direct = ext_in[ext_in.wallet == "buybacks.multisignature.near"].groupby("date")["amount"].sum()
    left = flows[(flows.dir == "out") & flows.is_near & ~flows.internal].groupby("date")["amount"].sum()

    df = pd.concat([issuance, captured, direct.rename("captured_near_buyback_wallet"),
                    left.rename("near_left_revenue_wallets")], axis=1, sort=True).fillna(0)
    df = df.loc[: daily.index.max()]  # only days covered by a supply reading
    m = df.resample("MS").sum().loc["2025-11-01":]
    m = m[m.index + pd.offsets.MonthEnd(0) <= daily.index.max()]  # complete months only
    m["captured_share_of_issuance"] = m.captured_near_3_wallets / m.net_issuance_near.where(m.net_issuance_near > 0)
    m["net_flow_to_market_near"] = m.net_issuance_near - m.captured_near_3_wallets + m.near_left_revenue_wallets
    m.to_csv(OUT / "supply_monthly.csv")
    return m


if __name__ == "__main__":
    m = monthly()
    print(m.round(3).to_string())
    since = m.loc["2026-02-01":]
    issued, cap = since.net_issuance_near.sum(), since.captured_near_3_wallets.sum()
    direct = since.captured_near_buyback_wallet.sum()
    print(f"\nFeb 2026 to {m.index.max():%b %Y}: issued {issued:,.0f} NEAR | captured by the 3 revenue wallets {cap:,.0f} ({cap/issued:.1%})"
          f" | of which straight into the buyback wallet {direct:,.0f} ({direct/issued:.1%})"
          f" | left the revenue wallets {since.near_left_revenue_wallets.sum():,.0f}")
