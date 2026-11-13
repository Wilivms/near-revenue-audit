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


def main() -> None:
    out = {"queries": "sql/*.sql, run on 2026-11-13", "revenue": revenue(), "supply": supply(), "activity": activity()}
    (OUT / "bigquery_crosscheck.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
