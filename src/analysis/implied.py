"""What does NEAR's price imply? A reverse valuation on the revenue measured here.

The forward question (does revenue offset issuance?) is answered elsewhere. This one runs backwards from
the market cap: what captured revenue would justify it, and how fast would today's revenue have to grow?

- Perpetuity: the revenue R* that a market cap M is worth at discount rate r and growth g, R* = M (r - g) / (1 + g).
- Five years then a peer multiple: the revenue NEAR would need in five years for M, compounded at r, to equal
  that revenue times the median multiple of the peers that pay holders (`make comps`), and the yearly growth
  that takes from today's revenue.
- In volume: the daily NEAR Intents volume each implied revenue needs at today's take.

It values captured revenue as if it all reached holders, which favours the price: here it buys NEAR back
but is not paid out, and issuance still dilutes. Inputs are committed outputs only.
"""
from __future__ import annotations

import json

import pandas as pd

from .ledger import OUT, llama_daily


def main() -> dict:
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    rev = rev.loc[:rev.index.max() - pd.Timedelta(days=1)]
    r30 = float(rev.iloc[-30:].sum() * 365 / 30)
    comps = pd.read_csv(OUT / "comps.csv")
    m = float(comps.loc[comps.token == "NEAR", "market_cap_usd"].iloc[0])
    peers = comps[(comps.token != "NEAR") & comps.mcap_to_holders_revenue.notna() & (comps.holders_revenue_30d_usd >= 100_000)]
    peer = float(peers.mcap_to_holders_revenue.median())
    vol = llama_daily("llama_volume", "v")
    vol.index = pd.to_datetime(vol.index).tz_localize(None)
    take = float(rev.iloc[-30:].sum() / vol.loc[rev.index[-30]:rev.index[-1]].sum())
    perp = []
    for r in (0.10, 0.15, 0.20):
        for g in (0.0, 0.03, 0.05):
            need = m * (r - g) / (1 + g)
            perp.append({"discount": r, "growth": g, "revenue_needed_usd": need, "times_today": need / r30,
                         "volume_per_day_usd": need / take / 365})
    five = []
    for r in (0.10, 0.15, 0.20):
        r5 = m * (1 + r) ** 5 / peer
        five.append({"discount": r, "revenue_in_5y_usd": r5, "times_today": r5 / r30, "growth_per_year": (r5 / r30) ** (1 / 5) - 1,
                     "volume_per_day_usd": r5 / take / 365})
    end = rev.index[-1]
    hist = float(vol.loc[end - pd.Timedelta(days=29):end].sum() / vol.loc[end - pd.Timedelta(days=394):end - pd.Timedelta(days=365)].sum() - 1)
    res = {"market_cap_usd": m, "revenue_annualised_usd": r30, "take_bps": take * 1e4, "peer_median_multiple": peer,
           "perpetuity": perp, "five_years_then_peer_multiple": five,
           "volume_growth_last_30d_vs_year_before": hist,
           "note": "captured revenue valued as if paid to holders (it buys NEAR back and is not paid out), which favours the price"}
    (OUT / "implied.json").write_text(json.dumps(res, indent=1))
    mid = next(x for x in five if x["discount"] == 0.15)
    p = next(x for x in perp if x["discount"] == 0.15 and x["growth"] == 0.03)
    print(f"implied: at 15% and 3% growth, the price needs {p['times_today']:.1f}x today's revenue (${p['volume_per_day_usd'] / 1e9:.1f}B a day of volume at "
          f"{take * 1e4:.1f} bps); or {mid['growth_per_year']:.0%} a year for five years then the peer median multiple ({peer:.0f}x); "
          f"Intents volume over the last 30 days is {hist:+.0%} on a year earlier")
    return res


if __name__ == "__main__":
    main()
