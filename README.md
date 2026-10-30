# NEAR Revenue Audit

*Working title. Track: Investment Thesis (`thesis`), NEAR HACKATHON 2026.*

**Question:** is NEAR's protocol revenue real, durable, or bought with incentives — and what does that imply for the long-term value of the NEAR token?

Most public NEAR theses quote headline figures (Intents volume, fees, buybacks). This project rebuilds those figures from the chain, reconciles them across sources, and states in advance what would prove the thesis wrong.

## How to reproduce (do X → see Y)

```bash
pip install -r requirements.txt
make data       # fetches DefiLlama, NEAR RPC, NearBlocks and price data into data/raw/<source>/<date>.json
make revenue    # rebuilds NEAR's captured revenue from its 3 revenue wallets → prints the reconciliation
                #   with DefiLlama (expect a ratio close to 1.00) and data/processed/revenue_rebuilt_daily.csv
make supply     # measured issuance (archival RPC) vs NEAR captured → data/processed/supply_monthly.csv
make ledger     # first-pass reconciliation on the buyback wallet only (kept to show the scope issue)
make swaps      # 1Click swap-level analysis → data/processed/swaps_weekly.csv, snapshot_windows.csv,
                #   retention.csv, snapshot_entrants.csv (needs the swap data, see below)
```

Findings so far, with the reasoning behind each one: [`RESEARCH_LOG.md`](RESEARCH_LOG.md).

Committed snapshots in `data/raw/` let anyone re-run the analysis on exactly the data we used, without network access: skip `make data`.

Swap-level data (`data/intents_v2/`, ~2.4M swaps) is not committed: it comes from the partner-only Explorer API. Collect it with `python3 -m src.ingest.intents_explorer` (continuous window) and `--sample-weeks` (Feb–Jul); the aggregated outputs in `data/processed/` are committed.

## Method

The thesis is an audit in five pillars. Hypotheses were written **before** running the analysis: see [`HYPOTHESES.md`](HYPOTHESES.md).

| Pillar | Question | Main sources |
| --- | --- | --- |
| 1. Ledger | Does reported revenue actually reach the buyback wallet? | DefiLlama, NearBlocks (`buybacks.multisignature.near`), NEAR price |
| 2. Supply | Do buybacks offset issuance? | NEAR RPC (supply, inflation), NearBlocks |
| 3. Quality of revenue | Where does revenue come from, and is it concentrated? | NEAR Intents Explorer API |
| 4. Incentives | How much growth is bought with incentives (NEAR@3.33)? | Intents Explorer API (confidential flows) |
| 5. Valuation | What is the range of outcomes for NEAR supply and value? | Monte Carlo on the above |

## Status

Work in progress. See `HYPOTHESES.md` for what is being tested.

## Data sources

- DefiLlama API (fees, revenue, holders revenue, volume, TVL of NEAR Intents; NEAR price)
- NEAR mainnet RPC (`rpc.mainnet.near.org`)
- NearBlocks API (transaction history of the buyback wallet)
- NEAR Intents Explorer API (per-swap data; requires a partner JWT in the `INTENTS_JWT` environment variable, never committed)

## License

MIT
