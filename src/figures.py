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
    r30 = rev["rebuilt_total_usd"].loc[:complete.max()].iloc[-30:].sum() * 365 / 30
    v["near_captured_mult"] = v["near_mcap"] / r30
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
        "near_mcap": usd(v["near_mcap"], 1), "near_value_at_peer": usd(v["near_value_at_peer"], 0), "share_not_revenue": pct(v["share_not_revenue"]),
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
        "oc_from": oc["last30"]["from"], "oc_to": oc["last30"]["to"], "oc_swaps": f"{oc['last30']['swaps'] / 1e6:.1f}M",
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
        ("F5", "NEAR's take more than doubled Aug to Oct", f"{f['take_aug']} → {f['take_oct']} bps of volume",
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
    ]
    return [{"id": i, "finding": a, "number": n, "check": c, "passed": bool(p), "command": cmd} for i, a, n, c, p, cmd in rows]


def public_claims(v: dict | None = None) -> list[dict]:
    """Claims made in public about NEAR's buybacks and issuance, checked against this audit's data."""
    v = v or values()
    f = figures()
    supply = json.loads(sorted((RAW / "chain_state").glob("*.json"))[-1].read_text())["total_supply_near"]
    # linear ramp of the cap from 2.5% to 1.6% over 2 years: the cut grows from 0 to 0.9 pp, so the
    # NEAR not issued over the 2 years is supply x 0.9% x (average cut over 2 years = half) x 2 years
    avoided_2y = supply * (0.025 - 0.016) * 0.5 * 2
    return [
        {"claim": "\"About $177M of daily volume makes NEAR deflationary\"", "source": "community DefiLlama Pro dashboard, widely quoted in 2026 (log 6)",
         "data": f"assumes all gross fees buy NEAR; with the captured share, break-even is {f['be_vol_now']}/day at {f['take_now']} bps", "verdict": "Inflated"},
        {"claim": "\"NEAR captures a growing share of fees\"", "source": "revenue.near.org, read 2026-11-11",
         "data": f"{f['cap_total_all']} of gross fees all-time, {f['cap_total_d30']} over the last 30 days; take {f['take_aug']} → {f['take_oct']} bps Aug to Oct, {f['take_last_week']} in the week of 2 Nov",
         "verdict": "Survives, but turned down in November"},
        {"claim": "\"...feeding buybacks that permanently remove NEAR from circulation\"", "source": "revenue.near.org, read 2026-11-11",
         "data": f"{f['fefunds_share']} of the NEAR captured sits in a DAO treasury with no on-chain commitment not to sell; nothing is burned; supply grows {f['net_growth']} a year net",
         "verdict": "Not shown"},
        {"claim": "Revenue as NEAR reports it", "source": "revenue.near.org monthly revenue series",
         "data": f"{f['series_over_wallets']} above the NEAR its own three revenue wallets receive (Mar–Oct), while the wallet totals agree within {f['wallets_gap']}",
         "verdict": "Unverified (gap unexplained)"},
        {"claim": "\"HSP-029 avoids 11.8M NEAR of issuance over two years\"", "source": "HSP-029 text on vote.dao; Unchained, 2026-11-03",
         "data": f"a linear ramp from 2.5% to 1.6% on today's supply avoids {avoided_2y / 1e6:.1f}M NEAR over two years; it cannot start before {f['hsp_earliest']}",
         "verdict": "Survives"},
    ]


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
    f["public_claims_table"] = public_claims_table(public_claims())
    out = {}
    for name in DOCS:
        t = (TEMPLATES / name).read_text()
        missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", t)) - set(f))
        if missing:
            raise KeyError(f"{name}: no value for {missing}")
        out[name] = "<!-- Generated from docs/templates/" + name + " by `make docs`; edit the template, not this file. -->\n" + \
            re.sub(r"\{\{(\w+)\}\}", lambda m: f[m.group(1)], t)
    return out


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
    if check and stale:
        print(f"STALE: {', '.join(stale)} differ from the templates rendered on the committed data; run `make docs`")
    return 1 if (stale or not all(r["passed"] for r in rows)) else 0


if __name__ == "__main__":
    sys.exit(main())
