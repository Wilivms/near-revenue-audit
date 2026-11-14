"""Who signs NEAR's transactions? Human-scale signers against bots, and whether either tells you anything.

Transaction and active-account counts mix three populations: a few dozen heavy signers (bots, relayers
and contracts that sign their own work, such as intents.near) that send most transactions, a few hundred
mid-size ones, and the signers who send at most 50 transactions a week (about 7 a day): human scale.
`sql/signers_weekly.sql` counts each class every week on NEAR's BigQuery dataset (committed result:
data/raw/bigquery/signers_weekly_<date>.csv). This step:

1. measures each class's share of transactions and how human-scale signers moved over the year,
2. flags burst weeks (human-scale signers above twice their 8-week median), which are account campaigns,
   not organic use,
3. extends the track's lead-lag test (F13) to human-scale signers: weekly changes against NEAR's price net
   of Bitcoin, lags 1-4 weeks, both directions, Holm's correction; and how they track Intents volume and
   revenue within the week.

Output: data/processed/signers.json and signers_weekly.csv.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .leadlag import LAGS, _holm, _p_value, weekly
from .ledger import OUT, RAW


def load() -> pd.DataFrame:
    f = sorted((RAW / "bigquery").glob("signers_weekly_*.csv"))[-1]
    d = pd.read_csv(f, parse_dates=["week"]).set_index("week")
    med = d["light_signers"].rolling(8, min_periods=4).median().shift(1)
    d["burst"] = d["light_signers"] > 2 * med
    d["light_non_tg"] = d["light_signers"] - d["light_tg"]  # .tg accounts are created by a Telegram game (HOT)
    return d


def main() -> dict:
    d = load()
    d.assign(heavy_share=d["heavy_txns"] / d["txns"], light_share=d["light_txns"] / d["txns"]).to_csv(OUT / "signers_weekly.csv")
    clean = d[~d["burst"]]
    last4, year4 = clean.iloc[-4:], clean[(clean.index >= clean.index[-4] - pd.Timedelta(days=364)) & (clean.index <= clean.index[-1] - pd.Timedelta(days=364))]
    g = weekly()
    s = np.log(d[["light_signers", "light_non_tg", "heavy_txns"]]).diff()
    s.loc[d["burst"] | d["burst"].shift(1, fill_value=False), ["light_signers", "light_non_tg"]] = np.nan  # burst weeks and the week after
    x = g.join(s, how="inner")
    rows = []
    for series in ("light_signers", "light_non_tg", "heavy_txns"):
        for k in LAGS:
            for direction, a, b in (("usage leads price", x[series], x["near_vs_btc"].shift(-k)),
                                    ("price leads usage", x["near_vs_btc"], x[series].shift(-k))):
                xy = pd.concat([a, b], axis=1).dropna()
                r = float(xy.iloc[:, 0].corr(xy.iloc[:, 1]))
                rows.append({"series": series, "direction": direction, "lag_weeks": k, "n": len(xy), "r": r, "p": _p_value(r, len(xy))})
    t = pd.DataFrame(rows)
    t["p_holm"] = np.nan
    for direction in t["direction"].unique():
        idx = t.index[t["direction"] == direction]
        t.loc[idx, "p_holm"] = _holm(t.loc[idx, "p"].tolist())
    same_week = {c: float(x["light_signers"].corr(x[c])) for c in ("intents_volume", "txns", "revenue", "near_vs_btc")}
    same_week_non_tg = {c: float(x["light_non_tg"].corr(x[c])) for c in ("intents_volume", "revenue", "near_vs_btc")}
    rev = x.loc["2026-03-02":]
    res = {
        "weeks": int(len(d)), "from": str(d.index[0].date()), "to": str(d.index[-1].date()),
        "heavy_signers_median": float(d["heavy_signers"].median()),
        "heavy_share_first": float(d["heavy_txns"].iloc[:4].sum() / d["txns"].iloc[:4].sum()),
        "heavy_share_last": float(d["heavy_txns"].iloc[-4:].sum() / d["txns"].iloc[-4:].sum()),
        "light_share_last": float(d["light_txns"].iloc[-4:].sum() / d["txns"].iloc[-4:].sum()),
        "light_signers_last4": float(last4["light_signers"].mean()), "light_signers_year_before": float(year4["light_signers"].mean()),
        "light_signers_yoy": float(last4["light_signers"].mean() / year4["light_signers"].mean() - 1),
        "light_signers_first4": float(clean["light_signers"].iloc[:4].mean()),
        "tg_share_of_light_last4": float(last4["light_tg"].sum() / last4["light_signers"].sum()),
        "light_non_tg_last4": float(last4["light_non_tg"].mean()), "light_non_tg_year_before": float(year4["light_non_tg"].mean()),
        "light_non_tg_yoy": float(last4["light_non_tg"].mean() / year4["light_non_tg"].mean() - 1),
        "light_non_tg_first4": float(clean["light_non_tg"].iloc[:4].mean()),
        "light_tx_per_signer_last4": float(last4["light_txns"].sum() / last4["light_signers"].sum()),
        "bursts": [{"week": str(k.date()), "light_signers": int(v), "implicit": int(i)} for k, v, i in
                   zip(d.index[d["burst"]], d.loc[d["burst"], "light_signers"], d.loc[d["burst"], "light_implicit"])],
        "heavy_txns_drop_2026_04": float(d.loc["2026-04-06":"2026-04-27", "heavy_txns"].mean() / d.loc["2026-03-02":"2026-03-23", "heavy_txns"].mean() - 1),
        "lead_lag_tests": int(len(t)), "lead_lag_significant_holm": int((t["p_holm"] < 0.05).sum()),
        "lead_lag_best": t.loc[t["p"].idxmin()].to_dict(),
        "same_week_corr": same_week, "same_week_corr_non_tg": same_week_non_tg,
        "light_vs_revenue_since_march": float(rev["light_signers"].corr(rev["revenue"])), "weeks_since_march": int(rev["revenue"].notna().sum()),
    }
    t.to_csv(OUT / "signers_leadlag.csv", index=False)
    (OUT / "signers.json").write_text(json.dumps(res, indent=1, default=str))
    print(f"signers: heavy signers (median {res['heavy_signers_median']:.0f} accounts) sent {res['heavy_share_first']:.0%} of transactions in Nov 2024, "
          f"{res['heavy_share_last']:.0%} now; human-scale signers {res['light_signers_last4']:,.0f} a week, {res['light_signers_yoy']:+.0%} on a year; "
          f"{len(res['bursts'])} burst weeks; lead-lag {res['lead_lag_significant_holm']} of {res['lead_lag_tests']} significant after Holm "
          f"(best r = {res['lead_lag_best']['r']:+.2f}, p = {res['lead_lag_best']['p']:.2f}); same week with Intents volume r = {same_week['intents_volume']:+.2f}, "
          f"with revenue since March r = {res['light_vs_revenue_since_march']:+.2f}")
    return res


if __name__ == "__main__":
    main()
