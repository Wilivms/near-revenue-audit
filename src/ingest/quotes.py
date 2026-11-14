"""Quote race: what a user receives from 1Click and from the main competing routers, for the same swap.

The take-rate question ("will competition compress NEAR's take?") needs the price NEAR Intents offers
against the alternatives a user or a wallet could route to. Each round asks, within a few seconds, for
the same input on the same route:
  - 1Click (NEAR Intents), public endpoint, no key, dry quote (no deposit address is created)
  - Relay, LI.FI (its public API; its quote includes LI.FI's default fixed fee, recorded) and, on
    same-asset routes, Across
and saves every answer, as returned, to data/raw/quotes/<UTC date>T<HHMM>.json. Nothing is signed or sent:
these are quotes for a public placeholder address. `make quotes` reads all rounds offline.

    python3 -m src.ingest.quotes          # one round, about a minute
"""
from __future__ import annotations

import datetime as dt
import json
import time

import requests

from .sources import RAW

EVM = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # a public address; quotes only, nothing is sent
SOL = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
BTC = "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"  # a public exchange address: Relay and LI.FI quote only for a sender with UTXOs
UA = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"  # USDC Arbitrum
UB = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC Base
UE = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC Ethereum
ZERO = "0x0000000000000000000000000000000000000000"
WETH = {1: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", 42161: "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"}

# chain: (Relay chain id, LI.FI chain id, sender address)
CHAINS = {"eth": (1, 1, EVM), "arb": (42161, 42161, EVM), "base": (8453, 8453, EVM),
          "sol": (792703809, 1151111081099710, SOL), "btc": (8253038, 20000000000001, BTC)}
# asset: (chain, 1Click asset id, Relay currency, LI.FI token, decimals)
ASSETS = {
    "USDC.arb": ("arb", "nep141:arb-0xaf88d065e77c8cc2239327c5edb3a432268e5831.omft.near", UA, UA, 6),
    "USDC.base": ("base", "nep141:base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913.omft.near", UB, UB, 6),
    "USDC.eth": ("eth", "nep141:eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.omft.near", UE, UE, 6),
    "ETH.eth": ("eth", "nep141:eth.omft.near", ZERO, ZERO, 18),
    "ETH.arb": ("arb", "nep141:arb.omft.near", ZERO, ZERO, 18),
    "SOL.sol": ("sol", "nep141:sol.omft.near", "11111111111111111111111111111111", "11111111111111111111111111111111", 9),
    "BTC.btc": ("btc", "nep141:btc.omft.near", "bc1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqmql8k8", "bitcoin", 8),
}
# route id, corridor, from, to, sizes in input units (about $1k and $20k)
ROUTES = [
    ("usdc-arb-base", "same asset, EVM L2 to L2", "USDC.arb", "USDC.base", (1_000, 20_000)),
    ("eth-eth-arb", "same asset, Ethereum to L2", "ETH.eth", "ETH.arb", (0.5, 10)),
    ("eth-usdc", "cross asset, EVM", "ETH.eth", "USDC.arb", (0.5, 10)),
    ("sol-usdc", "cross chain family, Solana to EVM", "SOL.sol", "USDC.eth", (13, 260)),
    ("btc-usdc", "native BTC to EVM", "BTC.btc", "USDC.eth", (0.015, 0.3)),
]
TIMEOUT = 45


def _units(x: float, dec: int) -> str:
    return str(int(round(x * 10**dec)))


def oneclick(src: str, dst: str, amount: str) -> dict:
    deadline = (dt.datetime.now(dt.UTC) + dt.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    body = {"dry": True, "swapType": "EXACT_INPUT", "slippageTolerance": 50, "originAsset": ASSETS[src][1],
            "depositType": "ORIGIN_CHAIN", "destinationAsset": ASSETS[dst][1], "amount": amount,
            "refundTo": CHAINS[ASSETS[src][0]][2], "refundType": "ORIGIN_CHAIN", "recipient": CHAINS[ASSETS[dst][0]][2],
            "recipientType": "DESTINATION_CHAIN", "deadline": deadline, "quoteWaitingTimeMs": 3000}
    r = requests.post("https://1click.chaindefuser.com/v0/quote", json=body, timeout=TIMEOUT)
    j = r.json()
    q = j.get("quote") or {}
    return {"status": r.status_code, "amount_out": q.get("amountOut"), "time_estimate_s": q.get("timeEstimate"),
            "error": None if q.get("amountOut") else j.get("message")}


def relay(src: str, dst: str, amount: str) -> dict:
    a, b = ASSETS[src], ASSETS[dst]
    body = {"user": CHAINS[a[0]][2], "originChainId": CHAINS[a[0]][0], "destinationChainId": CHAINS[b[0]][0],
            "originCurrency": a[2], "destinationCurrency": b[2], "amount": amount, "tradeType": "EXACT_INPUT",
            "recipient": CHAINS[b[0]][2]}
    r = requests.post("https://api.relay.link/quote", json=body, timeout=TIMEOUT)
    j = r.json()
    d = j.get("details") or {}
    out = (d.get("currencyOut") or {}).get("amount")
    return {"status": r.status_code, "amount_out": out, "time_estimate_s": d.get("timeEstimate"),
            "error": None if out else j.get("message")}


def lifi(src: str, dst: str, amount: str) -> dict:
    a, b = ASSETS[src], ASSETS[dst]
    p = {"fromChain": CHAINS[a[0]][1], "toChain": CHAINS[b[0]][1], "fromToken": a[3], "toToken": b[3], "fromAmount": amount,
         "fromAddress": CHAINS[a[0]][2], "toAddress": CHAINS[b[0]][2]}
    r = requests.get("https://li.quest/v1/quote", params=p, timeout=TIMEOUT)
    j = r.json()
    e = j.get("estimate") or {}
    fee = sum(float(c.get("percentage") or 0) for c in e.get("feeCosts") or [] if "LIFI" in (c.get("name") or "").upper())
    return {"status": r.status_code, "amount_out": e.get("toAmount"), "tool": j.get("tool"), "lifi_fee_pct": fee,
            "time_estimate_s": e.get("executionDuration"), "error": None if e.get("toAmount") else j.get("message")}


def across(src: str, dst: str, amount: str) -> dict | None:
    a, b = ASSETS[src], ASSETS[dst]
    if src.split(".")[0] != dst.split(".")[0] or a[0] in ("sol", "btc") or b[0] in ("sol", "btc"):
        return None  # Across bridges the same asset between EVM chains
    tok = lambda x: WETH.get(CHAINS[x[0]][0], x[2]) if x[2] == ZERO else x[2]  # noqa: E731
    p = {"inputToken": tok(a), "outputToken": tok(b), "originChainId": CHAINS[a[0]][0], "destinationChainId": CHAINS[b[0]][0], "amount": amount}
    r = requests.get("https://app.across.to/api/suggested-fees", params=p, timeout=TIMEOUT)
    j = r.json()
    fee = (j.get("totalRelayFee") or {}).get("total")
    ok = fee is not None and not j.get("isAmountTooLow")
    return {"status": r.status_code, "amount_out": str(int(amount) - int(fee)) if ok else None,
            "time_estimate_s": j.get("estimatedFillTimeSec"), "error": None if ok else (j.get("message") or "amount too low")}


PROVIDERS = {"1click": oneclick, "relay": relay, "lifi": lifi, "across": across}


def round_() -> dict:
    t0 = dt.datetime.now(dt.UTC)
    rows = []
    for rid, corridor, src, dst, sizes in ROUTES:
        for size in sizes:
            amount = _units(size, ASSETS[src][4])
            q = {}
            for name, f in PROVIDERS.items():
                s = time.time()
                try:
                    res = f(src, dst, amount)
                except Exception as e:  # a provider down is a missing quote, not a failed round
                    res = {"status": None, "amount_out": None, "error": f"{type(e).__name__}: {e}"[:200]}
                if res is None:
                    continue
                res["seconds"] = round(time.time() - s, 2)
                q[name] = res
            rows.append({"route": rid, "corridor": corridor, "from": src, "to": dst, "size_in": size, "amount_in": amount,
                         "out_decimals": ASSETS[dst][4], "quotes": q})
            print(f"{rid:14s} {size:>8} " + "  ".join(f"{k}={v.get('amount_out') or 'x'}" for k, v in q.items()))
    return {"started_utc": t0.isoformat(timespec="seconds"), "finished_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "note": "dry quotes for a public placeholder address; nothing was signed or sent", "rows": rows}


def main() -> None:
    r = round_()
    folder = RAW / "quotes"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (r["started_utc"][:16].replace(":", "") + ".json")
    path.write_text(json.dumps(r, indent=1))
    print(f"saved {path.relative_to(RAW.parents[1])}")


if __name__ == "__main__":
    main()
