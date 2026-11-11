"""Cross-check against NEAR's own revenue dashboard (revenue.near.org, public since November 2026).

The page embeds its data series in the HTML (Next.js payload). `fetch()` saves them to
data/raw/near_revenue/<date>.json; the analysis runs offline on the latest snapshot.

1. Wallets: all-time NEAR received by the three revenue wallets, theirs vs rebuilt here.
2. Offset: revenue as a share of emissions by month, theirs vs captured / net issuance here.
3. Take rate: rebuilt revenue / official volume and / official gross fees, by month and by week.
   (Official daily volume equals Dune's all-time volume query, so it extends that series daily.)
4. Confidential TVL, daily (the series behind H4.1), with its change since the peak.
5. Two definitions of revenue. NEAR's page also carries a monthly revenue series and the share of
   gross fees it captures by mechanism (front-end fees, B2B partners, quote improvement). That
   series runs above the NEAR that reaches the three wallets (and above DefiLlama's holders
   revenue, which tracks the wallets). The take rate is therefore reported on both definitions,
   and conclusions about recent weeks say which one they use.

Outputs: data/processed/official_monthly.csv, official_weekly.csv, official_tvl.csv,
official_crosscheck.json.
"""
from __future__ import annotations

import json
import re

import pandas as pd
import requests

from ..ingest.sources import RAW, _today
from .ledger import OUT

URL = "https://revenue.near.org/"
KEYS = ("totalFeesSeries", "intentVolumeSeries", "tvlChartSeries", "absoluteRevEmissions", "emissionsMonthly", "rows")
OPTIONAL_KEYS = ("revenueSeries",)  # monthly revenue as NEAR reports it (added to the snapshot on 2026-11-11)
MECHANISMS = {"fe": "front_end_fees", "b2b": "b2b_partners", "qi": "quote_improvement"}
FEE_SWITCH = "2026-02-23"


def fetch() -> dict:
    html = requests.get(URL, timeout=60, headers={"User-Agent": "near-revenue-audit (research)"}).text
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, flags=re.S)
    text = "".join(json.loads('"' + c + '"') for c in chunks)
    dec, out = json.JSONDecoder(), {}
    for key in KEYS + OPTIONAL_KEYS:
        best = []
        for m in re.finditer(f'"{key}":' + r"\[\{", text):
            try:
                v, _ = dec.raw_decode(text[m.end() - 2:])
            except ValueError:
                continue
            if len(v) > len(best):
                best = v
        if not best and key in KEYS:
            raise RuntimeError(f"revenue.near.org: series {key} not found (page layout changed?)")
        if best:
            out[key] = best
    # Share of gross fees captured, by mechanism and window: one flat object on the page
    m = re.search(r'\{"pp_fe_all_time":[^{}]*\}', text)
    if m:
        out["captureByMechanism"] = json.loads(m.group(0))
    folder = RAW / "near_revenue"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_today()}.json").write_text(json.dumps(out))
    return out


def latest() -> tuple[dict, str]:
    path = sorted((RAW / "near_revenue").glob("*.json"))[-1]
    return json.loads(path.read_text()), path.stem


def _series(rows: list, col: str, date: str = "date") -> pd.Series:
    df = pd.DataFrame(rows)
    return pd.Series(df[col].to_numpy(), index=pd.to_datetime(df[date]), name=col)


def crosscheck() -> dict:
    snap, snap_date = latest()
    volume = _series(snap["intentVolumeSeries"], "volume_usd", "date_at")
    fees = _series(snap["totalFeesSeries"], "fees_usd", "date_at")
    tvl = _series(snap["tvlChartSeries"], "value").rename("confidential_tvl_usd")
    tvl = tvl[tvl > 1e6]
    last_full = volume.index.max() - pd.Timedelta(days=1)  # the last day on the page is partial

    # 1. Wallets
    flows = pd.read_csv(OUT / "revenue_wallet_flows.csv", parse_dates=["date"])
    flows = flows[flows["date"] <= pd.Timestamp(snap_date)]  # the page's wallet totals are live on the snapshot day
    mine = flows[(flows.dir == "in") & flows.is_near & ~flows.internal].groupby("wallet")["amount"].sum()
    wallets = {r["name"]: {"official_near": r["nearAmount"], "rebuilt_near": float(mine.get(r["name"], 0.0)),
                           "ratio": float(mine.get(r["name"], 0.0) / r["nearAmount"])} for r in snap["rows"]}
    total_off = sum(r["nearAmount"] for r in snap["rows"])

    # 2. Offset of emissions, by month (their cumulative series, differenced)
    cum = pd.DataFrame(snap["absoluteRevEmissions"])
    cum.index = pd.to_datetime(cum["date"])
    daily = cum[["emissionsNear", "revenueNear"]].diff().fillna(cum[["emissionsNear", "revenueNear"]].iloc[0])
    m = daily.resample("MS").sum()
    m["official_offset"] = m["revenueNear"] / m["emissionsNear"]
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    m = m.join(sm[["net_issuance_near", "captured_near_3_wallets", "captured_share_of_issuance"]])
    both = m.dropna().loc["2026-02-01":]

    # 3. Take rate on official volume and fees
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    df = pd.concat([volume, fees, rev], axis=1, sort=True).loc[FEE_SWITCH:last_full].fillna(0.0)
    mon = df.resample("MS").sum()
    wk = df.resample("W-MON", label="left", closed="left").sum()
    wk = wk[df.resample("W-MON", label="left", closed="left").size() == 7]
    for t in (mon, wk):
        t["gross_fee_bps"] = t["fees_usd"] / t["volume_usd"] * 1e4
        t["take_bps"] = t["rebuilt_total_usd"] / t["volume_usd"] * 1e4
        t["capture_of_fees"] = t["rebuilt_total_usd"] / t["fees_usd"]
    m = m.join(mon)

    # 5. Revenue as NEAR reports it (monthly, in NEAR) against the NEAR reaching the wallets.
    # The page books each month's revenue on the 1st and updates the current month daily, so only
    # monthly totals can be compared. If the ratio of the two is stable, both show the same trend.
    definitions = None
    if "revenueSeries" in snap:
        rs = pd.DataFrame(snap["revenueSeries"])
        rs.index = pd.to_datetime(rs["period_month"])
        m = m.join(rs[["revenue_usd", "revenue_near"]].rename(columns={"revenue_usd": "official_revenue_usd", "revenue_near": "official_revenue_near"}))
        near_in = flows[(flows.dir == "in") & flows.is_near & ~flows.internal].set_index("date")["amount"]
        near_in = near_in[near_in.index < pd.Timestamp(snap_date)]  # complete days only
        wallets_m = near_in.resample("MS").sum()
        m["wallets_near_in"] = wallets_m.reindex(m.index)
        m["official_over_wallets_near"] = m["official_revenue_near"] / m["wallets_near_in"]
        full = m.loc["2026-03-01":"2026-10-01"]  # complete months after the fee switch
        cur = m.index[-1]
        cur_days = df.loc[cur:]
        definitions = {
            "mar_oct_official_usd": float(full["official_revenue_usd"].sum()), "mar_oct_wallets_usd": float(full["rebuilt_total_usd"].sum()),
            "mar_oct_official_over_wallets_usd": float(full["official_revenue_usd"].sum() / full["rebuilt_total_usd"].sum()),
            "official_over_wallets_near": {str(k.date())[:7]: round(float(v), 3) for k, v in m["official_over_wallets_near"].loc["2026-07-01":].items()},
            "oct_take_bps": {"official": float(m.loc["2026-10-01", "official_revenue_usd"] / m.loc["2026-10-01", "volume_usd"] * 1e4),
                             "wallets": float(m.loc["2026-10-01", "take_bps"])},
            "current_month": str(cur.date())[:7], "current_month_wallet_days": int(len(cur_days)),
            "current_month_take_bps_wallets": float(cur_days["rebuilt_total_usd"].sum() / cur_days["volume_usd"].sum() * 1e4),
            "current_month_take_bps_official_implied": float(cur_days["rebuilt_total_usd"].sum() / cur_days["volume_usd"].sum() * 1e4
                                                             * m.loc[cur, "official_over_wallets_near"]),
        }
    mechanisms = None
    if "captureByMechanism" in snap:
        cb = snap["captureByMechanism"]
        mechanisms = {w: {name: cb.get(f"pp_{k}_{w}") for k, name in MECHANISMS.items()} for w in ("d7", "d30", "ytd", "all_time")}
        for w in mechanisms:
            mechanisms[w]["total"] = float(sum(v for v in mechanisms[w].values() if v is not None))

    OUT.mkdir(parents=True, exist_ok=True)
    m.to_csv(OUT / "official_monthly.csv")
    wk.to_csv(OUT / "official_weekly.csv")
    tvl.to_csv(OUT / "official_tvl.csv")
    oct_w = wk.loc["2026-10-05":"2026-10-26"]
    out = {
        "snapshot": snap_date,
        "wallets": wallets,
        "wallets_total": {"official_near": total_off, "rebuilt_near": float(mine.sum()), "ratio": float(mine.sum() / total_off)},
        "offset_feb_to_last_full_month": {
            "months": [str(both.index.min().date())[:7], str(both.index.max().date())[:7]],
            "official": float(both["revenueNear"].sum() / both["emissionsNear"].sum()),
            "rebuilt": float(both["captured_near_3_wallets"].sum() / both["net_issuance_near"].sum()),
            "official_emissions_near": float(both["emissionsNear"].sum()), "rebuilt_issuance_near": float(both["net_issuance_near"].sum()),
            "official_revenue_near": float(both["revenueNear"].sum()), "rebuilt_captured_near": float(both["captured_near_3_wallets"].sum()),
        },
        "official_ytd": {"date": str(cum.index.max().date()), "emissions_near": float(cum["emissionsNear"].iloc[-1]),
                         "revenue_near": float(cum["revenueNear"].iloc[-1]),
                         "offset": float(cum["revenueNear"].iloc[-1] / cum["emissionsNear"].iloc[-1])},
        "take_october_weeks_bps": float(oct_w["rebuilt_total_usd"].sum() / oct_w["volume_usd"].sum() * 1e4),
        "capture_october_weeks": float(oct_w["rebuilt_total_usd"].sum() / oct_w["fees_usd"].sum()),
        "last_week": {"week": str(wk.index.max().date()), "take_bps": float(wk["take_bps"].iloc[-1]),
                      "capture_of_fees": float(wk["capture_of_fees"].iloc[-1]), "gross_fee_bps": float(wk["gross_fee_bps"].iloc[-1]),
                      "volume_usd": float(wk["volume_usd"].iloc[-1])},
        "tvl": {"last_usd": float(tvl.iloc[-1]), "last_date": str(tvl.index.max().date()), "peak_usd": float(tvl.max()),
                "peak_date": str(tvl.idxmax().date()), "change_from_peak": float(tvl.iloc[-1] / tvl.max() - 1),
                "change_30d": float(tvl.iloc[-1] / tvl.iloc[-31] - 1)},
    }
    if definitions:
        out["revenue_definitions"] = definitions
    if mechanisms:
        out["capture_by_mechanism"] = mechanisms
    (OUT / "official_crosscheck.json").write_text(json.dumps(out, indent=1))
    return out


def main(refresh: bool = False) -> None:
    if refresh:
        try:
            fetch()
        except Exception as e:  # noqa: BLE001
            print(f"WARNING revenue.near.org fetch failed, using the last snapshot: {e}")
    out = crosscheck()
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(pd.read_csv(OUT / "official_monthly.csv", index_col=0).round(3).to_string())
    print(pd.read_csv(OUT / "official_weekly.csv", index_col=0).tail(12).round(3).to_string())
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    import sys
    main(refresh="--refresh" in sys.argv)
