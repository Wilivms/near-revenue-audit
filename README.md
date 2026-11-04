# NEAR Revenue Audit

[![tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml/badge.svg)](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)

*Investment Thesis track (`thesis`), NEAR HACKATHON 2026.*

**Question:** is NEAR's protocol revenue real, durable, or bought with incentives, and what does that imply for the NEAR token?

- **Live dashboard:** https://near-revenue-audit.vercel.app (headline figures and kill criteria recomputed from DefiLlama and the NEAR RPC on every visit; analysis outputs refreshed daily).
- **The thesis:** [`REPORT.md`](REPORT.md). **Working notes, dead ends, corrections:** [`RESEARCH_LOG.md`](RESEARCH_LOG.md). **Hypotheses written before the tests:** [`HYPOTHESES.md`](HYPOTHESES.md). **Reviewer FAQ:** [`FAQ.md`](FAQ.md).

## Findings in 60 seconds

| | Finding | Evidence |
| --- | --- | --- |
| Real | Revenue rebuilt from the chain matches DefiLlama within 0.1% ($7.29M since the 2026-02-23 fee switch) | `make revenue`, log 2 |
| Growing, partly bought | NEAR's take doubled from mid-September (≈2.2 → 5.4 bps of volume), mostly because confidential swaps went from 13% to 41% of volume; that growth follows the NEAR@3.33 airdrop, whose first drop (~$1.39M) about equals the revenue uplift it produced | `make confidential`, logs 24–25 |
| Not owned | On 1Click, integrators keep ~91% of the fee pool; SwapKit has 71% of app fees and sends NEAR ~1% of its revenue | `make swaps` outputs, logs 11, 18 |
| Too small | Buybacks offset about **one fifth** of issuance; market cap ≈ 200x annual captured revenue (moves with price; live on the dashboard) vs 41x needed for supply to stop growing | `make supply`, `make montecarlo`, logs 5–6, 17 |
| Still true in 2027 | Base case: 21% of 2027 issuance offset, 9% chance of a net deflationary 2027; a walk-forward test shows the engine leans optimistic | `make montecarlo`, `make backtest`, logs 17, 21 |
| Priced on something else | Peers whose holders share revenue trade at a median 22x; NEAR at 212x | `make comps`, log 22 |

## Try it (do X → see Y)

Everything below runs offline on the committed snapshots in `data/raw/`.

```bash
git clone https://github.com/Wilivms/near-revenue-audit && cd near-revenue-audit
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make reproduce        # runs every offline step and the tests; ends with "5 passed"
```

| Command | You should see |
| --- | --- |
| `make revenue` | captured revenue rebuilt from 3 revenue wallets vs DefiLlama: ratio 0.999, each month within ±5% |
| `make supply` | Feb–Oct 2026: 23.7M NEAR issued, 3.49M captured (14.7%) |
| `make confidential` | confidential share of volume by month (41% in Oct), weekly fit `0.65 bps × public + 12.2 bps × confidential`, H4.1 test (TVL $71M → $155M), airdrop counterfactual |
| `make montecarlo` | 9 scenarios (including an incentive wind-down) to end-2027 and the volume × take-rate table (break-even ≈ $750M/day at 5.4 bps) |
| `make backtest` | calibration of past forecasts (share inside the 10–90% band, mean PIT) |
| `make dashboard-serve` | the dashboard at http://localhost:8000 |
| `make test` | model checks: seed reproducibility, deflation identity, no look-ahead in the backtest |

With network access, `make refresh` fetches fresh snapshots (DefiLlama, NEAR RPC and archival RPC, NearBlocks, CoinGecko) and re-runs everything. A daily GitHub Action does this and commits the refreshed `dashboard/data.json`, which the hosted dashboard loads.

## Method

Hypotheses were written **before** the analysis ([`HYPOTHESES.md`](HYPOTHESES.md)); each result in the log says whether it holds, was rejected, or could not be tested, and pre-registered kill criteria are monitored on the dashboard.

| Pillar | Question | Main sources |
| --- | --- | --- |
| 1. Ledger | Does reported revenue reach NEAR's wallets, and does it stay there? | NearBlocks (3 revenue wallets), DefiLlama, DAO proposals read on-chain |
| 2. Supply | Do buybacks offset issuance? | Archival RPC total supply, revenue wallets |
| 3. Quality of revenue | Who pays, through which channel, on which asset? | 2.4M 1Click swaps (NEAR Intents Explorer API), NEAR's Dune dashboard |
| 4. Incentives | How much growth is bought (NEAR@3.33)? | NEAR's Dune dashboard (confidential volume and TVL) |
| 5. Valuation | Where does it go by end-2027? | Monte Carlo (joint block bootstrap), walk-forward backtest |
| 6. Context | Peers, competitors, the holder's view | DefiLlama, CoinGecko, RPC validators |

## Data sources and how they were obtained

- **DefiLlama API** (fees, revenue, holders revenue, volume of NEAR Intents; NEAR and BTC prices; peers), **CoinGecko** (market caps), **NEAR RPC and archival RPC** (supply, protocol config, validators, contract views), **NearBlocks API** (wallet histories, `intents.near` admin calls).
- **NEAR Intents Explorer API**: per-swap 1Click data; needs a partner key in `INTENTS_JWT` (git-ignored `.env`, never committed). The raw swaps are not committed; their aggregates in `data/processed/` are.
- **NEAR's Dune dashboard** ([dune.com/near/near-intents](https://dune.com/near/near-intents)): Dune's API needs a paid plan, so the public result tables were read page by page in a browser and saved as text in `data/raw/dune/`, with each query id in the file header.

## Hackathon disclosures

- **Timeline**: first commit 2026-10-29, after the 2026-10-19 announcement (Q-001); everything here was built in the hackathon window.
- **Second project by the same author** (Q-015): a cross-chain portfolio rebalancer under an on-chain risk mandate, independent of this repository. Its repository is linked here before submission.
- **Libraries and tools** (Q-005): Python (requests, pandas, numpy, pytest), Playwright for dashboard screenshots, vanilla HTML/SVG for the dashboard, Vercel for hosting. Code written with the help of an AI assistant (Claude).
- **Not investment advice.** Independent research, not affiliated with NEAR Foundation.

## License

MIT
