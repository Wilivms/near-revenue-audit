"""Data ingestion for the NEAR Revenue Audit.

Every fetch writes a dated raw snapshot to data/raw/<source>/<YYYY-MM-DD>.json
so the analysis can be re-run on exactly the same data (reproducibility).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

LLAMA = "https://api.llama.fi"
LLAMA_COINS = "https://coins.llama.fi"
NEAR_RPC = "https://rpc.mainnet.near.org"
NEARBLOCKS = "https://api.nearblocks.io/v1"

BUYBACK_WALLET = "buybacks.multisignature.near"
YOCTO = 10**24


def load_env(path: Path = ROOT / ".env") -> None:
    """Load KEY=value lines from .env into os.environ (the file is git-ignored)."""
    import os

    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def intents_jwt() -> str:
    """Partner JWT for the NEAR Intents Explorer API, read from the environment."""
    import os

    load_env()
    token = os.environ.get("INTENTS_JWT")
    if not token:
        raise RuntimeError(
            "INTENTS_JWT is missing. Create a .env file at the repo root containing "
            "INTENTS_JWT=<your key> (see .env.example)."
        )
    return token


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _save(source: str, payload, name: str | None = None) -> Path:
    folder = RAW / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name or _today()}.json"
    path.write_text(json.dumps(payload))
    return path


def _get(url: str, params: dict | None = None, retries: int = 7):
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(min(60, 5 * 2 ** attempt))  # shared CI runners hit rate limits: back off harder
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Rate limited too many times: {url}")


def _rpc(method: str, params):
    r = requests.post(
        NEAR_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["result"]


# --- DefiLlama -------------------------------------------------------------

def fetch_llama_intents() -> dict[str, Path]:
    """Daily fees, revenue, holders revenue, volume and TVL of NEAR Intents."""
    out = {}
    for data_type in ("dailyFees", "dailyRevenue", "dailyHoldersRevenue"):
        payload = _get(f"{LLAMA}/summary/fees/near-intents", {"dataType": data_type})
        out[data_type] = _save(f"llama_{data_type}", payload)
    out["volume"] = _save("llama_volume", _get(f"{LLAMA}/summary/dexs/near-intents"))
    out["tvl"] = _save("llama_tvl", _get(f"{LLAMA}/protocol/near-intents"))
    return out


def fetch_near_prices(start_unix: int = 1730419200, span_days: int | None = None) -> Path:
    """Daily NEAR/USD price from DefiLlama coins (CoinGecko id)."""
    days = span_days or int((time.time() - start_unix) // 86400) + 1
    prices, chunk = [], 300  # the endpoint rejects long spans
    for offset in range(0, days, chunk):
        payload = _get(
            f"{LLAMA_COINS}/chart/coingecko:near",
            {"start": start_unix + offset * 86400, "span": min(chunk, days - offset), "period": "1d",
             "searchWidth": 600},
        )
        prices.extend(payload["coins"]["coingecko:near"]["prices"])
    # Points land a few seconds either side of midnight (e.g. 23:59:59): round to the nearest
    # UTC day, otherwise two points collide on one day and the next day is left empty.
    unique = {round(p["timestamp"] / 86400): p for p in prices}  # one point per UTC day
    return _save("near_price", sorted(unique.values(), key=lambda p: p["timestamp"]))


# --- NEAR RPC --------------------------------------------------------------

def fetch_chain_state() -> Path:
    """Current total supply, inflation parameters and buyback wallet balance."""
    block = _rpc("block", {"finality": "final"})["header"]
    config = _rpc("EXPERIMENTAL_protocol_config", {"finality": "final"})
    wallet = _rpc(
        "query",
        {"request_type": "view_account", "finality": "final", "account_id": BUYBACK_WALLET},
    )
    payload = {
        "block_height": block["height"],
        "timestamp_ns": int(block["timestamp"]),
        "total_supply_near": int(block["total_supply"]) / YOCTO,
        "max_inflation_rate": config["max_inflation_rate"],
        "protocol_reward_rate": config["protocol_reward_rate"],
        "epoch_length": config["epoch_length"],
        "buyback_wallet_near": int(wallet["amount"]) / YOCTO,
    }
    return _save("chain_state", payload)


def fetch_wallet_state() -> Path:
    """Balance and staked ("locked") NEAR of the three revenue wallets: is bought NEAR staked or locked?"""
    rows = {}
    for account in REVENUE_WALLETS:
        a = _rpc("query", {"request_type": "view_account", "finality": "final", "account_id": account})
        rows[account] = {"block_height": a["block_height"], "liquid_near": int(a["amount"]) / YOCTO, "staked_near": int(a["locked"]) / YOCTO}
    return _save("wallet_state", rows)


# --- NearBlocks ------------------------------------------------------------

# NEAR's three revenue wallets, as listed by revenue.near.org and DefiLlama's adapter.
REVENUE_WALLETS = [
    "buybacks.multisignature.near",
    "fefundsadmin.sputnik-dao.near",
    "1csfundsadmin.sputnik-dao.near",
]


def _row_key(row: dict) -> str:
    # 'txns' rows are receipts (receipt_id); 'ft-txns' rows are token events (event_index)
    return str(row.get("receipt_id") or row.get("event_index") or row.get("id"))


def _previous(source: str) -> list | None:
    files = sorted((RAW / source).glob("*.json"))
    return json.loads(files[-1].read_text()) if files else None


def fetch_account_history(account: str, kind: str = "txns", per_page: int = 25, max_pages: int = 1000,
                          known: list | None = None) -> list:
    """NearBlocks history of an account, oldest first. kind: 'txns' or 'ft-txns'.

    With `known` (the last snapshot), only pages newer than it are fetched, newest first, and the
    new rows are appended: a daily refresh needs a few calls instead of the whole history.
    """
    seen = {_row_key(r) for r in known} if known else None
    rows, cursor = [], None
    for _ in range(max_pages):
        params = {"per_page": per_page, "order": "desc" if seen else "asc"}
        if cursor:
            params["cursor"] = cursor
        page = _get(f"{NEARBLOCKS}/account/{account}/{kind}", params)
        batch = page.get("txns", [])
        if not batch:
            break
        if seen is not None:
            fresh = [r for r in batch if _row_key(r) not in seen]
            rows.extend(fresh)
            if len(fresh) < len(batch):
                break
        else:
            rows.extend(batch)
        cursor = page.get("cursor")
        if not cursor:
            break
        time.sleep(1.2)  # stay well under the free-tier rate limit
    if seen is None:
        return rows
    return known + sorted(rows, key=lambda r: int(r["block_timestamp"]))


def fetch_buyback_txns() -> Path:
    """Full transaction history of the buyback wallet (kept for backward compatibility)."""
    return _save("buyback_txns", fetch_account_history(BUYBACK_WALLET, known=_previous("buyback_txns")))


def _view(contract: str, method: str, args: dict | None = None):
    import base64

    res = _rpc("query", {
        "request_type": "call_function", "finality": "final", "account_id": contract,
        "method_name": method, "args_base64": base64.b64encode(json.dumps(args or {}).encode()).decode(),
    })
    return json.loads(bytes(res["result"]))


def fetch_governance() -> dict[str, Path]:
    """Policy and every proposal (with descriptions) of the two revenue DAOs."""
    out = {}
    for dao in ("fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"):
        payload = {
            "policy": _view(dao, "get_policy"),
            "proposals": _view(dao, "get_proposals", {"from_index": 0, "limit": 100}),
        }
        folder = RAW / "governance"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{dao.split('.')[0]}.json"
        path.write_text(json.dumps(payload, indent=1))
        out[dao] = path
    return out


def fetch_revenue_wallets() -> dict[str, Path]:
    """NEAR transfers and token transfers of all three revenue wallets."""
    out = {}
    for wallet in REVENUE_WALLETS:
        short = wallet.split(".")[0]
        for kind, tag in (("txns", "txns"), ("ft-txns", "ft")):
            name = f"wallet_{short}_{tag}"
            out[f"{short}_{tag}"] = _save(name, fetch_account_history(wallet, kind, known=_previous(name)))
    return out


if __name__ == "__main__":
    # Each source is fetched independently: if one is rate-limited or down, its last committed
    # snapshot stays in use (every reader takes the latest file) and the others still refresh.
    import sys

    failed = []
    for fetch in (fetch_llama_intents, fetch_near_prices, fetch_chain_state, fetch_buyback_txns,
                  fetch_revenue_wallets, fetch_governance, fetch_wallet_state):
        try:
            print(fetch.__name__, fetch())
        except Exception as e:  # noqa: BLE001
            failed.append(fetch.__name__)
            print(f"WARNING {fetch.__name__} failed, keeping the previous snapshot: {e}", file=sys.stderr)
    if len(failed) == 6:
        sys.exit("every source failed")
