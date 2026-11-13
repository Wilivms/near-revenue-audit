"""Third-source check on NEAR's public BigQuery dataset (the source the track suggests).

The three queries in sql/ were run by hand in the BigQuery console (free sandbox, no billing account) on
2026-11-13 and their results saved in data/raw/bigquery/. This module compares them with the sources the
pipeline uses, so anyone can re-run the queries and see the same agreement:

- revenue: NEAR transferred into the three revenue wallets since the fee switch (receipt_actions) against
  the NearBlocks wallet histories that the revenue rebuild uses, month by month;
- supply: total supply at the last block of each day (blocks) against the archival-RPC samples, and net
  issuance Feb–Oct against supply_monthly.csv;
- activity: daily transactions and distinct signers (transactions) against the NearBlocks charts used in
  the lead-lag tests, and the share of transactions sent to intents.near.

Output: data/processed/bigquery_crosscheck.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..ingest.sources import RAW
from .ledger import OUT
from .leadlag import _chain

WALLETS = {"buybacks.multisignature.near", "fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"}
BQ = RAW / "bigquery"


def _latest(prefix: str) -> pd.DataFrame:
    return pd.read_csv(sorted(BQ.glob(f"{prefix}_*.csv"))[-1], parse_dates=["block_date"])


def revenue() -> dict:
    bq = _latest("wallet_transfers")
    ext = bq[~bq["sender"].isin(WALLETS | {"system"})]
    flows = pd.read_csv(OUT / "revenue_wallet_flows.csv", parse_dates=["date"])
    nb = flows[(flows["dir"] == "in") & flows["is_near"] & ~flows["internal"] & (flows["date"] >= "2026-02-23")]
    last_full = nb["date"].max() - pd.Timedelta(days=1)  # the NearBlocks snapshot's last day may be partial
    a = ext[ext["block_date"] <= last_full].groupby(ext["block_date"].dt.to_period("M"))["near_in"].sum()
    b = nb[nb["date"] <= last_full].groupby(nb["date"].dt.to_period("M"))["amount"].sum()
    m = pd.concat([a.rename("bigquery"), b.rename("nearblocks")], axis=1).fillna(0)
    return {"to": str(last_full.date()), "near_bigquery": float(m["bigquery"].sum()), "near_nearblocks": float(m["nearblocks"].sum()),
            "max_monthly_gap": float((m["bigquery"] / m["nearblocks"] - 1).abs().max()),
            "monthly": {str(k): [round(float(r.bigquery), 3), round(float(r.nearblocks), 3)] for k, r in m.iterrows()},
            "from_intents_near": float(ext.loc[ext["sender"] == "intents.near", "near_in"].sum() / ext["near_in"].sum())}


def supply() -> dict:
    s = _latest("supply_daily").sort_values("last_block")
    rpc = pd.DataFrame(json.loads((RAW / "supply_history" / "blocks.json").read_text())).sort_values("height")
    rpc = rpc[rpc["height"].between(s["last_block"].min(), s["last_block"].max())]
    rel = rpc["supply"] / np.interp(rpc["height"], s["last_block"], s["total_supply_near"]) - 1
    d = s.set_index("block_date")["total_supply_near"]
    issued = float(d.loc["2026-10-31"] - d.loc["2026-01-31"])
    ours = float(pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True).loc["2026-02":"2026-10", "net_issuance_near"].sum())
    return {"rpc_samples": int(len(rpc)), "max_abs_rel_gap": float(rel.abs().max()), "issued_feb_oct_bigquery": issued,
            "issued_feb_oct_pipeline": ours, "issued_gap": issued / ours - 1}


def activity() -> dict:
    a = _latest("activity_daily").set_index("block_date")
    m = a.join(_chain(), how="inner")
    oct25, oct26 = a.loc["2025-10"], a.loc["2026-10"]
    return {"days": int(len(m)), "txns_ratio_min": float((m["transactions"] / m["txns"]).min()),
            "txns_ratio_max": float((m["transactions"] / m["txns"]).max()),
            "signers_vs_active_median": float((m["signers"] / m["active_accounts"]).median()),
            "intents_share_of_txns_oct2025": float(oct25["tx_to_intents"].sum() / oct25["transactions"].sum()),
            "intents_share_of_txns_oct2026": float(oct26["tx_to_intents"].sum() / oct26["transactions"].sum())}


def intents_signers() -> dict:
    """Late October against early November, 12 days each: transactions to intents.near, who signs them,
    and NEAR's captured revenue over the same days."""
    s = pd.read_csv(sorted(BQ.glob("intents_signers_*.csv"))[-1]).set_index("period")
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    a, b = s.loc["oct20_31"], s.loc["nov01_12"]
    ra, rb = float(rev.loc["2026-10-20":"2026-10-31"].sum()), float(rev.loc["2026-11-01":"2026-11-12"].sum())
    return {"windows": "2026-10-20..31 vs 2026-11-01..12", "txns_change": float(b.txns / a.txns - 1),
            "self_signed_share_nov": float(b.by_intents_near / b.txns),
            "self_signed_share_of_increase": float((b.by_intents_near - a.by_intents_near) / (b.txns - a.txns)),
            "other_signers_change": float(b.other_signers / a.other_signers - 1), "by_others_change": float(b.by_others / a.by_others - 1),
            "revenue_change": rb / ra - 1, "revenue_oct20_31_usd": ra, "revenue_nov01_12_usd": rb}


def pool_revenue() -> dict:
    """How much of the NEAR withdrawn to the two revenue wallets came through accounts that the confidential pool
    (51e8f94d..., about $136M, the size of NEAR's confidential TVL) had funded; and what that NEAR is worth per dollar
    of confidential volume (NEAR's Dune dashboard), against the rest per dollar of public volume."""
    from .revenue_wallets import near_price
    w = pd.read_csv(sorted(BQ.glob("pool_revenue_weekly_*.csv"))[-1], parse_dates=["week"]).groupby("week")[["near", "near_from_pool"]].sum()
    month = w.groupby(w.index.to_period("M")).sum()
    px = near_price()
    px.index = pd.to_datetime(px.index).tz_localize(None)
    wpx = px.resample("W-MON", label="left", closed="left").mean().reindex(w.index)
    c = pd.read_csv(OUT / "confidential_weekly.csv", index_col=0, parse_dates=True)
    j = w.assign(pool_usd=w["near_from_pool"] * wpx, rest_usd=(w["near"] - w["near_from_pool"]) * wpx).join(c[["confidential_usd", "public_usd"]], how="inner")
    j = j.loc["2026-08-10":]  # the weeks of the take-rate fit (REPORT section 2)
    return {"monthly_share": {str(k): float(v) for k, v in (month["near_from_pool"] / month["near"]).items()},
            "share_since_sep28": float(w.loc["2026-09-28":, "near_from_pool"].sum() / w.loc["2026-09-28":, "near"].sum()),
            "fit_weeks": f"{j.index.min().date()}..{j.index.max().date()}",
            "pool_bps_on_confidential": float(j["pool_usd"].sum() / j["confidential_usd"].sum() * 1e4),
            "rest_bps_on_public": float(j["rest_usd"].sum() / j["public_usd"].sum() * 1e4)}


def main() -> None:
    out = {"queries": "sql/*.sql, run on 2026-11-13", "revenue": revenue(), "supply": supply(), "activity": activity(),
           "intents_signers": intents_signers(), "pool_revenue": pool_revenue()}
    (OUT / "bigquery_crosscheck.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
