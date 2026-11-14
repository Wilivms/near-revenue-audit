"""NEAR's major events, tested the same way: did each one move volume, revenue, the take, share or price?

Each event gets the same before/after split as the incident study (two weeks before, two weeks after, a
two-day gap on each side of the event) on the daily series that cover it, and the change is ranked
against the same split at every date of the last year that is at least three weeks from any listed
event (a placebo distribution; earlier dates are left out because Intents volume then grew several-fold, a
different regime). A change outside most placebo dates is unusual for that series; one
inside them is not, whatever the narrative said at the time.

Series (all committed, offline): NEAR Intents volume (DefiLlama), revenue rebuilt from the three wallets,
NEAR's take (revenue over volume), NEAR Intents' share of cross-chain swap volume against THORChain,
Chainflip and Maya (DefiLlama), confidential TVL, and NEAR's price against Bitcoin (abnormal log return
over the first three days and the two weeks, beta from the 120 days before).

Output: data/processed/events.csv (event x measure) and events.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .ledger import OUT, RAW, llama_daily, near_price
from .token_risk import btc_price

EVENTS = [
    ("halving", "2025-10-30", "Issuance halved (5% to 2.5% a year), nearcore 2.9.0",
     "https://invezz.com/news/2025/10/30/near-protocol-near-slashes-inflation-to-2-5-after-successful-halving-upgrade/"),
    ("fee_switch", "2026-02-24", "Fee switch: Intents fees start buying NEAR (23 Feb), Confidential Intents launch (25 Feb)",
     "https://tools.prnewswire.com/en-us/live/20813/release/20260225EN95768"),
    ("confidential_ga", "2026-07-13", "Confidential Intents open to all developers",
     "https://glitchwire.com/news/nears-confidential-intents-reaches-general-availability-bringing-privacy-infrast/"),
    ("confidential_1click", "2026-07-27", "Confidential execution added to the 1Click Swap API",
     "https://coinfomania.com/pl/near-protocol-enhances-1click-swap-api-with-confidential-intents-pl/"),
    ("airdrop_snapshot", "2026-09-16", "NEAR@3.33 Drop 1 snapshot (confidential balances)", "RESEARCH_LOG.md entry 24"),
    ("exploit", "2026-10-01", "Freeze of a Bitget-linked swap (29 Sep), $3.8M exploit and 3.7-hour halt (1 Oct)",
     "https://www.theblock.co/news/ecosystems/2026-10-01-near-intents-halts-services-after-3-8-million-exploit-417404"),
    ("hsp029", "2026-11-02", "HSP-029 (issuance cap 2.5% to 1.6%) approved, enters its timelock", "RESEARCH_LOG.md entry 41"),
]
RIVALS = ["thorchain-dex", "chainflip-amm", "maya-protocol"]
GUARD = 21  # placebo dates stay this many days from any listed event
PLACEBO_DAYS = 380


def series() -> pd.DataFrame:
    vol = llama_daily("llama_volume", "volume")
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"].rename("revenue")
    rev = rev[rev.index >= "2026-02-23"]
    payload = json.loads(sorted((RAW / "comps").glob("*.json"))[-1].read_text())
    cv = payload["crosschain_volume"]
    riv = pd.DataFrame({s: pd.Series({pd.to_datetime(t, unit="s").normalize(): v for t, v in cv[s]}) for s in RIVALS
                        if isinstance(cv.get(s), list)}).sum(axis=1).rename("rivals")
    ctvl = pd.read_csv(OUT / "confidential_tvl.csv", index_col=0, parse_dates=True)["confidential_tvl_usd"].rename("confidential_tvl")
    df = pd.concat([vol, rev, riv, ctvl, near_price(), btc_price()], axis=1, sort=True)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated()].sort_index()
    df["share"] = df["volume"] / (df["volume"] + df["rivals"])
    df["r_near"] = np.log(df["near_usd"]).diff()
    df["r_btc"] = np.log(df["btc_usd"]).diff()
    return df


def _abnormal(df: pd.DataFrame, e: pd.Timestamp, days: int) -> float | None:
    est = df.loc[e - pd.Timedelta(days=135): e - pd.Timedelta(days=16), ["r_near", "r_btc"]].dropna()
    win = df.loc[e: e + pd.Timedelta(days=days - 1), ["r_near", "r_btc"]].dropna()
    if len(est) < 60 or len(win) < days:
        return None
    beta = float(np.cov(est["r_near"], est["r_btc"])[0, 1] / est["r_btc"].var())
    alpha = float(est["r_near"].mean() - beta * est["r_btc"].mean())
    return float((win["r_near"] - alpha - beta * win["r_btc"]).sum())


def stats(df: pd.DataFrame, e: pd.Timestamp, post_days: int = 14) -> dict:
    b0, b1 = e - pd.Timedelta(days=16), e - pd.Timedelta(days=3)
    a0, a1 = e + pd.Timedelta(days=2), e + pd.Timedelta(days=1 + post_days)
    out = {}
    for c in ("volume", "revenue", "confidential_tvl"):
        pre, post = df.loc[b0:b1, c].dropna(), df.loc[a0:a1, c].dropna()
        if len(pre) >= 12 and len(post) >= min(post_days, 10) and pre.median() > 0:
            out[f"{c}_change"] = float(post.median() / pre.median() - 1)
    pre, post = df.loc[b0:b1, ["revenue", "volume"]].dropna(), df.loc[a0:a1, ["revenue", "volume"]].dropna()
    if len(pre) >= 12 and len(post) >= min(post_days, 10):
        out["take_change_bps"] = float((post["revenue"].sum() / post["volume"].sum() - pre["revenue"].sum() / pre["volume"].sum()) * 1e4)
    pre, post = df.loc[b0:b1, "share"].dropna(), df.loc[a0:a1, "share"].dropna()
    if len(pre) >= 12 and len(post) >= min(post_days, 10):
        out["share_change_pts"] = float((post.median() - pre.median()) * 100)
    for k, n in (("abnormal_return_3d", 3), ("abnormal_return_14d", 14)):
        v = _abnormal(df, e, n)
        if v is not None:
            out[k] = v
    return out


def main() -> dict:
    df = series()
    last = df["volume"].dropna().index.max()
    dates = [pd.Timestamp(d) for _, d, _, _ in EVENTS]
    # placebo dates from the last year only: in 2024-25 Intents volume grew several-fold, a different regime
    candidates = [d for d in pd.date_range(max(df.index.min() + pd.Timedelta(days=140), last - pd.Timedelta(days=PLACEBO_DAYS)), last - pd.Timedelta(days=16))
                  if all(abs((d - e).days) >= GUARD for e in dates)]
    placebo = {d: stats(df, d) for d in candidates}
    rows = []
    for key, date, label, source in EVENTS:
        e = pd.Timestamp(date)
        post_days = min(14, (last - e).days - 1)
        st = stats(df, e, post_days)
        for k, v in st.items():
            vals = [p[k] for p in placebo.values() if k in p]
            lo, hi = sum(x <= v for x in vals), sum(x >= v for x in vals)
            rows.append({"event": key, "date": date, "label": label, "source": source, "measure": k, "value": v,
                         "post_days": post_days, "placebo_n": len(vals), "placebo_median": float(np.median(vals)),
                         "placebo_p10": float(np.percentile(vals, 10)), "placebo_p90": float(np.percentile(vals, 90)),
                         "percentile": lo / len(vals), "p_two_sided": min(1.0, 2 * min(lo + 1, hi + 1) / (len(vals) + 1))})
    t = pd.DataFrame(rows)
    t.round(6).to_csv(OUT / "events.csv", index=False)
    unusual = t[t["p_two_sided"] <= 0.10]
    res = {"events": [{"key": k, "date": d, "label": lab, "source": src} for k, d, lab, src in EVENTS],
           "placebo_dates": len(candidates), "series_to": str(last.date()),
           "unusual": [{"event": r.event, "measure": r.measure, "value": r.value, "p": r.p_two_sided} for r in unusual.itertuples()],
           "note": "change over the median day of two weeks after against two weeks before (2-day gaps), ranked against the same split at "
                   f"every date of the last year at least {GUARD} days from any listed event; p is two-sided; with many events and measures, a few "
                   "p ≤ 0.10 are expected by chance"}
    (OUT / "events.json").write_text(json.dumps(res, indent=1))
    print(f"events: {len(EVENTS)} events, {len(candidates)} placebo dates, {len(t)} tests, {len(unusual)} with p <= 0.10:")
    for r in t.itertuples():
        flag = " *" if r.p_two_sided <= 0.10 else ""
        print(f"  {r.event:20s} {r.measure:22s} {r.value:+9.3f}  placebo median {r.placebo_median:+8.3f}  p={r.p_two_sided:.2f}{flag}")
    return res


if __name__ == "__main__":
    main()
