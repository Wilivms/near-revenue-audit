"""Bundle the committed analysis outputs into dashboard/data.json.

The dashboard reads this file for everything that needs our own analysis (1Click swaps, supply,
Monte Carlo) and fetches DefiLlama, DefiLlama coins and the NEAR RPC live in the browser for the
headline figures and kill criteria 1 and 3. If the live fetch fails, it falls back to the
`live_fallback` block below, labelled with its date.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .ledger import OUT, RAW, ROOT, llama_daily, near_price

DASH = ROOT / "dashboard"


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.replace({np.nan: None}).to_json(orient="records", date_format="iso"))


def build() -> dict:
    supply = pd.read_csv(OUT / "supply_monthly.csv")
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)
    vol = llama_daily("llama_volume", "volume_usd")
    price = near_price()
    daily = pd.concat([vol, rev["rebuilt_total_usd"].rename("captured_usd"), price], axis=1, sort=True)
    daily = daily[daily.index >= "2026-02-23"].dropna(subset=["volume_usd"])
    daily["captured_usd"] = daily["captured_usd"].fillna(0)
    roll = daily[["volume_usd", "captured_usd"]].rolling(14).sum()
    daily["take_bps_14d"] = roll["captured_usd"] / roll["volume_usd"] * 1e4
    daily = daily.reset_index().rename(columns={"index": "date"})
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")

    weekly = pd.read_csv(OUT / "swaps_weekly.csv")
    fees = pd.read_csv(OUT / "fee_shares_last30d.csv").rename(columns={"ref": "referral"})
    mc_s = pd.read_csv(OUT / "montecarlo_scenarios.csv")
    mc_p = pd.read_csv(OUT / "montecarlo_paths_base.csv")
    mc_all = pd.read_csv(OUT / "montecarlo_paths_all.csv")
    sens = pd.read_csv(OUT / "montecarlo_sensitivity.csv")
    chain = json.loads(sorted((RAW / "chain_state").glob("*.json"))[-1].read_text())
    comps = pd.read_csv(OUT / "comps.csv")
    share = pd.read_csv(OUT / "crosschain_share.csv", index_col=0)
    risk = pd.read_csv(OUT / "token_risk.csv")
    hy = pd.read_csv(OUT / "holder_yield.csv")
    conf_w = pd.read_csv(OUT / "confidential_weekly.csv")
    conf_tvl = pd.read_csv(OUT / "confidential_tvl.csv")
    conf_sum = json.loads((OUT / "confidential_summary.json").read_text())
    off = json.loads((OUT / "official_crosscheck.json").read_text())
    off_w = pd.read_csv(OUT / "official_weekly.csv")
    off_tvl = pd.read_csv(OUT / "official_tvl.csv")
    by_asset = pd.read_csv(OUT / "revenue_by_asset_last30d.csv").rename(columns={"label": "asset"})

    sm = supply[supply["date"] >= "2026-02-01"]
    issuance_rate = sm["net_issuance_near"].sum() / pd.to_datetime(sm["date"]).dt.days_in_month.sum() * 365 \
        / chain["total_supply_near"]
    last30 = daily.tail(30)
    return {
        "built_at": daily["date"].iloc[-1],  # last day of data, not the wall clock: the rebuild is byte-identical
        "issuance_rate": issuance_rate,
        # last day of collected 1Click swaps: integrator and asset shares are "30 days to" this date
        "oneclick_as_of": str((pd.Timestamp(weekly["period_start"].iloc[-1]) + pd.Timedelta(days=int(weekly["days"].iloc[-1]) - 1)).date()),
        "live_fallback": {
            "as_of": daily["date"].iloc[-1],
            "price": float(price.dropna().iloc[-1]),
            "supply": chain["total_supply_near"],
            "captured_30d_usd": float(last30["captured_usd"].sum()),
            "volume_30d_usd": float(last30["volume_usd"].sum()),
        },
        "daily": _records(daily[["date", "volume_usd", "captured_usd", "near_usd", "take_bps_14d"]]),
        "supply_monthly": _records(supply[["date", "net_issuance_near", "captured_near_3_wallets",
                                           "captured_near_buyback_wallet", "captured_share_of_issuance"]]),
        "oneclick_weekly": _records(weekly[["period_start", "volume_usd_per_day", "near_bps", "fee_bps",
                                            "zec_vol_share", "zec_near_rev_share", "noref_near_rev_share",
                                            "top3_integrators_near_rev", "senders_per_day"]]),
        "fee_shares_last30d": _records(fees.head(8)),
        "revenue_by_asset": _records(by_asset),
        "confidential": {
            "weekly": _records(conf_w.rename(columns={conf_w.columns[0]: "week"})[["week", "public_usd", "confidential_usd", "confidential_share", "take_bps"]]),
            "tvl": _records(conf_tvl.rename(columns={conf_tvl.columns[0]: "date"})),
            "monthly_share": conf_sum["monthly_confidential_share"],
            "summary": {"regression": conf_sum["regression"]["rebuilt_total_usd"], "h41": conf_sum["h41"], "incentive": conf_sum["incentive"],
                        "ci": conf_sum["regression"]["bootstrap_90ci"]["bps_confidential"],
                        "robustness": conf_sum["regression"]["robustness"], "jump_explained": conf_sum["jump_explained"],
                        "near_terms": conf_sum["near_terms"],
                        "out_of_sample": conf_sum["out_of_sample"], "counterfactual": conf_sum["counterfactual"]},
        },
        "official": {
            "summary": off,
            "weekly": _records(off_w.rename(columns={off_w.columns[0]: "week"})[["week", "volume_usd", "gross_fee_bps", "take_bps", "capture_of_fees"]].tail(30)),
            "tvl": _records(off_tvl.rename(columns={off_tvl.columns[0]: "date"})),
        },
        # peers with material holders revenue only (at least $100k in 30 days): a token paying its holders
        # a few hundred dollars is not a comparable, and its multiple (18,000x for JTO) breaks the chart
        "comps": _records(comps[comps["mcap_to_holders_revenue"].notna() & (comps["holders_revenue_30d_usd"] >= 100_000)][["token", "market_cap_usd", "annualised_usd", "mcap_to_holders_revenue"]]),
        "crosschain_share": _records(share.filter(like="_share").reset_index().rename(columns={share.index.name or "index": "month"})),
        "token_risk": _records(risk),
        "holder_yield": _records(hy),
        "montecarlo": {
            "scenarios": _records(mc_s[["name", "take_bps", "median_offset_2027", "p10_offset_2027",
                                        "p90_offset_2027", "p_2027_net_deflationary",
                                        "median_path_deflationary_month"]]),
            "base_paths": _records(mc_p),
            "paths": {name: _records(g.drop(columns="scenario")) for name, g in mc_all.groupby("scenario", sort=False)},
            "sensitivity": _records(sens),
        },
    }


def main() -> None:
    DASH.mkdir(exist_ok=True)
    data = build()
    (DASH / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    print(f"dashboard/data.json: {len(data['daily'])} days, {len(data['oneclick_weekly'])} 1Click weeks")


if __name__ == "__main__":
    main()
