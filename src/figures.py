"""One source for every figure the documents quote, and the checks behind each finding.

`figures()` reads the committed outputs in data/processed/ (written by `make reproduce`) and
returns formatted values keyed by name. The documents are written as templates in docs/templates/
with {{name}} placeholders; `python3 -m src.figures` renders README.md, REPORT.md and FAQ.md from
them, so no number in the prose is typed by hand and none can drift from the data.

`claims()` turns the headline findings into checks with explicit conditions. `make verify`
renders the documents, prints the table and exits 1 if a finding no longer follows from the data,
or if a rendered document differs from the committed one.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
TEMPLATES = ROOT / "docs" / "templates"
DOCS = ("README.md", "REPORT.md", "FAQ.md", "THESIS.md")
FEE_SWITCH = "2026-02-23"


# ---------- formatting ----------
def pct(x: float, d: int = 0) -> str:
    return f"{x * 100:.{d}f}%"


def spct(x: float) -> str:
    """A signed whole percentage, with a real minus sign."""
    return f"{x * 100:+.0f}%".replace("-", "−")


def usd(x: float, d: int | None = None) -> str:
    a = abs(x)
    if a >= 1e9:
        return f"${x / 1e9:.{2 if d is None else d}f}B"
    if a >= 1e6:
        return f"${x / 1e6:.{2 if d is None else d}f}M"
    if a >= 1e3:
        return f"${x / 1e3:.{0 if d is None else d}f}k"
    return f"${x:.0f}"


def num(x: float, d: int = 0) -> str:
    return f"{x:,.{d}f}"


def near_m(x: float, d: int = 2) -> str:
    return f"{x / 1e6:.{d}f}M"


def mult(x: float, d: int = 0) -> str:
    return f"{x:.{d}f}x"


# ---------- inputs ----------
def _leaves(d) -> int:
    return sum(_leaves(v) for v in d.values()) if isinstance(d, dict) else 1


def _json(name: str) -> dict:
    return json.loads((OUT / name).read_text())


def _latest_raw(source: str):
    return json.loads(sorted((RAW / source).glob("*.json"))[-1].read_text())


def _llama(source: str) -> pd.Series:
    chart = _latest_raw(source)["totalDataChart"]
    return pd.Series({pd.to_datetime(t, unit="s").normalize(): v for t, v in chart}).sort_index()


def values() -> dict:
    """Raw (unformatted) values, from the committed outputs only."""
    v: dict = {}
    # 1. Ledger: rebuild vs DefiLlama
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)
    complete = rev.index[rev.index < rev.index.max()]  # the last day of the snapshot is partial
    since = rev.loc[FEE_SWITCH:complete.max()]
    v["rev_rebuilt"] = since["rebuilt_total_usd"].sum()
    v["rev_llama"] = since["llama_holders_revenue_usd"].sum()
    v["rev_ratio"] = v["rev_rebuilt"] / v["rev_llama"]
    v["rev_end"] = complete.max()
    m = since.resample("MS")[["rebuilt_total_usd", "llama_holders_revenue_usd"]].sum()
    full_months = m.loc["2026-03-01":(complete.max() + pd.Timedelta(days=1)).to_period("M").start_time - pd.Timedelta(days=1)]
    v["rev_month_ratio_min"] = float((full_months.rebuilt_total_usd / full_months.llama_holders_revenue_usd).min())
    v["rev_month_ratio_max"] = float((full_months.rebuilt_total_usd / full_months.llama_holders_revenue_usd).max())
    by_wallet = since[[c for c in since.columns if c.startswith("rebuilt_") and c != "rebuilt_total_usd"]].sum() / v["rev_rebuilt"]
    v["share_buyback_wallet"] = by_wallet["rebuilt_buybacks_usd"]
    v["share_fefunds"] = by_wallet["rebuilt_fefundsadmin_usd"]
    v["share_1cs"] = by_wallet["rebuilt_1csfundsadmin_usd"]
    flows = pd.read_csv(OUT / "revenue_wallet_flows.csv")
    near_in = flows[(flows.dir == "in") & flows.is_near & ~flows.internal]
    near_out = flows[(flows.dir == "out") & flows.is_near & ~flows.internal]
    v["near_in_all"] = near_in["amount"].sum()
    v["near_out_all"] = near_out["amount"].sum()
    v["near_out_share"] = v["near_out_all"] / v["near_in_all"]
    fe = near_in[near_in.wallet.str.startswith("fefunds")]["amount"].sum() - near_out[near_out.wallet.str.startswith("fefunds")]["amount"].sum()
    v["fefunds_near"] = fe
    v["fefunds_share"] = fe / (v["near_in_all"] - v["near_out_all"])

    # 2. Official cross-check
    off = _json("official_crosscheck.json")
    v["wallets_official"] = off["wallets_total"]["official_near"]
    v["wallets_rebuilt"] = off["wallets_total"]["rebuilt_near"]
    v["wallets_gap"] = abs(off["wallets_total"]["ratio"] - 1)
    v["offset_rebuilt"] = off["offset_feb_to_last_full_month"]["rebuilt"]
    v["offset_official"] = off["offset_feb_to_last_full_month"]["official"]
    v["offset_months"] = off["offset_feb_to_last_full_month"]["months"]
    v["issued_feb_oct"] = off["offset_feb_to_last_full_month"]["rebuilt_issuance_near"]
    v["captured_feb_oct"] = off["offset_feb_to_last_full_month"]["rebuilt_captured_near"]
    v["emissions_official"] = off["offset_feb_to_last_full_month"]["official_emissions_near"]
    rd = off.get("revenue_definitions", {})
    v["series_over_wallets"] = rd.get("mar_oct_official_over_wallets_usd", np.nan)
    ratios = list(rd.get("official_over_wallets_near", {}).values())
    v["series_ratio_min"], v["series_ratio_max"] = (min(ratios), max(ratios)) if ratios else (np.nan, np.nan)
    v["series_take_oct"] = rd.get("oct_take_bps", {}).get("official", np.nan)
    v["series_take_nov"] = rd.get("current_month_take_bps_official_implied", np.nan)
    cbm = off.get("capture_by_mechanism", {})
    for w in ("all_time", "d30"):
        for k in ("front_end_fees", "b2b_partners", "quote_improvement", "total"):
            v[f"cap_{k}_{w}"] = cbm.get(w, {}).get(k, np.nan)
    om = pd.read_csv(OUT / "official_monthly.csv", index_col=0, parse_dates=True)
    v["take_aug"] = om.loc["2026-08-01", "take_bps"]
    v["take_sep"] = om.loc["2026-09-01", "take_bps"]
    v["take_oct"] = om.loc["2026-10-01", "take_bps"]
    v["gross_bps_oct"] = om.loc["2026-10-01", "gross_fee_bps"]
    v["capture_oct"] = om.loc["2026-10-01", "capture_of_fees"]
    lw = off["last_week"]
    v["take_last_week"], v["capture_last_week"], v["gross_last_week"] = lw["take_bps"], lw["capture_of_fees"], lw["gross_fee_bps"]
    v["last_week"] = lw["week"]
    tvl = off["tvl"]
    v["tvl_last"], v["tvl_last_date"], v["tvl_peak"], v["tvl_peak_date"] = tvl["last_usd"], tvl["last_date"], tvl["peak_usd"], tvl["peak_date"]
    v["tvl_from_peak"], v["tvl_30d"] = tvl["change_from_peak"], tvl["change_30d"]
    hr = _llama("llama_dailyHoldersRevenue")
    vol = _llama("llama_volume")
    nov = slice(om.index[-1], pd.Timestamp(lw["week"]) + pd.Timedelta(days=6))
    v["take_nov_llama"] = hr.loc[nov].sum() / vol.loc[nov].sum() * 1e4

    # 3. Confidential channel
    c = _json("confidential_summary.json")
    reg = c["regression"]
    v["fit_weeks"] = reg["weeks"]
    v["fit_conf"], v["fit_pub"], v["fit_r2"] = reg["rebuilt_total_usd"]["bps_confidential"], reg["rebuilt_total_usd"]["bps_public"], reg["rebuilt_total_usd"]["r2"]
    v["fit_ci_lo"], v["fit_ci_hi"] = reg["bootstrap_90ci"]["bps_confidential"]
    rb = reg["robustness"]
    v["fd_conf"], v["fd_pub"] = rb["first_difference_bps"]["confidential"], rb["first_difference_bps"]["public"]
    v["fd_ci_lo"], v["fd_ci_hi"] = rb["first_difference_90ci_confidential"]
    v["loo_lo"], v["loo_hi"] = rb["leave_one_out_confidential_bps"]
    v["daily_fit_conf"] = reg["daily_fit_bps"]["confidential"]
    v["corr_conf_buyback"], v["corr_pub_buyback"] = reg["corr_confidential_vs_buyback_wallet"], reg["corr_public_vs_buyback_wallet"]
    v["dune_fee_bps"] = c["incentive"]["confidential_fee_bps_dune_alltime"]
    je = c["jump_explained"]
    v["jump_rise"], v["jump_share_change"] = je["rise_bps"], je["confidential_share_change"]
    v["jump_levels"], v["jump_dune"], v["jump_fd"] = (je["share_of_rise_explained"][k] for k in ("levels_fit", "dune_fee_table", "first_difference_fit"))
    ms = c["monthly_confidential_share"]
    v["conf_share_aug"], v["conf_share_sep"], v["conf_share_oct"] = ms["2026-08"], ms["2026-09"], ms["2026-10"]
    inc, cf, nt = c["incentive"], c["counterfactual"], c["near_terms"]
    v["drop1_usd"], v["drop1_price"] = inc["drop1_usd_at_conversion"], inc["near_price_at_conversion"]
    v["conf_vol_since_launch"] = inc["confidential_volume_jun15_oct_usd"]
    v["conf_rev_lo"] = inc["confidential_volume_jun15_oct_usd"] * v["dune_fee_bps"] / 1e4
    v["conf_rev_hi"] = inc["confidential_volume_jun15_oct_usd"] * v["fit_conf"] / 1e4
    v["take_mayaug"], v["sepoct_at_old"], v["sepoct_actual"], v["uplift"] = cf["may_aug_take_bps"], cf["sep_oct_at_may_aug_take_usd"], cf["sep_oct_actual_usd"], cf["uplift_usd"]
    v["drop1_over_uplift"] = v["drop1_usd"] / v["uplift"]
    v["uplift_near"], v["net_near"] = nt["uplift_near"], nt["net_near_removed"]
    oos = c["out_of_sample"]
    v["oos_pred"], v["oos_pred_fd"], v["oos_actual"] = oos["predicted_usd"], oos["predicted_first_difference_usd"], oos["actual_usd"]
    v["oos_over_levels"], v["oos_over_fd"] = 1 / oos["actual_over_predicted"], 1 / oos["actual_over_predicted_first_difference"]
    v["oos_conf_share"] = oos["confidential_share"]
    h = c["h41"]
    v["tvl_snap"], v["tvl_snap_30d"] = h["tvl_at_snapshot_usd"], h["tvl_30d_after_usd"]

    # 4. Supply, valuation, Monte Carlo
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True).loc["2026-02-01":]
    v["offset_month_min"], v["offset_month_max"] = sm["captured_share_of_issuance"].min(), sm["captured_share_of_issuance"].max()
    hy = pd.read_csv(OUT / "holder_yield.csv").set_index("measure")["value"]
    v["issuance"] = hy.iloc[0]
    v["buyback_rate"], v["net_growth"], v["staked"], v["staker_reward"] = hy.iloc[1], hy.iloc[2], hy.iloc[3], hy.iloc[4]
    v["breakeven_now"] = 1 / v["issuance"]
    v["breakeven_cut"] = 1 / (v["issuance"] * 1.6 / 2.5)
    comps = pd.read_csv(OUT / "comps.csv")
    peers = comps[(comps.token != "NEAR") & comps.mcap_to_holders_revenue.notna() & (comps.holders_revenue_30d_usd >= 100_000)]
    near = comps[comps.token == "NEAR"].iloc[0]
    v["peers_n"], v["peers_median"] = len(peers), peers.mcap_to_holders_revenue.median()
    v["peers_q1"], v["peers_q3"] = peers.mcap_to_holders_revenue.quantile(0.25), peers.mcap_to_holders_revenue.quantile(0.75)
    v["near_holders_mult"] = near.mcap_to_holders_revenue
    v["near_mcap"] = near.market_cap_usd
    v["near_value_at_peer"] = near.annualised_usd * v["peers_median"]
    v["share_not_revenue"] = 1 - v["near_value_at_peer"] / v["near_mcap"]
    from .analysis.ledger import near_price
    v["price_now"] = float(near_price().dropna().iloc[-1])
    v["price_date"] = str(near_price().dropna().index[-1])[:10]
    v["price_at_peer"] = v["price_now"] * v["near_value_at_peer"] / v["near_mcap"]
    r30 = rev["rebuilt_total_usd"].loc[:complete.max()].iloc[-30:].sum() * 365 / 30
    v["near_captured_mult"] = v["near_mcap"] / r30
    v["r30_from"], v["r30_to"] = str(complete.max() - pd.Timedelta(days=29))[:10], str(complete.max())[:10]
    v["r30_annual"] = r30
    v["mcap_date"] = sorted((RAW / "comps").glob("*.json"))[-1].stem[:10]
    sc = pd.read_csv(OUT / "montecarlo_scenarios.csv").set_index("name")
    pick = {"base": "base: take now, 365d history", "mayaug": "take back to May–Aug level", "wind": "incentive winds down over 6 months",
            "cut": "base + issuance cut (HSP-029, earliest start)", "windcut": "incentive winds down + issuance cut",
            "bbonly": "base, buyback wallet only counted as retired", "double": "take doubles again", "bull": "take now, 180d history (bull)"}
    for k, name in pick.items():
        r = sc.loc[name]
        v[f"mc_{k}_med"], v[f"mc_{k}_p10"], v[f"mc_{k}_p90"], v[f"mc_{k}_p"] = r.median_offset_2027, r.p10_offset_2027, r.p90_offset_2027, r.p_2027_net_deflationary
        v[f"mc_{k}_take"] = r.take_bps
        v[f"mc_{k}_vol_dec27"] = r.median_volume_dec2027_musd
    sens = pd.read_csv(OUT / "montecarlo_sensitivity.csv")
    first_vol = float(sens.volume.iloc[0].strip("$").split("M")[0])
    for key, col in zip(("old", "now", "8", "11", "15"), sens.columns[1:]):
        v[f"be_vol_{key}"] = first_vol / sens[col].iloc[0]  # $M/day at which offset = 100%
    v["take_now"] = float(sens.columns[2].split()[0])
    v["volume0"] = first_vol
    gov = _json("governance_hsp029.json")
    v["hsp_for"], v["hsp_turnout"], v["hsp_voters"] = gov["share_for_of_cast"], gov["turnout"], gov["voters"]
    v["hsp_timelock_end"], v["hsp_earliest"] = gov["timelock_ends"][:10], gov["earliest_ramp_start"]
    v["hsp_status"] = gov["status"]
    risk = pd.read_csv(OUT / "token_risk.csv")
    near_all = risk[(risk.asset == "NEAR") & (risk.window == "since Nov 2024")].iloc[0]
    btc_all = risk[(risk.asset == "BTC") & (risk.window == "since Nov 2024")].iloc[0]
    v["near_vol"], v["btc_vol"], v["near_maxdd"], v["near_underwater"] = near_all.annualised_vol, btc_all.annualised_vol, near_all.max_drawdown, near_all.longest_underwater_days
    v["kill1"] = hr.loc[:complete.max()].iloc[-30:].sum() / (hr.loc[:complete.max()].iloc[-180:].sum() / 6)
    ll = _json("leadlag_summary.json")
    v["ll_weeks"], v["ll_sig"], v["ll_tests"] = ll["weeks"], ll["significant_after_holm"], ll["tests"]
    v["ll_best_r"], v["ll_best_p"], v["ll_best_series"], v["ll_best_lag"] = (ll["best_usage_leads_price"][k] for k in ("r", "p", "series", "lag_weeks"))
    v["ll_beta"] = ll["beta_near_btc"]
    tr = ll["tracks_captured_revenue_weekly_r"]
    v["ll_rev_vol"], v["ll_rev_txns"], v["ll_rev_active"], v["ll_rev_price"], v["ll_rev_weeks"] = tr["intents_volume"], tr["txns"], tr["active_accounts"], tr["near_vs_btc"], tr["weeks"]
    v["yoy_vol"], v["yoy_txns"], v["yoy_active"] = (ll["yoy_30d"][k] for k in ("intents_volume", "l1_txns", "l1_active_accounts"))
    # 1Click (swap-level, last 30 days of the collection)
    fs = pd.read_csv(OUT / "fee_shares_last30d.csv", index_col=0)
    v["oc_fee_shares"] = fs
    ra = pd.read_csv(OUT / "revenue_by_asset_last30d.csv", index_col=0)
    v["oc_assets"] = ra
    nov = _json("oneclick_november.json")
    v["oc"] = nov
    v["data_to"] = str(complete.max().date())
    return v


def figures() -> dict[str, str]:
    """Formatted values for the templates."""
    v = values()
    f = {
        "data_to": v["data_to"],
        "rev_rebuilt": usd(v["rev_rebuilt"]), "rev_llama": usd(v["rev_llama"]), "rev_ratio": f"{v['rev_ratio']:.3f}",
        "rev_gap": pct(abs(1 - v["rev_ratio"]), 1), "rev_end": str(v["rev_end"].date()),
        "rev_rebuilt_exact": f"${v['rev_rebuilt']:,.0f}", "rev_llama_exact": f"${v['rev_llama']:,.0f}",
        "rev_month_band": f"{pct(v['rev_month_ratio_min'] - 1)} to +{pct(v['rev_month_ratio_max'] - 1)}".replace("+-", "-"),
        "share_buyback_wallet": pct(v["share_buyback_wallet"]), "share_fefunds": pct(v["share_fefunds"]), "share_1cs": pct(v["share_1cs"]),
        "near_out_all": num(v["near_out_all"]), "near_out_share": pct(v["near_out_share"], 1),
        "fefunds_near": near_m(v["fefunds_near"], 1), "fefunds_share": pct(v["fefunds_share"]),
        "wallets_official": near_m(v["wallets_official"], 3), "wallets_rebuilt": near_m(v["wallets_rebuilt"], 3), "wallets_gap": pct(v["wallets_gap"], 2),
        "offset_rebuilt": pct(v["offset_rebuilt"], 1), "offset_official": pct(v["offset_official"], 1),
        "offset_per100": f"{v['offset_rebuilt'] * 100:.0f}", "offset_per100_official": f"{v['offset_official'] * 100:.0f}",
        "issued_feb_oct": near_m(v["issued_feb_oct"], 1), "captured_feb_oct": near_m(v["captured_feb_oct"], 2),
        "emissions_gap": pct(v["emissions_official"] / v["issued_feb_oct"] - 1, 1),
        "offset_month_min": pct(v["offset_month_min"]), "offset_month_max": pct(v["offset_month_max"]),
        "series_over_wallets": pct(v["series_over_wallets"] - 1), "series_ratio_min": f"{v['series_ratio_min']:.2f}", "series_ratio_max": f"{v['series_ratio_max']:.2f}",
        "series_take_oct": f"{v['series_take_oct']:.1f}", "series_take_nov": f"{v['series_take_nov']:.1f}",
        "cap_total_all": pct(v["cap_total_all_time"]), "cap_total_d30": pct(v["cap_total_d30"]),
        "cap_fe_all": pct(v["cap_front_end_fees_all_time"]), "cap_fe_d30": pct(v["cap_front_end_fees_d30"]),
        "cap_b2b_all": pct(v["cap_b2b_partners_all_time"]), "cap_b2b_d30": pct(v["cap_b2b_partners_d30"]),
        "cap_qi_all": pct(v["cap_quote_improvement_all_time"]), "cap_qi_d30": pct(v["cap_quote_improvement_d30"]),
        "take_aug": f"{v['take_aug']:.1f}", "take_sep": f"{v['take_sep']:.1f}", "take_oct": f"{v['take_oct']:.1f}",
        "gross_bps_oct": f"{v['gross_bps_oct']:.0f}", "capture_oct": pct(v["capture_oct"]),
        "take_last_week": f"{v['take_last_week']:.1f}", "capture_last_week": pct(v["capture_last_week"]), "gross_last_week": f"{v['gross_last_week']:.0f}",
        "take_nov_llama": f"{v['take_nov_llama']:.1f}",
        "tvl_last": usd(v["tvl_last"], 0), "tvl_last_date": v["tvl_last_date"], "tvl_peak": usd(v["tvl_peak"], 0), "tvl_peak_date": v["tvl_peak_date"],
        "tvl_from_peak": pct(-v["tvl_from_peak"]), "tvl_30d": pct(-v["tvl_30d"]),
        "tvl_snap": usd(v["tvl_snap"], 0), "tvl_snap_30d": usd(v["tvl_snap_30d"], 0),
        "fit_weeks": str(v["fit_weeks"]), "fit_conf": f"{v['fit_conf']:.1f}", "fit_pub": f"{v['fit_pub']:.1f}", "fit_r2": f"{v['fit_r2']:.2f}",
        "fit_ci": f"{v['fit_ci_lo']:.1f}–{v['fit_ci_hi']:.1f}", "fd_conf": f"{v['fd_conf']:.1f}", "fd_pub": f"{v['fd_pub']:.1f}",
        "fd_ci": f"{v['fd_ci_lo']:.1f}–{v['fd_ci_hi']:.1f}", "loo": f"{v['loo_lo']:.1f}–{v['loo_hi']:.1f}", "daily_fit_conf": f"{v['daily_fit_conf']:.1f}",
        "corr_conf_buyback": f"{v['corr_conf_buyback']:.2f}", "corr_pub_buyback": f"{v['corr_pub_buyback']:.2f}",
        "dune_fee_bps": f"{v['dune_fee_bps']:.1f}",
        "premium_range": f"{min(v['fd_conf'], v['dune_fee_bps']):.1f}–{v['fit_conf']:.0f}", "public_range": f"{min(v['fit_pub'], v['fd_pub']):.0f}–{max(v['fit_pub'], v['fd_pub']):.0f}",
        "jump_rise": f"{v['jump_rise']:.1f}", "jump_share_change": f"{v['jump_share_change'] * 100:.0f}",
        "jump_levels": pct(v["jump_levels"]), "jump_dune": pct(v["jump_dune"]), "jump_fd": pct(v["jump_fd"]),
        "conf_share_aug": pct(v["conf_share_aug"]), "conf_share_sep": pct(v["conf_share_sep"]), "conf_share_oct": pct(v["conf_share_oct"]),
        "drop1_usd": usd(v["drop1_usd"]), "conf_vol_since_launch": usd(v["conf_vol_since_launch"]),
        "conf_rev_range": f"{usd(v['conf_rev_lo'], 1)}–{usd(v['conf_rev_hi'], 1)}",
        "take_mayaug": f"{v['take_mayaug']:.1f}", "sepoct_at_old": usd(v["sepoct_at_old"]), "sepoct_actual": usd(v["sepoct_actual"]), "uplift": usd(v["uplift"]),
        "drop1_over_uplift": pct(v["drop1_over_uplift"]), "uplift_over_drop1": f"{1 / v['drop1_over_uplift']:.2f}x",
        "uplift_near": f"{v['uplift_near'] / 1e3:.0f}k", "net_near": f"{v['net_near'] / 1e3:.0f}k",
        "oos_pred": usd(v["oos_pred"]), "oos_pred_fd": usd(v["oos_pred_fd"]), "oos_actual": usd(v["oos_actual"]),
        "oos_over_levels": f"{v['oos_over_levels']:.1f}x", "oos_over_fd": f"{v['oos_over_fd']:.1f}x", "oos_conf_share": pct(v["oos_conf_share"]),
        "issuance": pct(v["issuance"], 2), "buyback_rate": pct(v["buyback_rate"], 1), "net_growth": pct(v["net_growth"], 1),
        "staked": pct(v["staked"]), "staker_reward": pct(v["staker_reward"], 1),
        "breakeven_now": mult(v["breakeven_now"]), "breakeven_cut": mult(v["breakeven_cut"]),
        "near_captured_mult": mult(v["near_captured_mult"]), "near_holders_mult": mult(v["near_holders_mult"]),
        "peers_n": str(v["peers_n"]), "peers_median": mult(v["peers_median"]), "peers_iqr": f"{v['peers_q1']:.0f}–{v['peers_q3']:.0f}x",
        "offset_window": "{} to {}".format(*[pd.Timestamp(m + "-01").strftime("%B %Y") for m in v["offset_months"]]),
        "r30_from": v["r30_from"], "r30_to": v["r30_to"], "r30_annual": usd(v["r30_annual"], 1), "mcap_date": v["mcap_date"],
        "near_mcap": usd(v["near_mcap"], 1), "near_value_at_peer": usd(v["near_value_at_peer"], 0), "share_not_revenue": pct(v["share_not_revenue"]), "price_now": f"${v['price_now']:.2f}", "price_date": v["price_date"], "price_at_peer": f"${v['price_at_peer']:.2f}",
        "take_now": f"{v['take_now']:.1f}", "volume0": f"${v['volume0']:.0f}M",
        "be_vol_now": f"${v['be_vol_now']:.0f}M", "be_vol_8": f"${v['be_vol_8']:.0f}M", "be_vol_15": f"${v['be_vol_15']:.0f}M",
        "hsp_for": pct(v["hsp_for"], 2), "hsp_turnout": pct(v["hsp_turnout"]), "hsp_voters": str(v["hsp_voters"]),
        "hsp_timelock_end": v["hsp_timelock_end"], "hsp_earliest": v["hsp_earliest"], "hsp_status": v["hsp_status"],
        "near_vol": pct(v["near_vol"]), "btc_vol": pct(v["btc_vol"]), "near_maxdd": pct(v["near_maxdd"]), "near_underwater": str(int(v["near_underwater"])),
        "kill1": pct(v["kill1"]),
        "ll_weeks": str(v["ll_weeks"]), "ll_sig": str(v["ll_sig"]), "ll_tests": str(v["ll_tests"]),
        "ll_best": f"r = {v['ll_best_r']:+.2f}, p = {v['ll_best_p']:.2f} before correction ({ {'txns': 'L1 transactions', 'intents_volume': 'Intents volume', 'active_accounts': 'L1 active accounts'}[v['ll_best_series']] }, {v['ll_best_lag']}-week lag)",
        "ll_beta": f"{v['ll_beta']:.2f}", "ll_rev_vol": f"{v['ll_rev_vol']:.2f}", "ll_rev_txns": f"{v['ll_rev_txns']:.2f}",
        "ll_rev_active": f"{v['ll_rev_active']:.2f}", "ll_rev_price": f"{v['ll_rev_price']:.2f}", "ll_rev_weeks": str(v["ll_rev_weeks"]),
        "yoy_vol": f"{v['yoy_vol'] * 100:+.0f}%", "yoy_txns": f"{v['yoy_txns'] * 100:+.0f}%", "yoy_active": f"{v['yoy_active'] * 100:+.0f}%",
    }
    fs, ra, oc = v["oc_fee_shares"], v["oc_assets"], v["oc"]
    sk = fs.loc["swapkit"]
    o1, o2, tb = oc["oct16_29"], oc["nov01_10"], oc["trust_burst_oct23_28"]
    f.update({
        "oc_from": oc["last30"]["from"], "oc_to": oc["last30"]["to"], "oc_swaps": f"{oc['last30']['swaps_collected'] / 1e6:.1f}M", "oc_swaps_30": f"{oc['last30']['swaps'] / 1e3:.0f}k",
        "oc_integrators_keep": pct(1 - oc["last30"]["near_share_of_fee_pool"]),
        "sk_vol": pct(sk.volume_share), "sk_fees": pct(sk.fee_share),
        "sk_near": "under 0.1%" if sk.near_revenue_share < 0.001 else pct(sk.near_revenue_share, 1),
        "noref_vol": pct(fs.loc["(none)"].volume_share), "noref_near": pct(fs.loc["(none)"].near_revenue_share),
        "asset_btc": pct(ra.loc["BTC", "near_revenue_share"]) if "BTC" in ra.index else "n/a",
        "asset_zec": pct(ra.loc["ZEC", "near_revenue_share"]) if "ZEC" in ra.index else "n/a",
        "asset_eth": pct(ra.loc["ETH", "near_revenue_share"]) if "ETH" in ra.index else "n/a",
        "asset_stable_vol": pct(ra.loc["stable↔stable", "volume_share"]), "asset_stable_near": pct(ra.loc["stable↔stable", "near_revenue_share"]),
        "asset_stable_bps": f"{ra.loc['stable↔stable', 'near_bps']:.1f}",
        "oc_bps_oct": f"{o1['near_bps']:.1f}", "oc_bps_nov": f"{o2['near_bps']:.1f}",
        "oc_bps_oct_ex": f"{o1['near_bps_ex_trust']:.1f}", "oc_bps_nov_ex": f"{o2['near_bps_ex_trust']:.1f}",
        "trust_burst_vol": usd(tb["volume_usd"], 0), "trust_burst_near": usd(tb["near_usd"], 0), "trust_burst_zec": pct(tb["zec_share"]),
        "trust_share_oct": pct(o1["trust_near_share"]),
        "noref_day_oct": usd(o1["noref_near_usd_per_day"], 1), "noref_day_nov": usd(o2["noref_near_usd_per_day"], 1),
        "noref_share_nov": pct(o2["noref_near_share"]),
        "zec_vol_oct": pct(o1["zec_volume_share"]), "zec_vol_nov": pct(o2["zec_volume_share"]),
        "zec_near_oct": pct(o1["zec_near_share"]), "zec_near_nov": pct(o2["zec_near_share"]),
        "oc_vol_oct": usd(o1["volume_usd_per_day"], 0), "oc_vol_nov": usd(o2["volume_usd_per_day"], 0),
    })
    names = {"(none)": "No integrator (NEAR's front-end, direct users)", "swapkit": "SwapKit", "trustwallet": "Trust Wallet", "lifi": "LI.FI",
             "rango": "Rango", "arbie": "Arbie", "zodl": "Zodl", "e1a72603-64b3-4be1-8265-8bae5970d396": "Anonymous referral `e1a72603…`"}
    top = pd.concat([fs.loc[["swapkit"]], fs.drop(index="swapkit").sort_values("near_revenue_share", ascending=False).head(5)])
    rows = ["| Integrator | Volume | App fees | NEAR's revenue |", "| --- | --- | --- | --- |"]
    rows += [f"| {names.get(i, i)} | {pct(r.volume_share, 1)} | {pct(r.fee_share, 1)} | {pct(r.near_revenue_share, 1)} |" for i, r in top.iterrows()]
    f["oc_table"] = "\n".join(rows)
    for k in ("base", "mayaug", "wind", "cut", "windcut", "bbonly", "double", "bull"):
        f[f"mc_{k}"] = pct(v[f"mc_{k}_med"])
        f[f"mc_{k}_band"] = f"{v[f'mc_{k}_p10'] * 100:.0f}–{v[f'mc_{k}_p90'] * 100:.0f}%"
        f[f"mc_{k}_p"] = pct(v[f"mc_{k}_p"])
        f[f"mc_{k}_take"] = f"{v[f'mc_{k}_take']:.1f}"
    f["mc_bull_vol_mult"] = f"{v['mc_bull_vol_dec27'] / v['volume0']:.0f}x"
    q = _json("oneclick_quality.json")
    f.update({"q_senders": f"{q['senders'] / 1e3:.0f}k", "q_one_swap": pct(q["one_swap_senders"]), "q_top10": pct(q["top10_volume"]),
              "q_top100": pct(q["top100_volume"]), "q_heavy_n": str(q["senders_100plus_swaps"]), "q_heavy_vol": pct(q["senders_100plus_volume"]),
              "q_heavy_rev": pct(q["senders_100plus_near_revenue"]), "q_rt_vol": pct(q["round_trip_volume"], 1),
              "q_rt_rev": pct(q["round_trip_near_revenue"], 1), "q_rt_ref": pct(q["round_trip_top_integrator"][1]),
              "q_hhi": f"{q['hhi_volume']:.0f}", "q_with_sender": pct(q["swaps_with_sender"])})
    f["outputs_n"] = str(len(list(OUT.glob("*"))) + 1)
    oq = _json("open_questions.json")
    bb, fe, g = oq["confidential_fee"]["buyback multisig"], oq["confidential_fee"]["front-end fund"], oq["revenue_gap"]
    f.update({"oq_bb_conf": f"{bb['confidential_bps']:.1f}", "oq_bb_band": f"{bb['boot_p5']:.1f}–{bb['boot_p95']:.1f}", "oq_bb_loo": f"{bb['loo_min']:.1f}–{bb['loo_max']:.1f}",
              "oq_bb_fd": f"{bb['first_diff_confidential_bps']:.1f}", "oq_bb_pub": f"{bb['public_bps']:.1f}", "oq_bb_corr": f"{bb['corr_with_confidential']:.2f}",
              "oq_bb_corr_pub": f"{bb['corr_with_public']:.2f}", "oq_fe_conf": f"{fe['confidential_bps']:.1f}", "oq_fe_fd": f"{fe['first_diff_confidential_bps']:.1f}",
              "oq_weeks": str(oq["confidential_fee"]["weeks"]),
              "oq_qi_share": pct(g["ytd"]["quote_improvement_share_of_reported"]), "oq_gap_ytd": pct(g["ytd"]["reported_over_wallets"] - 1),
              "oq_gap_ytd_ex": pct(g["ytd"]["without_quote_improvement_over_wallets"] - 1, 1), "oq_gap_d30": pct(g["d30"]["reported_over_wallets"] - 1),
              "oq_gap_d30_ex": pct(g["d30"]["without_quote_improvement_over_wallets"] - 1, 1), "oq_gap_all": pct(g["all_time"]["reported_over_wallets"] - 1),
              "oq_gap_all_ex": pct(g["all_time"]["without_quote_improvement_over_wallets"] - 1, 1), "oq_gap_d7": pct(g["d7"]["reported_over_wallets"] - 1),
              "oq_gap_d7_ex": pct(g["d7"]["without_quote_improvement_over_wallets"] - 1, 1), "oq_qi_ytd_usd": usd(g["ytd"]["quote_improvement_usd"])})
    f["log_n"] = str(len(re.findall(r"^### \d+\.", (ROOT / "RESEARCH_LOG.md").read_text(), re.M)))
    bq = _json("bigquery_crosscheck.json")
    f.update({"bq_rev_near": f"{bq['revenue']['near_bigquery'] / 1e6:.3f}M", "bq_rev_gap": "0 (identical to the last digit)" if bq['revenue']['max_monthly_gap'] < 1e-9 else pct(bq['revenue']['max_monthly_gap'], 3),
              "bq_rev_to": bq["revenue"]["to"], "bq_supply_gap": pct(bq["supply"]["issued_gap"], 2), "bq_issued": f"{bq['supply']['issued_feb_oct_bigquery'] / 1e6:.2f}M",
              "bq_rpc_n": str(bq["supply"]["rpc_samples"]), "bq_days": str(bq["activity"]["days"]),
              "bq_intents_tx_25": pct(bq["activity"]["intents_share_of_txns_oct2025"], 1), "bq_intents_tx_26": pct(bq["activity"]["intents_share_of_txns_oct2026"], 1)})
    rv = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    f.update(follow_100(v))
    sc = _json("swap_cost.json")
    s30 = sc["last30"]
    c100 = lambda b: f"${b / 100:.2f}"  # bps of $100 in dollars  # noqa: E731
    f.update({"sc_from": sc["from"], "sc_to": sc["to"], "sc_swaps": f"{s30['swaps']:,}", "sc_cost": f"{s30['cost_bps']:.0f}",
              "sc_int": f"{s30['integrators_bps']:.0f}", "sc_near": f"{s30['near_bps']:.1f}", "sc_rest": f"{s30['solvers_networks_bps']:.0f}",
              "sc_near_share": pct(s30["near_share_of_cost"], 1), "sc_cost_100": c100(s30["cost_bps"]), "sc_int_100": c100(s30["integrators_bps"]),
              "sc_near_100": c100(s30["near_bps"]), "sc_rest_100": c100(s30["solvers_networks_bps"]),
              "sc_small": f"{sc['by_size']['under $10']['cost_bps']:.0f}", "sc_mid": f"{sc['by_size']['$3k-10k']['cost_bps']:.0f}",
              "sc_left": pct(sc["left_out_last30"]["share_of_volume"], 3)})
    lines = ["| Swap size | Swaps | User pays | Integrators | NEAR | Solvers and networks |", "| --- | --- | --- | --- | --- | --- |"]
    for b, x in sc["by_size"].items():
        few = " (too few swaps to read)" if x["swaps"] < 100 else ""
        lines.append(f"| {b}{few} | {x['swaps']:,} | {x['cost_bps']:.0f} bps | {x['integrators_bps']:.0f} | {x['near_bps']:.1f} | {x['solvers_networks_bps']:.0f} |")
    lines.append(f"| **All** | {s30['swaps']:,} | **{s30['cost_bps']:.0f} bps** | {s30['integrators_bps']:.0f} | {s30['near_bps']:.1f} | {s30['solvers_networks_bps']:.0f} |")
    f["sc_table"] = "\n".join(lines)
    follow = [(10, "$10-30"), (100, "$100-300"), (1_000, "$1k-3k"), (10_000, "$10k-30k"), (100_000, "$100k-300k"), (1_000_000, "$300k-1M")]
    money = lambda x: f"${x:,.2f}" if x < 100 else f"${x:,.0f}"  # noqa: E731
    lines = ["| You swap | You give up | to integrators | to NEAR | to solvers and networks | NEAR's share |", "| --- | --- | --- | --- | --- | --- |"]
    for amt, b in follow:
        x = sc["by_size"][b]
        lines.append(f"| ${amt:,} | **{money(amt * x['cost_bps'] / 1e4)}** ({x['cost_bps']:.0f} bps) | {money(amt * x['integrators_bps'] / 1e4)} | "
                     f"{money(amt * x['near_bps'] / 1e4)} | {money(amt * x['solvers_networks_bps'] / 1e4)} | {pct(x['near_bps'] / x['cost_bps'])} |")
    f["sc_follow_table"] = "\n".join(lines)
    bs = sc["by_size"]
    flat = [bs[b]["cost_bps"] for b in ("$3k-10k", "$10k-30k", "$30k-100k")]
    f.update({"sc_tiny": f"{bs['under $10']['cost_bps']:.0f}", "sc_flat_lo": f"{min(flat):.0f}", "sc_flat_hi": f"{max(flat):.0f}",
              "sc_big": f"{bs['$300k-1M']['cost_bps']:.0f}", "sc_big_rest": f"{bs['$300k-1M']['solvers_networks_bps']:.0f}",
              "sc_flat_rest": f"{bs['$3k-10k']['solvers_networks_bps']:.0f}", "sc_big_near": f"{bs['$300k-1M']['near_bps']:.1f}",
              "sc_10_cost": f"${10 * bs['$10-30']['cost_bps'] / 1e4:.2f}"})
    el = _json("elasticity.json")
    cs = el["cross_section"]
    f.update({"el_n": str(cs["integrators"]), "el_rho": f"{cs['spearman']:+.2f}".replace("-", "−"), "el_p": f"{cs['p']:.2f}",
              "el_rises": str(el["fee_rises"]), "el_cuts": str(el["fee_cuts"]), "el_rise_vol": spct(el["fee_rises_median_volume"]),
              "el_cut_vol": spct(el["fee_cuts_median_volume"]),
              "el_hi_g": spct(cs["by_fee_band"]["60+ bps"]["median_relative_growth"]), "el_hi_n": str(cs["by_fee_band"]["60+ bps"]["integrators"]),
              "el_hi_v": usd(cs["by_fee_band"]["60+ bps"]["volume_before_usd"], 0), "el_lo_g": spct(cs["by_fee_band"]["0-10 bps"]["median_relative_growth"]),
              "el_lo_n": str(cs["by_fee_band"]["0-10 bps"]["integrators"])})
    sg_ = _json("signers.json")
    f.update({"sg_heavy_n": f"{sg_['heavy_signers_median']:.0f}", "sg_heavy_first": pct(sg_["heavy_share_first"]), "sg_heavy_last": pct(sg_["heavy_share_last"]),
              "sg_light_share": pct(sg_["light_share_last"]), "sg_light": f"{sg_['light_signers_last4'] / 1e3:.0f}k", "sg_light_first": f"{sg_['light_signers_first4'] / 1e6:.1f}M",
              "sg_yoy": spct(sg_["light_signers_yoy"]), "sg_bursts": str(len(sg_["bursts"])), "sg_tests": str(sg_["lead_lag_tests"]),
              "sg_sig": str(sg_["lead_lag_significant_holm"]), "sg_best_r": f"{sg_['lead_lag_best']['r']:+.2f}", "sg_best_p": f"{sg_['lead_lag_best']['p']:.2f}",
              "sg_vol_r": f"{sg_['same_week_corr']['intents_volume']:+.2f}".replace("-", "−"), "sg_rev_r": f"{sg_['light_vs_revenue_since_march']:+.2f}",
              "sg_bot_drop": spct(sg_["heavy_txns_drop_2026_04"]), "sg_weeks": str(sg_["weeks"]),
              "sg_tg_share": pct(sg_["tg_share_of_light_last4"]), "sg_non_tg": f"{sg_['light_non_tg_last4'] / 1e3:.0f}k",
              "sg_non_tg_yoy": spct(sg_["light_non_tg_yoy"]),
              "sg_non_tg_vol_r": f"{sg_['same_week_corr_non_tg']['intents_volume']:+.2f}".replace("-", "−")})
    ct = _json("control.json")
    ms, fe, oc = ct["multisig"], ct["daos"]["fefundsadmin.sputnik-dao.near"], ct["daos"]["1csfundsadmin.sputnik-dao.near"]
    implicit = oc["near_paid_out_by_recipient"].get("an implicit account", 0.0)
    f.update({"ct_date": ct["read_at"][:10], "ct_ms_conf": str(ms["confirmations"]), "ct_ms_keys": str(ms["keys"]), "ct_ms_fak": str(ms["full_access_keys"]),
              "ct_ms_requests": str(ms["requests_ever"]), "ct_ms_out": f"{ms['near_sent_out']:,.0f}", "ct_ms_bal": f"{ms['balance_near'] / 1e6:.2f}M",
              "ct_ms_out_share": pct(ms["near_sent_out"] / (ms["near_sent_out"] + ms["balance_near"]), 1),
              "ct_fe_members": str(fe["members"]), "ct_fe_pay": str(fe["approvals_to_transfer"]), "ct_fe_policy": str(fe["approvals_to_change_policy"]),
              "ct_fe_props": str(fe["proposals"]), "ct_fe_policy_changes": str(len(fe["policy_changes"])),
              "ct_fe_policy_change_day": fe["policy_changes"][0]["day"] if fe["policy_changes"] else "",
              "ct_fe_stable": usd(fe["stablecoins_paid_usd"], 2), "ct_fe_stable_since": f"${fe['stablecoins_paid_since_buybacks_usd'] / 1e3:,.0f}k",
              "ct_fe_liq": usd(fe["stablecoins_by_recipient"].get("auroraliqsupport.near", 0.0), 2),
              "ct_fe_bal": f"{fe['balance_near'] / 1e6:.2f}M",
              "ct_oc_members": str(oc["members"]), "ct_oc_pay": str(oc["approvals_to_transfer"]), "ct_oc_one": str(len(oc["approved_with_one_vote"])),
              "ct_oc_implicit": f"{implicit:,.0f}", "ct_oc_to_bb": f"{oc['near_paid_out_by_recipient'].get('buybacks.multisignature.near', 0.0) / 1e3:,.0f}k",
              "ct_fee_pips": str(ct["intents_protocol_fee_pips"]), "ct_held": f"{ct['held_near'] / 1e6:.2f}M",
              "ct_one_signer": pct(ct["held_where_one_signer_can_change_the_rules"]),
              "ct_block": f"{min(b for b in ct['block_heights'].values() if b):,}", "ct_payments_table": control_table(ct)})
    tr = _json("treasury.json")
    f.update({"tr_moved": f"{tr['moved_out_2026_near'] / 1e6:.2f}M", "tr_x": f"{tr['moved_over_captured']:.0f}", "tr_staked1": f"{tr['staked_first_near'] / 1e6:.1f}M",
              "tr_unstaked_day": tr["unstaked_day"], "tr_endow": f"{tr['foundation_endowment_joined_near'] / 1e6:.0f}M",
              "tr_staked2": f"{tr['staked_again_near'] / 1e6:.1f}M", "tr_staked2_day": tr["staked_again_days"][1],
              "tr_captured": f"{tr['captured_by_revenue_wallets_near'] / 1e6:.2f}M"})
    im = _json("implied.json")
    pm = {(x["discount"], x["growth"]): x for x in im["perpetuity"]}
    fv = {x["discount"]: x for x in im["five_years_then_peer_multiple"]}
    f.update({"im_lo": f"{min(x['times_today'] for x in im['perpetuity']):.0f}", "im_hi": f"{max(x['times_today'] for x in im['perpetuity']):.0f}",
              "im_mid": f"{pm[(0.15, 0.03)]['times_today']:.0f}", "im_mid_vol": usd(pm[(0.15, 0.03)]["volume_per_day_usd"], 1),
              "im_g5": pct(fv[0.15]["growth_per_year"]), "im_g5_lo": pct(fv[0.10]["growth_per_year"]), "im_g5_hi": pct(fv[0.20]["growth_per_year"]),
              "im_peer": f"{im['peer_median_multiple']:.0f}x", "im_volg": spct(im["volume_growth_last_30d_vs_year_before"]), "im_take": f"{im['take_bps']:.1f}"})
    lines = ["| Discount rate | Growth 0% | Growth 3% | Growth 5% | Or: growth a year for 5 years, then the peer multiple |", "| --- | --- | --- | --- | --- |"]
    for r in (0.10, 0.15, 0.20):
        lines.append(f"| {r:.0%} | " + " | ".join(f"{pm[(r, g)]['times_today']:.0f}x" for g in (0.0, 0.03, 0.05)) + f" | {pct(fv[r]['growth_per_year'])} |")
    f["im_table"] = "\n".join(lines)
    rb = pd.read_csv(OUT / "robustness.csv").fillna({"note": ""})
    rj = _json("robustness.json")
    fmt = {"F1": lambda x: f"ratio {x:.3f}", "F3": lambda x: pct(x, 1), "F4": lambda x: f"{x:.0f}x", "F5": lambda x: f"{x:.2f}x",
           "F8": lambda x: f"cost {pct(x)} of uplift", "F10": lambda x: f"{x:.2f}x", "F11": lambda x: pct(x), "F12": lambda x: f"{x:.0f}x",
           "F13": lambda x: f"r = {x:.2f}"}
    worst = {"F1": lambda a: (a["value"] - 1).abs().idxmax(), "F3": lambda a: a["value"].idxmax(), "F4": lambda a: a["value"].idxmin(),
             "F5": lambda a: a["value"].idxmin(), "F8": lambda a: a["value"].idxmax(), "F10": lambda a: a["value"].idxmin(),
             "F11": lambda a: a["value"].idxmax(), "F12": lambda a: a["value"].idxmin(), "F13": lambda a: a["value"].idxmax()}
    lines = ["| Finding | Alternatives that hold | Weakest alternative | Where it would break (a test it does not claim) |", "| --- | --- | --- | --- |"]
    for k, g in rb.groupby("finding", sort=False):
        alt, st = g[g["kind"] == "alternative"], g[g["kind"] != "alternative"]
        if len(alt):
            w = alt[~alt["holds"]].iloc[0] if (~alt["holds"]).any() else alt.loc[worst[k](alt)]
            weak = f"{'**flips**: ' if not w['holds'] else ''}{w['variant']}: {fmt[k](w['value'])}"
        else:
            weak = "–"
        brk = "; ".join(f"{r.variant}: {fmt[k](r.value) if k != 'F4' else f'${r.value:.2f}'}" for r in st.itertuples() if r.kind == "stress" and (not r.holds or k == "F4")) or "–"
        if k == "F13":
            brk = "smallest correlation detectable with 80% power over " + " and ".join(f"{r.variant.split(', ')[1]}: {r.value:.2f}" for r in st.itertuples())
        lines.append(f"| {k} | {int(alt['holds'].sum())} of {len(alt)} | {weak} | {brk} |")
    f.update({"rob_table": "\n".join(lines), "rob_variants": str(rj["variants"]), "rob_alt": str(rj["alternatives"]), "rob_alt_hold": str(rj["alternatives_hold"]),
              "rob_fragile": ", ".join(rj["fragile"]) or "none"})
    be = rb[(rb["finding"] == "F4") & (rb["kind"] == "stress")]["value"].iloc[0]
    f["rob_be"] = f"{be:.2f}"
    f["rob_be_drop"] = pct(1 - be / v["price_now"])
    f13p = rb[(rb["finding"] == "F13") & (rb["kind"] == "info")]["value"].tolist()
    f.update({"rob_f13_single": f"{f13p[0]:.2f}", "rob_f13_holm": f"{f13p[1]:.2f}"})
    ic = _json("incident.json")
    ie, ip, ih = ic["event"], ic["placebo"], ic["halt"]
    f.update({"ic_hours": f"{ih['hours']:.1f}", "ic_from": ih["last_swap_before_utc"][11:16], "ic_to": ih["first_swap_after_utc"][11:16],
              "ic_rev_lost": f"${ih['near_revenue_forgone_usd']:,.0f}", "ic_vol_lost": usd(ih["volume_forgone_usd"]),
              "ic_gap_week": f"{ih['longest_gap_in_prior_week_minutes']:.0f}",
              "ic_vol": spct(ie["volume_usd"]["change"]), "ic_vol_p": spct(ip["volume_usd"]["change"]),
              "ic_rev": spct(ie["near_usd"]["change"]), "ic_rev_p": spct(ip["near_usd"]["change"]),
              "ic_riv": spct(ie["rivals_volume"]["change"]), "ic_riv_p": spct(ip["rivals_volume"]["change"]),
              "ic_int": f"{ie['integrators']['before_per_day']:.0f} to {ie['integrators']['after_per_day']:.0f}",
              "ic_kept": str(ie["top_integrators_kept_half"]), "ic_kept_p": str(ip["top_integrators_kept_half"]), "ic_top": str(ie["top_integrators"]),
              "ic_top_vol": spct(ie["top_integrators_volume_change"]), "ic_top_vol_p": spct(ip["top_integrators_volume_change"])})
    pdist, cb = ic["placebo_distribution"], ic["comeback"]
    f.update({"ic_pn": str(pdist["volume_usd_change"]["n"]), "ic_first_hour": pct(ih["first_full_hour_ratio"]), "ic_first_day": pct(ih["first_24h_volume_vs_usual"]),
              "ic_cut": str(cb["cut_back"]), "ic_back": str(cb["back_to_half_by_31oct_12nov"]), "ic_top_nov": spct(cb["top_volume_31oct_12nov_vs_before"]),
              **{f"ic_d_{k}": spct(v["event"]) if "change" in k else str(int(v["event"])) for k, v in pdist.items()},
              **{f"ic_dm_{k}": spct(v["placebo_median"]) if "change" in k else f"{v['placebo_median']:.0f}" for k, v in pdist.items()},
              **{f"ic_dp_{k}": f"{v['p_two_sided']:.2f}" for k, v in pdist.items()},
              "ic_top_vol_pmin": spct(pdist["top_volume_change"]["placebo_min"]), "ic_kept_pmin": str(int(pdist["top_kept_half"]["placebo_min"]))})
    ev = pd.read_csv(OUT / "events.csv")
    ej = _json("events.json")
    cols = [("volume_change", "Intents volume", spct), ("revenue_change", "NEAR revenue", spct),
            ("take_change_bps", "Take", lambda x: f"{x:+.1f} bps".replace("-", "−")), ("share_change_pts", "Share vs rivals", lambda x: f"{x:+.0f} pts".replace("-", "−")),
            ("abnormal_return_3d", "NEAR vs BTC, 3 days", spct), ("abnormal_return_14d", "NEAR vs BTC, 2 weeks", spct)]
    lines = ["| Event | " + " | ".join(c[1] for c in cols) + " |", "| --- |" + " --- |" * len(cols)]
    for e in ej["events"]:
        r = ev[ev["event"] == e["key"]].set_index("measure")
        cell = lambda m, fmt: "–" if m not in r.index else (f"**{fmt(r.loc[m, 'value'])}**" if r.loc[m, "p_two_sided"] <= 0.10 else fmt(r.loc[m, "value"]))  # noqa: E731
        short = {"halving": "Issuance halved", "fee_switch": "Fee switch and Confidential Intents launch", "confidential_ga": "Confidential Intents for all developers",
                 "confidential_1click": "Confidential execution in the 1Click API", "airdrop_snapshot": "NEAR@3.33 Drop 1 snapshot",
                 "exploit": "Freeze and $3.8M exploit", "hsp029": "HSP-029 approved (issuance cap 1.6%)"}[e["key"]]
        lines.append(f"| {short}, {e['date']} | " + " | ".join(cell(m, fmt) for m, _, fmt in cols) + " |")
    f.update({"ev_table": "\n".join(lines), "ev_n": str(len(ej["events"])), "ev_tests": str(len(ev)), "ev_unusual": str(len(ej["unusual"])),
              "ev_expected": f"{len(ev) * 0.1:.0f}", "ev_placebo": str(ej["placebo_dates"])})
    evv = lambda k, m: ev[(ev["event"] == k) & (ev["measure"] == m)]["value"].iloc[0]  # noqa: E731
    f.update({"ev_snap_rev": spct(evv("airdrop_snapshot", "revenue_change")), "ev_snap_px3": spct(evv("airdrop_snapshot", "abnormal_return_3d")),
              "ev_snap_px14": spct(evv("airdrop_snapshot", "abnormal_return_14d")), "ev_hsp_px3": spct(evv("hsp029", "abnormal_return_3d")),
              "ev_exp_px3": spct(evv("exploit", "abnormal_return_3d")), "ev_fs_px3": spct(evv("fee_switch", "abnormal_return_3d")),
              "ev_halv_px3": spct(evv("halving", "abnormal_return_3d")), "ev_halv_vol": spct(evv("halving", "volume_change"))})
    qr = _json("quote_race.json")
    bc = qr["by_corridor_median_gap_bps"]
    sg = lambda x: "0.0 bps" if round(x, 1) == 0 else f"{x:+.1f} bps".replace("-", "−")  # noqa: E731
    f.update({"qr_rounds": str(qr["rounds"]), "qr_swaps": str(qr["quotes_compared"]), "qr_first": qr["first_round"][:16].replace("T", " "),
              "qr_last": qr["last_round"][:16].replace("T", " "), "qr_best_share": pct(qr["oneclick_best_share"]),
              "qr_median": sg(qr["median_gap_vs_best_bps"]), "qr_ex_lifi_median": sg(qr["median_gap_vs_best_ex_lifi_fee_bps"]),
              "qr_c_l2": sg(bc["same asset, EVM L2 to L2"]), "qr_c_l1l2": sg(bc["same asset, Ethereum to L2"]),
              "qr_c_xasset": sg(bc["cross asset, EVM"]), "qr_c_sol": sg(bc["cross chain family, Solana to EVM"]),
              "qr_c_btc": sg(bc["native BTC to EVM"])})
    sr = _json("source_revisions.json")
    fl, rb, nd = sr["defillama"]["gross fees"], sr["rebuilt_from_wallets"], sr["near_dashboard"]["gross fees"]
    big = fl["largest"][0]
    f.update({"rv_snaps": str(len(fl["snapshots"])), "rv_first": fl["snapshots"][0], "rv_last": fl["snapshots"][-1],
              "rv_fee_settle": str(fl["settled_after_days"]), "rv_fee_factor": f"×{big['factor']:.0f}",
              "rv_fee_day": big["day"], "rv_fee_first": f"${big['first']:,.0f}", "rv_fee_latest": f"${big['latest']:,.0f}",
              "rv_fee_moved": str(sum(x["moved_1pct"] for k, x in fl["by_age"].items() if k in ("1", "2"))),
              "rv_fee_young": str(sum(x["pairs"] for k, x in fl["by_age"].items() if k in ("1", "2"))),
              "rv_rev_max": pct(max(x["max_abs_change"] for x in sr["defillama"]["holders revenue"]["by_age"].values()), 1),
              "rv_nd_factor": f"×{nd['largest'][0]['factor']:.0f}" if nd.get("largest") else "none",
              "rv_rb_pairs": f"{rb['pairs']:,}", "rv_rb_snaps": str(len(rb["snapshots"])),
              "rv_rb_moved": str(sum(x["moved_1pct"] for x in rb["by_age"].values()))})
    f["rev_nov01_11"] = f"${float(rv.loc['2026-11-01':'2026-11-11'].sum()) / 1e6:.2f}M"
    pr = bq["pool_revenue"]
    f.update({"pool_share_jun": pct(pr["monthly_share"]["2026-06"]), "pool_share_aug": pct(pr["monthly_share"]["2026-08"]),
              "pool_share_oct": pct(pr["monthly_share"]["2026-10"]), "pool_share_late": pct(pr["share_since_sep28"]),
              "pool_bps": f"{pr['pool_bps_on_confidential']:.1f}", "pool_rest_bps": f"{pr['rest_bps_on_public']:.1f}"})
    si = bq["intents_signers"]
    f.update({"bq_is_tx": f"{si['txns_change'] * 100:+.0f}%", "bq_is_rev": f"{si['revenue_change'] * 100:+.0f}%",
              "bq_is_self_inc": pct(si["self_signed_share_of_increase"], 1), "bq_is_self_nov": pct(si["self_signed_share_nov"]),
              "bq_is_others": f"{si['by_others_change'] * 100:+.0f}%", "bq_is_other_signers": f"{si['other_signers_change'] * 100:+.0f}%"})
    anchors = [json.loads(x) for x in (ROOT / "anchor" / "anchors.jsonl").read_text().splitlines() if x.strip()]
    last = {a["kind"]: a for a in anchors}
    link = lambda a: f"[{a['tx'][:8]}…](https://testnet.nearblocks.io/txns/{a['tx']})"  # noqa: E731
    # releases only: the daily bot appends a "daily" row every day, and the documents must not change with it
    first_daily = next(a for a in anchors if a["kind"] == "daily")
    f.update({"anchor_pred_tx": link(last["predictions"]), "anchor_snap_tx": link(last["snapshot"]), "anchor_daily_tx": link(first_daily),
              "anchor_pred_date": last["predictions"]["date"]})
    from .predictions import resolve
    for _, r in resolve(pd.Timestamp(v["data_to"])).iterrows():
        f[f"{r.id.lower()}_so_far"] = r.so_far or r.status
    return f


def claims(v: dict | None = None) -> list[dict]:
    """Headline findings as checks: the statement, the number, how it is checked, PASS/FAIL."""
    v = v or values()
    f = figures()
    rows = [
        ("F1", "Reported revenue reaches NEAR's wallets", f"{f['rev_rebuilt']} rebuilt vs {f['rev_llama']} on DefiLlama (ratio {f['rev_ratio']})",
         "NEAR inflows to the 3 revenue wallets (NearBlocks) at daily prices vs DefiLlama holders revenue, since the fee switch; holds if within ±2%",
         abs(v["rev_ratio"] - 1) <= 0.02, "make revenue"),
        ("F2", "NEAR's own dashboard agrees on the wallets", f"{f['wallets_rebuilt']} vs {f['wallets_official']} NEAR ({f['wallets_gap']} apart)",
         "all-time NEAR received by the same 3 wallets vs revenue.near.org's wallet table; holds if within ±1%",
         v["wallets_gap"] <= 0.01, "make official"),
        ("F3", "Buybacks offset well under a fifth of issuance", f"{f['offset_rebuilt']} (NEAR's dashboard: {f['offset_official']})",
         "NEAR captured / net issuance from archival-RPC total supply, Feb–Oct 2026; holds if both definitions are below 20%",
         v["offset_rebuilt"] < 0.2 and v["offset_official"] < 0.2, "make supply official"),
        ("F4", "Market cap is far above break-even", f"{f['near_captured_mult']} annual captured revenue vs {f['breakeven_now']} ({f['breakeven_cut']} after HSP-029)",
         "identity: supply stops growing iff market cap / annual captured revenue < 1 / issuance; holds if above the post-cut threshold",
         v["near_captured_mult"] > v["breakeven_cut"], "make montecarlo"),
        ("F5", "NEAR's take doubled from August to October", f"{f['take_aug']} → {f['take_oct']} bps of volume (1.8x to 2.5x depending on the window: make robustness)",
         "wallet revenue / NEAR-reported Intents volume, by month; holds if October ≥ 2× August",
         v["take_oct"] >= 2 * v["take_aug"], "make official"),
        ("F6", "Confidential swaps pay NEAR more than public ones, in every method", f"{f['premium_range']} bps vs {f['public_range']} (Dune fee table {f['dune_fee_bps']})",
         "weekly fit in levels and in first differences, Aug–Oct; holds if the confidential coefficient exceeds the public one in both",
         v["fit_conf"] > v["fit_pub"] and v["fd_conf"] > v["fd_pub"], "make confidential"),
        ("F7", "They explain part, not all, of the jump", f"{f['jump_fd']} to {f['jump_levels']} of the +{f['jump_rise']} bps",
         "(change in confidential share) × (confidential premium) / rise in take, under three premiums; holds if the range spans below 100%",
         v["jump_fd"] < 1, "make confidential"),
        ("F8", "Drop 1 of NEAR@3.33 cost less than the revenue uplift", f"{f['drop1_usd']} vs {f['uplift']} ({f['drop1_over_uplift']})",
         "333,333 NEAR at the conversion price vs Sep–Oct revenue above the May–Aug take rate; holds if cost < uplift",
         v["drop1_over_uplift"] < 1, "make confidential"),
        ("F9", "The fit missed its first unseen week", f"{f['oos_actual']} actual vs {f['oos_pred_fd']}–{f['oos_pred']} predicted",
         "week of 2026-11-02, never used in the fit; holds (as a reported failure) if actual < both predictions",
         v["oos_actual"] < min(v["oos_pred"], v["oos_pred_fd"]), "make confidential"),
        ("F10", "Confidential TVL did not leave after the snapshot (H4.1 rejected)", f"{f['tvl_snap']} → {f['tvl_snap_30d']} 30 days later; {f['tvl_last']} on {f['tvl_last_date']}",
         "Dune confidential TVL around the NEAR@3.33 snapshot, then NEAR's dashboard; holds if TVL 30 days later > at the snapshot",
         v["tvl_snap_30d"] > v["tvl_snap"], "make confidential official"),
        ("F11", "Supply still grows through 2027 in the base case", f"median {f['mc_base']} of 2027 issuance offset ({f['mc_base_p']} chance of a deflationary 2027)",
         "Monte Carlo, 10,000 paths, joint block bootstrap of volume and price; holds if the median is below 100% with and without HSP-029",
         v["mc_base_med"] < 1 and v["mc_cut_med"] < 1, "make montecarlo"),
        ("F12", "Peers are priced on their revenue, NEAR is not", f"{f['near_holders_mult']} vs peer median {f['peers_median']} ({f['peers_n']} peers)",
         "market cap / annualised holders revenue (DefiLlama, CoinGecko); holds if NEAR is above every peer's interquartile range",
         v["near_holders_mult"] > v["peers_q3"], "make comps"),
        ("F13", "Usage does not lead NEAR's price (the track's hypothesis)", f"{f['ll_sig']} of {f['ll_tests']} lead-lag tests significant after Holm; best {f['ll_best']}",
         "weekly changes, NEAR price net of BTC, lags 1–4 weeks, Intents volume and L1 activity, both directions; holds if none is significant at 5% after Holm",
         v["ll_sig"] == 0, "make leadlag"),
        ("F14", "NEAR's BigQuery dataset agrees with the pipeline's sources", f"revenue wallets {f['bq_rev_near']} NEAR on both, max monthly gap {f['bq_rev_gap']}; net issuance Feb–Oct {f['bq_issued']} ({f['bq_supply_gap']} apart)",
         "queries in sql/ run on NEAR's public BigQuery dataset vs NearBlocks wallet histories and archival-RPC supply; holds if every month is within 0.1% and issuance within 0.5%",
         _json("bigquery_crosscheck.json")["revenue"]["max_monthly_gap"] < 1e-3 and abs(_json("bigquery_crosscheck.json")["supply"]["issued_gap"]) < 5e-3, "make bigquery"),
        ("F15", "The 1Click results recompute without the partner key", f"{_leaves(_json('oneclick_offline_check.json')['published'])} figures (integrator shares, the November take, the fee-schedule test) recomputed from the published daily aggregates, all within 1.5%",
         "data/processed/oneclick_daily.csv (daily sums by integrator, route type, NEAR fee tier, ZEC; no swap or address) recomputed and compared with the outputs of make swaps; holds if all agree within 1.5%",
         _json("oneclick_offline_check.json")["agree"], "make oneclick-offline"),
        ("F16", "The rebuilt revenue never revises; the aggregators' latest days do",
         f"{f['rv_rb_moved']} of {f['rv_rb_pairs']} daily readings of the rebuilt revenue changed across {f['rv_rb_snaps']} dated snapshots; DefiLlama's gross fees for the latest day were revised up to {f['rv_fee_factor']} ({f['rv_fee_day']}: {f['rv_fee_first']} → {f['rv_fee_latest']}), settled after {f['rv_fee_settle']} days",
         "every dated snapshot in data/raw compared day by day with the latest (same rebuild code on each wallet snapshot); holds if no complete day of the rebuilt revenue moved by 1% or more (figures that use DefiLlama's gross fees stop at its settled days)",
         _json("source_revisions.json")["rebuilt_from_wallets"]["pairs"] > 0 and sum(x["moved_1pct"] for x in _json("source_revisions.json")["rebuilt_from_wallets"]["by_age"].values()) == 0,
         "make revisions"),
        ("F17", "The exploit cost NEAR little revenue, but large integrators pulled back",
         f"1Click stopped for {f['ic_hours']} hours on 1 Oct ({f['ic_from']} to {f['ic_to']} UTC), about {f['ic_rev_lost']} of NEAR revenue; in the two weeks after, NEAR's 1Click revenue changed {f['ic_rev']} (inside the range of {f['ic_pn']} placebo dates) while the 25 largest integrators' volume changed {f['ic_top_vol']}, below every placebo date ({f['ic_top_vol_pmin']} at worst); {f['ic_back']} of the {f['ic_cut']} that cut back returned by November",
         "1Click swap aggregates: the longest gap with no swap on 1 Oct; the median day of 3-16 Oct against 15-28 Sep, ranked against the same split at every date whose windows avoid 27 Sep-4 Oct; holds if the halt lasted under 12 hours, NEAR's 1Click revenue change lies within the placebo range and the top-25 integrators' volume change lies below it",
         _json("incident.json")["halt"]["hours"] < 12
         and _json("incident.json")["placebo_distribution"]["near_usd_change"]["placebo_min"] <= _json("incident.json")["placebo_distribution"]["near_usd_change"]["event"] <= _json("incident.json")["placebo_distribution"]["near_usd_change"]["placebo_max"]
         and _json("incident.json")["placebo_distribution"]["top_volume_change"]["event"] < _json("incident.json")["placebo_distribution"]["top_volume_change"]["placebo_min"],
         "make incident"),
        ("F18", "Users pay about 60 bps a swap on 1Click; NEAR keeps about a sixteenth of it",
         f"{f['sc_cost']} bps of what users send is gone on delivery ({f['sc_from']} to {f['sc_to']}, {f['sc_swaps']} swaps): integrators {f['sc_int']}, NEAR {f['sc_near']}, solvers and networks {f['sc_rest']} ({f['sc_near_share']} to NEAR)",
         "dollar value sent and delivered per 1Click swap (Explorer API), split by the fees in each record, daily sums committed; holds if NEAR's share of the user's cost is under 10% and integrators' over half",
         _json("swap_cost.json")["last30"]["near_share_of_cost"] < 0.10 and _json("swap_cost.json")["last30"]["integrators_bps"] > 0.5 * _json("swap_cost.json")["last30"]["cost_bps"],
         "make swap-cost"),
    ]
    return [{"id": i, "finding": a, "number": n, "check": c, "passed": bool(p), "command": cmd} for i, a, n, c, p, cmd in rows]


def _claims_data() -> dict:
    """Series the public-claims ledger tests against: DefiLlama, the rebuilt revenue, NearBlocks, Dune, supply."""
    from .analysis.leadlag import _chain
    from .analysis.ledger import llama_daily, near_price
    d = {"vol": llama_daily("llama_volume", "v"), "fees": llama_daily("llama_dailyFees", "f"),
         "hr": llama_daily("llama_dailyHoldersRevenue", "h"), "px": near_price(), "chain": _chain()}
    d["rev"] = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"].loc[FEE_SWITCH:]
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    days = pd.date_range(sm.index.min(), sm.index.max() + pd.offsets.MonthEnd(0))
    d["issued"] = pd.Series([sm.loc[pd.Timestamp(x.year, x.month, 1), "net_issuance_near"] / x.days_in_month for x in days], index=days)
    d["ctvl"] = pd.read_csv(OUT / "confidential_tvl.csv", index_col=0, parse_dates=True).iloc[:, 0]
    d["share"] = pd.read_csv(OUT / "crosschain_share.csv", index_col=0, parse_dates=True)["near-intents_share"]
    return d


def control_table(ct: dict) -> str:
    """Every payment the two revenue DAOs executed, with its proposal, approvals and transaction (REPORT appendix)."""
    lines = ["| Fund | Proposal | Executed | Paid | To | Approvals | Proposal text (start) | Transaction |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for d in ct["daos"].values():
        for p in d["payments"]:
            amt = f"{p['amount']:,.0f} {p['token']}"
            text = re.sub(r"<br>|\*|\|", " ", p["description"]).split("Summary")[0].replace("Title:", "").replace("Notes:", "").strip() or "(none)"
            tx = f"[{p['tx'][:8]}…](https://nearblocks.io/txns/{p['tx']})" if p["tx"] else "not found"
            lines.append(f"| {d['label']} | {p['proposal']} | {p['day'] or p['proposed']} | {amt} | `{p['to']}` | {p['approvals']} | {text} | {tx} |")
    return "\n".join(lines)


def follow_100(v: dict) -> dict:
    """Where $100 of NEAR Intents volume goes, over the same 30 days as the headline multiple."""
    d = _claims_data()
    a, b = v["r30_from"], v["r30_to"]
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True).loc[a:b]
    vol = float(d["vol"].loc[a:b].sum())
    # gross fees: DefiLlama revises its latest days (make revisions), so the fee rate is taken over the settled days only
    rv = _json("source_revisions.json")["defillama"]["gross fees"]
    settled = str((pd.Timestamp(rv["snapshots"][-1]) - pd.Timedelta(days=rv["settled_after_days"])).date())
    fb = min(b, settled)
    fees = float(d["fees"].loc[a:fb].sum()) / float(d["vol"].loc[a:fb].sum()) * vol
    captured = float(rev["rebuilt_total_usd"].sum())
    bb = float(rev["rebuilt_buybacks_usd"].sum())
    days = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
    lf = json.loads((ROOT / "dashboard" / "data.json").read_text())["live_fallback"]  # same inputs as the dashboard's card
    issued_usd = lf["supply"] * v["issuance"] / 365 * days * lf["price"]  # new NEAR over the window, at the latest close
    oc = pd.read_csv(OUT / "oneclick_daily.csv")
    oc = oc[(oc["day"] >= a) & (oc["day"] <= b)]
    per = lambda x: f"${100 * x / vol:.3f}"  # noqa: E731
    return {"f100_from": a, "f100_to": b, "f100_fees_to": fb, "f100_fees": per(fees), "f100_near": per(captured), "f100_bb": per(bb),
            "f100_fe": per(captured - bb), "f100_issued": per(issued_usd), "f100_cover": pct(captured / issued_usd),
            "f100_vol": usd(vol, 2), "oc_share_vol": pct(oc["volume_usd"].sum() / vol), "f100_oc_pool": f"${100 * oc['fee_usd'].sum() / oc['volume_usd'].sum():.3f}",
            "f100_oc_near": f"${100 * oc['near_usd'].sum() / oc['volume_usd'].sum():.3f}",
            "f100_oc_int": f"${100 * (oc['fee_usd'].sum() - oc['near_usd'].sum()) / oc['volume_usd'].sum():.3f}",
            # static values printed in dashboard/index.html, shown when JavaScript does not run (same inputs as its live card)
            "s_per100": str(round(100 * captured / issued_usd)), "s_rev30": usd(captured, 2), "s_take": f"{captured / vol * 1e4:.1f} bps",
            "s_bought30": f"{captured / lf['price'] / 1e3:,.0f}k NEAR at ${lf['price']:.2f}", "s_vol30": usd(vol, 2),
"s_be": f"{1 / v['issuance']:.0f}×",
            "s_issued30": f"{lf['supply'] * v['issuance'] / 365 * days / 1e6:.1f}M NEAR", "s_iss_rate": f"{v['issuance'] * 100:.2f}% a year, on-chain"}


def public_claims(v: dict | None = None) -> list[dict]:
    """Claims made in public about NEAR's revenue, buybacks, issuance and usage, checked against this audit's data.

    Each row quotes or paraphrases a dated public source and tests it on the committed snapshots, at the
    claim's own date where it has one. Verdicts: Survives, Close (within about 10%, or within definitions),
    Overstated, Inflated (off by a multiple), Not shown (the data does not support it), Unverified.
    """
    v = v or values()
    f = figures()
    d = _claims_data()
    vol, fees, hr, px, rev, ch = d["vol"], d["fees"], d["hr"], d["px"], d["rev"], d["chain"]
    supply = json.loads(sorted((RAW / "chain_state").glob("*.json"))[-1].read_text())["total_supply_near"]
    # linear ramp of the cap from 2.5% to 1.6% over 2 years: the cut grows from 0 to 0.9 pp, so the
    # NEAR not issued over the 2 years is supply x 0.9% x (average cut over 2 years = half) x 2 years
    avoided_2y = supply * (0.025 - 0.016) * 0.5 * 2
    cum = lambda s, to: s.loc[:to].sum()  # noqa: E731
    win = lambda s, a, b: s.loc[a:b].sum()  # noqa: E731
    a30, b30 = "2026-09-07", "2026-10-06"  # the 30 days before 6 October (Bankless podcast, Nansen's capture figures)
    iss30 = d["issued"].loc[a30:b30]
    iss30_usd = float((iss30 * px.reindex(iss30.index)).sum())
    bb30 = win(rev, a30, b30)
    q3 = ch.loc["2026-07-01":"2026-09-30"]
    peak = q3["txns"].idxmax()
    crossed8 = rev.cumsum()
    crossed8 = crossed8[crossed8 >= 8e6].index.min()
    month_iss_16 = supply * 0.016 / 12 * float(px.dropna().iloc[-1])
    last30_rev = float(rev.iloc[-30:].sum())
    ct = d["ctvl"]
    ct_sep, ct_jun = float(ct.asof(pd.Timestamp("2026-09-30"))), float(ct.asof(pd.Timestamp("2026-06-30")))
    share = d["share"]
    may_oct = share.loc["2026-05-01":"2026-10-01"]
    take_jun = win(rev, "2026-05-04", "2026-06-03") / win(vol, "2026-05-04", "2026-06-03") * 1e4
    ws = json.loads(sorted((RAW / "wallet_state").glob("*.json"))[-1].read_text())
    ws_liquid, ws_staked = sum(x["liquid_near"] for x in ws.values()), sum(x["staked_near"] for x in ws.values())
    flows = pd.read_csv(OUT / "revenue_wallet_flows.csv", parse_dates=["date"])
    pre = flows[(flows["dir"] == "in") & flows["is_near"] & ~flows["internal"] & (flows["date"] < "2026-02-24")]
    fp = _json("oneclick_fee_policy.json")
    bbw = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_buybacks_usd"]
    rows = [
        # --- what NEAR said it would do
        ("\"NEAR Intents has already directed revenue to over 1M in $NEAR buyback\"", "[Evolving NEAR Tokenomics, near.org, 2026-02-24](https://www.near.org/blog/evolving-near-tokenomics)",
         f"{pre['amount'].sum() / 1e6:.2f}M NEAR ({usd(pre['usd'].sum())}) had reached the revenue wallets before 24 February", "Survives"),
        ("Acquired NEAR is \"staked, locked, or otherwise removed from liquid circulation\"", "same",
         f"the three revenue wallets hold {ws_liquid / 1e6:.2f}M NEAR, {ws_staked:,.0f} of it staked or locked (NEAR RPC `view_account`, {sorted((RAW / 'wallet_state').glob('*.json'))[-1].stem}); none is burned", "Not shown"),
        ("1Click with an API key and no app fee: 20 bps, 1 bp on stablecoin and same-asset routes", "[NEAR Intents docs, fees](https://docs.near-intents.org/resources/fees)",
         f"swaps without an integrator, last 30 days: {pct(fp['no_ref_cross']['share_at_20_or_more'])} of cross-asset volume pays NEAR's wallets 20 bps or more, {pct(fp['no_ref_same']['share_at_1'])} of same-asset volume pays 1 bp", "Survives for most volume"),
        ("1Click with app fees: a 50/50 split, at least 20 bps to 1Click (custom deals exist)", "same",
         f"swaps with an integrator, last 30 days: {pct(fp['ref_cross']['share_at_20_or_more'])} of cross-asset volume pays NEAR 20 bps or more, {pct(fp['ref_cross']['share_at_0'])} pays it nothing; average {fp['ref_cross']['near_bps']:.1f} bps", "The exception is the rule"),
        # --- revenue and buybacks
        ("\"About $177M of daily volume makes NEAR deflationary\"", "community DefiLlama Pro dashboard, widely quoted in 2026 (log 6)",
         f"assumes all gross fees buy NEAR; with the captured share, break-even is {f['be_vol_now']}/day at {f['take_now']} bps", "Inflated"),
        ("\"NEAR captures a growing share of fees\"", "revenue.near.org, read 2026-11-11",
         f"{f['cap_total_all']} of gross fees all-time, {f['cap_total_d30']} over the last 30 days (read high: the page's latest days of fees are still being revised, F16); take {f['take_aug']} → {f['take_oct']} bps Aug to Oct, {f['take_last_week']} in the week of 2 Nov",
         "Survives, but turned down in November"),
        ("\"...feeding buybacks that permanently remove NEAR from circulation\"", "revenue.near.org, read 2026-11-11",
         f"{f['fefunds_share']} of the NEAR captured sits in a DAO treasury with no on-chain commitment not to sell; nothing is burned; supply grows {f['net_growth']} a year net",
         "Not shown"),
        ("Revenue as NEAR reports it", "revenue.near.org monthly revenue series",
         f"{f['series_over_wallets']} above the NEAR its own three revenue wallets receive (Mar–Oct), while the wallet totals agree within {f['wallets_gap']}",
         "Unverified (gap unexplained)"),
        ("Share of emissions offset, as NEAR reports it", "revenue.near.org, read 2026-11-11",
         f"{f['offset_official']} on NEAR's count, {f['offset_rebuilt']} rebuilt from the wallets and archival supply, Feb–Oct", "Survives (definitions differ)"),
        ("\"Buybacks are still real\": about $1.9M of Intents-funded purchases over 30 days", "Sal Ternullo (SVRN) on Bankless, via [Stocktwits, 2026-10-06](https://stocktwits.com/news-articles/markets/cryptocurrency/near-treasury-firm-ceo-says-buybacks-are-still-real-but-issuance-runs-six-times-higher/cZDteDIRBl3)",
         f"{usd(bb30)} reached the three revenue wallets over the 30 days to 6 Oct", "Survives"),
        ("Issuance runs about $13M over the same 30 days, \"more than six times\" buybacks", "same",
         f"{iss30.sum() / 1e6:.2f}M NEAR issued, {usd(iss30_usd)} at daily prices: {iss30_usd / bb30:.1f}× the revenue captured", "Overstated (direction right)"),
        ("Bought NEAR is not burned; it sits in a \"permanent capital vehicle\"", "same",
         f"nothing is burned; {f['fefunds_share']} of captured NEAR is in the front-end fund's DAO treasury, the rest in the buyback wallet; no lock on either", "Survives"),
        ("At 1.6% issuance NEAR still issues about $8M a month; buybacks cover under a quarter", "same",
         f"{usd(month_iss_16)} a month at today's price on today's supply; the last 30 days of captured revenue ({usd(last30_rev)}) would cover {last30_rev / month_iss_16:.0%}", "Close (price-dependent)"),
        ("Staking yield falls from about 5.4% to about 3.5% under HSP-029", "same",
         f"staker reward {pct(v['staker_reward'], 1)} today; scaled by 1.6/2.5, {pct(v['staker_reward'] * 1.6 / 2.5, 1)}", "Survives"),
        ("\"HSP-029 avoids 11.8M NEAR of issuance over two years\"", "HSP-029 text on vote.dao; Unchained, 2026-11-03",
         f"a linear ramp from 2.5% to 1.6% on today's supply avoids {avoided_2y / 1e6:.1f}M NEAR over two years; it cannot start before {f['hsp_earliest']}",
         "Survives"),
        ("HSP-029 passed the House of Stake vote (closed 2026-11-02)", "vote.dao proposal 29; The Defiant",
         f"{f['hsp_for']} of veNEAR cast in favour; in timelock until {f['hsp_timelock_end']}", "Survives"),
        ("Cumulative fees above $52M; more than $8M captured for buybacks", "Nansen NEAR Q3 2026, via [Altcoin Buzz, 2026-10-28](https://www.altcoinbuzz.io/near-intents-fees-buybacks-52-million)",
         f"fees {usd(cum(fees, '2026-10-28'))} to 28 Oct (DefiLlama); captured {usd(cum(rev, '2026-10-28'))} by then on the wallets, "
         + (f"crossing $8M on {crossed8:%Y-%m-%d}" if pd.notna(crossed8) else f"{usd(rev.sum())} by {rev.index.max():%d %b}, still under $8M; NEAR's own revenue series, {f['series_over_wallets']} higher, would pass it"),
         "Fees survive; $8M not on the wallets"),
        ("$6.68M of NEAR bought back as of 19 October", "DefiLlama holders revenue, via Altcoin Buzz (2026-10-28)",
         f"{usd(cum(hr, '2026-10-19'))} on DefiLlama, {usd(cum(rev, '2026-10-19'))} rebuilt from the wallets", "Survives"),
        ("Lifetime fee capture about 16.4% (as of 6 October)", "Nansen NEAR Q3 2026, via Altcoin Buzz",
         f"{pct(cum(rev, '2026-10-06') / win(fees, FEE_SWITCH, '2026-10-06'), 1)} of fees since the fee switch, {pct(cum(rev, '2026-10-06') / cum(fees, '2026-10-06'), 1)} of all fees since launch", "Close (definitions)"),
        ("Fee capture about 28.4% over the last 30 days (6 October)", "same",
         f"{pct(bb30 / win(fees, a30, b30), 1)} rebuilt, {pct(win(hr, a30, b30) / win(fees, a30, b30), 1)} on DefiLlama", "Close, a little high"),
        # --- the latest press, 12 November (figures to 11 November, the day before publication)
        ("About $2.7M of NEAR bought back from Intents revenue so far in Q4", "[AMBCrypto, 2026-11-12](https://ambcrypto.com/near-intents-fuels-2-7m-in-q4-buybacks-as-revenue-surges/), from BSC News",
         f"{usd(win(rev, '2026-10-01', '2026-11-11'))} reached the three revenue wallets from 1 October to 11 November, but only {usd(win(bbw, '2026-10-01', '2026-11-11'))} the buyback multisig itself (the rest sits in the front-end fund)", "Survives, on all three wallets"),
        ("$8.68M of fees since 1 October, of which NEAR Intents kept $2.82M", "same",
         f"{usd(win(fees, '2026-10-01', '2026-11-11'))} of gross fees on DefiLlama to 11 November; {usd(win(rev, '2026-10-01', '2026-11-11'))} reached NEAR's wallets", "Survives"),
        ("$3.07M of buybacks in Q3, per DefiLlama", "same",
         f"DefiLlama's holders revenue is {usd(win(hr, '2026-07-01', '2026-09-30'))}; the wallets received {usd(win(rev, '2026-07-01', '2026-09-30'))}, of which {usd(win(bbw, '2026-07-01', '2026-09-30'))} into the buyback multisig", "Close (DefiLlama's definition)"),
        # --- volume, usage, TVL
        ("Q3 2026 Intents volume about $10.4B", "Nansen NEAR Q3 2026, via [Altcoin Buzz, 2026-11-02](https://www.altcoinbuzz.io/near-protocol-q3-2026-on-chain-activity-intents)",
         f"{usd(win(vol, '2026-07-01', '2026-09-30'))} on DefiLlama", "Close"),
        ("Q3: about 68M transactions, 739k a day, 79.3k daily active accounts, a peak of 1.21M on 27 September", "same",
         f"NearBlocks: {q3['txns'].sum() / 1e6:.1f}M, {q3['txns'].mean() / 1e3:.0f}k a day, {q3['active_accounts'].mean() / 1e3:.1f}k active, peak {q3['txns'].max() / 1e6:.2f}M on {peak:%d %b}", "Survives"),
        ("Confidential Intents TVL about $160M at end-September, up 463% on the quarter", "same",
         f"Dune: {usd(ct_sep, 1)} on 30 Sep, {usd(ct_jun, 1)} on 30 Jun (+{ct_sep / ct_jun - 1:.0%})", "Survives"),
        ("Intents volume above $32B", "Ternullo on Bankless, 2026-10-06",
         f"{usd(cum(vol, '2026-10-06'))} cumulative on DefiLlama to 6 Oct", "Survives"),
        ("Over $20B of cumulative volume (3 June); about $32M of fees, a 0.16% take", "[Crypto Briefing via KuCoin, 2026-06-03](https://www.kucoin.com/news/flash/near-intents-surpasses-20b-in-all-time-transaction-volume)",
         f"{usd(cum(vol, '2026-06-03'))} and {usd(cum(fees, '2026-06-03'))} of gross fees on DefiLlama; NEAR itself kept {take_jun:.1f} bps of volume in the month to 3 June", "Survives (gross fees, not NEAR's take)"),
        ("Over $18B of cumulative volume, about $5B of it since the end of February", "[Bankless, 2026-05-15](https://www.bankless.com/read/nears-intents-and-ai-bets-fuel-revival), citing Dune",
         f"{usd(cum(vol, '2026-05-15'))} to 15 May, {usd(win(vol, '2026-03-01', '2026-05-15'))} since 1 March (DefiLlama)", "Survives"),
        ("NEAR Intents is the largest cross-chain swap venue", "near.org and Intents team framing",
         f"{pct(may_oct.min())}–{pct(may_oct.max())} of cross-chain swap volume each month May–Oct (DefiLlama); {pct(share.iloc[-1])} in November to date, behind THORChain", "Survives to October; not in November"),
        ("Staking ratio holds at about 46%", "Bitwise Q3 2026 staking report, via Crypto Briefing",
         f"{pct(v['staked'], 1)} of total supply staked (validators, NEAR RPC)", "Close"),
        # --- value accrual
        ("Intents volume spikes coincide with NEAR rallies; the Intents flywheel reprices NEAR", "Crypto Briefing (2026-06-03); Bankless, \"NEAR's Intents and AI bets fuel revival\"",
         f"{f['ll_sig']} of {f['ll_tests']} weekly lead-lag tests significant after Holm, NEAR net of BTC (REPORT section 8)", "Not shown"),
        ("Usage on NEAR is growing", "recurring ecosystem framing",
         f"Intents volume {f['yoy_vol']} year on year over the last 30 days; L1 transactions {f['yoy_txns']}", "Intents yes, L1 no"),
    ]
    out, prev = [], ""
    for c, s_, dt, vd in rows:
        if s_ == "same":  # repeat the previous source, without its link, so each row stands alone when sorted
            s_ = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", prev)
        else:
            prev = s_
        out.append({"claim": c, "source": s_, "data": dt, "verdict": vd})
    return out


def public_claims_table(rows: list[dict]) -> str:
    lines = ["| Claim | Source | What the data says | Verdict |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['claim']} | {r['source']} | {r['data']} | **{r['verdict']}** |" for r in rows]
    return "\n".join(lines)


def claims_table(rows: list[dict]) -> str:
    lines = ["| ID | Finding | Number | How it is checked | Result |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['finding']} | {r['number']} | {r['check']} (`{r['command']}`) | {'PASS' if r['passed'] else '**FAIL**'} |")
    return "\n".join(lines)


def render() -> dict[str, str]:
    f = figures()
    f["claims_table"] = claims_table(claims())
    f["claims_passed"] = f"{sum(r['passed'] for r in claims())}/{len(claims())}"
    f["claims_n"] = str(len(claims()))
    pcs = public_claims()
    f["public_claims_table"] = public_claims_table(pcs)
    f["public_claims_n"] = str(len(pcs))
    f["public_claims_survive"] = str(sum(r["verdict"].startswith("Survives") for r in pcs))
    f["public_claims_close"] = str(sum(r["verdict"].startswith("Close") for r in pcs))
    f["public_claims_fail"] = str(len(pcs) - int(f["public_claims_survive"]) - int(f["public_claims_close"]))
    out = {}
    for name in DOCS:
        t = (TEMPLATES / name).read_text()
        missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", t)) - set(f))
        if missing:
            raise KeyError(f"{name}: no value for {missing}")
        out[name] = "<!-- Generated from docs/templates/" + name + " by `make docs`; edit the template, not this file. -->\n" + \
            re.sub(r"\{\{(\w+)\}\}", lambda m: f[m.group(1)], t)
    out[DASHBOARD] = static_dashboard(f)
    return out


DASHBOARD = "dashboard/index.html"
STATIC = re.compile(r'(<[a-z]+\b[^>]*\bdata-s="(\w+)"[^>]*>)([^<]*)(</)')


def static_dashboard(f: dict) -> str:
    """The dashboard's values for readers without JavaScript (and for crawlers): every element marked data-s="key" holds
    the committed snapshot's value of that key; the page's script then replaces them with live values."""
    t = (ROOT / DASHBOARD).read_text()
    missing = sorted({m.group(2) for m in STATIC.finditer(t)} - set(f))
    if missing:
        raise KeyError(f"{DASHBOARD}: no value for {missing}")
    return STATIC.sub(lambda m: m.group(1) + html.escape(f[m.group(2)], quote=False) + m.group(4), t)


def main() -> int:
    check = "--check" in sys.argv
    docs = render()
    rows = claims()
    stale = []
    for name, text in docs.items():
        path = ROOT / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    for r in rows:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']:<4} {r['finding']}: {r['number']}")
    print(f"{sum(r['passed'] for r in rows)}/{len(rows)} findings hold")
    f = figures()  # the README's "headline numbers, exactly", as printed values
    print("Headline numbers:")
    print(f"  {f['offset_rebuilt']} of new NEAR offset by the 3 revenue wallets, {f['offset_window']}")
    print(f"  {f['near_captured_mult']} market cap ({f['mcap_date']}) / wallet revenue {f['r30_from']} to {f['r30_to']}, annualised")
    print(f"  {f['breakeven_now']} break-even multiple (1 / {f['issuance']}); about {f['be_vol_now']} of daily volume at today's take")
    print(f"  {f['oc_integrators_keep']} of the 1Click fee pool kept by integrators, {f['oc_from']} to {f['oc_to']}")
    print(f"Follow $100 of Intents volume, {f['f100_from']} to {f['f100_to']}: fees {f['f100_fees']}, to NEAR's wallets {f['f100_near']} "
          f"(buyback multisig {f['f100_bb']}), new NEAR issued {f['f100_issued']}: revenue covers {f['f100_cover']} of issuance")
    if check and stale:
        print(f"STALE: {', '.join(stale)} differ from the templates rendered on the committed data; run `make docs`")
    return 1 if (stale or not all(r["passed"] for r in rows)) else 0


if __name__ == "__main__":
    sys.exit(main())
