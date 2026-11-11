# NEAR Revenue Audit

[![tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml/badge.svg)](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)

*Investment Thesis track (`thesis`), NEAR HACKATHON 2026. Data to {{data_to}}.*

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. Several public dashboards, NEAR's own included, now report how much. This project asks the questions they do not answer: **why** the revenue moved, **who** pays it, **what** the growth cost, whether it **lasts**, and what that means for the token. Every number below is computed from public data by code in this repository, and every document is rendered from those outputs.

- **Live dashboard:** https://near-revenue-audit.vercel.app. Headline figures and two kill criteria are recomputed in the browser from DefiLlama and the NEAR RPC on every visit; the rest refreshes daily.
- **The thesis on one page** (claim, evidence for and against, what would change our mind, what could not be computed): [`THESIS.md`](THESIS.md). **In full:** [`REPORT.md`](REPORT.md). **Working notes, dead ends and corrections:** [`RESEARCH_LOG.md`](RESEARCH_LOG.md). **Hypotheses written before the tests:** [`HYPOTHESES.md`](HYPOTHESES.md). **Reviewer FAQ:** [`FAQ.md`](FAQ.md). **Dated predictions:** [`predictions/`](predictions/).

> **For the jury, in 60 seconds**
> - **Verdict.** NEAR's protocol revenue is real (rebuilt from the chain: within {{rev_gap}} of DefiLlama, {{wallets_gap}} of NEAR's own dashboard), but buybacks offset only {{offset_rebuilt}} of new NEAR. Market cap is {{near_captured_mult}} annual captured revenue; supply stops growing below {{breakeven_now}}. NEAR is not yet a scarcity asset.
> - **What only this thesis shows.** NEAR's take more than doubled (from {{take_aug}} to {{take_oct}} bps) partly because of an airdrop: confidential swaps under NEAR@3.33 explain {{jump_fd}}–{{jump_levels}} of the rise, and the first drop cost {{drop1_over_uplift}} of the uplift. On {{oc_swaps}} 1Click swaps from the partner API, integrators keep {{oc_integrators_keep}} of the fee pool, and November's drop came from one integrator's burst ending. NEAR's own revenue series runs {{series_over_wallets}} above what its wallets receive.
> - **Held to account.** {{claims_passed}} findings re-checked in CI on every commit; hypotheses written before the data; a model that failed out of sample and says so; six predictions frozen on 2026-11-11 with a Bitcoin timestamp (P1 so far: {{p1_so_far}}, threshold 5.0).
> - **Next:** the [live dashboard](https://near-revenue-audit.vercel.app) (try the simulator), then [`THESIS.md`](THESIS.md) on one page.

[![The live dashboard: NEAR's captured revenue against issuance](docs/img/hero.jpg)](https://near-revenue-audit.vercel.app)

## The answer

NEAR's revenue is **real**: rebuilt from the chain, it matches DefiLlama within {{rev_gap}} and NEAR's own dashboard within {{wallets_gap}}. It is **too small** to support the token on supply: buybacks offset {{offset_rebuilt}} of issuance, and market cap is {{near_captured_mult}} annual captured revenue against {{breakeven_now}} needed for supply to stop growing ({{breakeven_cut}} once the approved issuance cut is phased in). Many theses in this track reach those two results. What this one adds is the **why**:

- **The doubling was partly bought.** NEAR's take went from {{take_aug}} to {{take_oct}} bps of volume between August and October. The largest identified driver is confidential swaps ({{conf_share_aug}} → {{conf_share_oct}} of volume), which pay NEAR {{premium_range}} bps against {{public_range}} on public swaps and explain {{jump_fd}} to {{jump_levels}} of the rise, depending on the method. They grew under an airdrop campaign (NEAR@3.33) whose first drop cost {{drop1_over_uplift}} of the revenue uplift.
- **It is already easing, and the model said so by failing.** The weekly fit missed its first unseen week ({{oos_actual}} against {{oos_pred_fd}}–{{oos_pred}} predicted). In early November the take fell to {{take_last_week}} bps on three sources while confidential TVL fell {{tvl_from_peak}} from its peak.
- **NEAR does not own the customer.** On {{oc_swaps}} 1Click swaps, integrators keep about {{oc_integrators_keep}} of the fee pool; the largest (SwapKit) takes {{sk_fees}} of app fees and sends NEAR {{sk_near}} of its revenue. In November, NEAR's 1Click take fell from {{oc_bps_oct}} to {{oc_bps_nov}} bps, mostly because one integrator's burst (Trust Wallet, {{trust_burst_vol}} of ZEC at 20 bps in late October) stopped; NEAR's own front-end revenue held.
- **NEAR's own revenue series runs {{series_over_wallets}} above what its three revenue wallets receive**, every month ({{series_ratio_min}}–{{series_ratio_max}}×), while the wallet totals agree within {{wallets_gap}}. The gap is not fees waiting to be swept; it is an open question put to NEAR.
- **Usage does not lead the price.** The track's own hypothesis: {{ll_sig}} of {{ll_tests}} lead-lag tests are significant after Holm's correction, over {{ll_weeks}} weeks.

## Findings, each one a check

`make verify` rebuilds every document from the outputs and re-runs these checks; it fails if a finding no longer follows from the data or a document has drifted from it. Result on the committed data: **{{claims_passed}} hold**.

{{claims_table}}

## Try it (do X → see Y)

| What would it take? (simulator) | Every finding as a live check |
|---|---|
| [![Simulator](docs/img/simulator.jpg)](https://near-revenue-audit.vercel.app/#simulator) | [![Checks](docs/img/checks.jpg)](https://near-revenue-audit.vercel.app/#checks) |

Everything below runs offline on the committed snapshots in `data/raw/` (listed with their sha256 in `data/raw/MANIFEST.json`).

```bash
git clone https://github.com/Wilivms/near-revenue-audit && cd near-revenue-audit
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make check-clean      # rebuilds everything, runs the tests, then compares every output with the committed one
make verify           # renders README/REPORT/FAQ/THESIS from the outputs and re-checks the findings
```

| Command | You should see |
| --- | --- |
| `make check-clean` | the tests pass, then `29/29 outputs match the committed ones` (text exactly, numbers to 1e-9) |
| `make verify` | `{{claims_passed}} findings hold` and no stale document |
| `make revenue` | revenue rebuilt from the 3 revenue wallets vs DefiLlama: {{rev_rebuilt_exact}} vs {{rev_llama_exact}} since the fee switch |
| `make official` | the same wallets against NEAR's own dashboard ({{wallets_gap}} apart), the take rate on both revenue definitions, capture by mechanism |
| `make confidential` | the weekly fit ({{fit_pub}} bps public, {{fit_conf}} confidential; {{fd_conf}} on week-to-week changes), the share of the jump explained, the airdrop counterfactual, the out-of-sample week, H4.1 |
| `make supply` | Feb–Oct 2026: {{issued_feb_oct}} NEAR issued, {{captured_feb_oct}} captured ({{offset_rebuilt}}) |
| `make montecarlo` | 11 scenarios to end-2027; base case {{mc_base}} of 2027 issuance offset; break-even at {{be_vol_now}}/day of volume at {{take_now}} bps |
| `make governance` | HSP-029 read from `vote.dao`: {{hsp_for}} of veNEAR cast in favour, timelock ends {{hsp_timelock_end}} |
| `make leadlag` | {{ll_tests}} lead-lag tests of usage against price, {{ll_sig}} significant after Holm |
| `make predictions` | six frozen predictions, resolved as their dates pass |
| `make dashboard-serve` | the dashboard at http://localhost:8000 |

With network access, `make refresh` fetches fresh snapshots and re-runs everything. A daily GitHub Action does this and commits `dashboard/live.json`, which the hosted dashboard loads first; `dashboard/data.json` stays the reproducible one.

## Judging map

| Criterion | Where to check it |
| --- | --- |
| Runs as described | `make check-clean` (CI runs it on every push: badge above); `make verify`; `data/raw/MANIFEST.json` with a test that every snapshot matches its hash |
| Evidence, not conviction | 13 findings with explicit pass conditions (above); hypotheses and kill criteria registered before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), unchanged since its first commit); results against expectations reported as written (H4.1 rejected, the fit's out-of-sample miss, a kill criterion triggered on 1Click) |
| Technical implementation | revenue rebuilt from wallet histories ([`revenue_wallets.py`](src/analysis/revenue_wallets.py)); supply from archival-RPC headers ([`supply.py`](src/analysis/supply.py)); {{oc_swaps}} swaps from the Intents Explorer API ([`intents_explorer.py`](src/ingest/intents_explorer.py), [`swaps.py`](src/analysis/swaps.py)); robustness of the channel fit ([`confidential.py`](src/analysis/confidential.py)); joint block bootstrap with a walk-forward backtest ([`montecarlo.py`](src/analysis/montecarlo.py), [`backtest_mc.py`](src/analysis/backtest_mc.py)); governance read on-chain ([`governance.py`](src/analysis/governance.py)) |
| Design | the dashboard: a what-if simulator on the break-even identity, live kill criteria, a scenario fan chart, a "show the numbers" table under each chart and the sources listed on the page; light theme, phone widths, reduced-motion support |
| Impact | findings that change how NEAR's revenue should be read: the September jump decomposed and costed, the integrator economics of 1Click, a 20% gap inside NEAR's own revenue reporting, a public threshold ($177M/day) shown to be 3–6× too low |
| Originality | swap-level data no other thesis uses; an incentive's cost set against the revenue it bought; a model whose own failure is published; NEAR's dashboard audited against the chain |
| Sustainability | `make refresh` and a daily Action; predictions that resolve from 2026-11-15 to 2027-04-02 with a resolver; MIT licence |

## Predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv): sha256 committed next to it (checked by a test) and timestamped in Bitcoin with OpenTimestamps (`ots verify predictions/PREDICTIONS.csv.ots`). Two resolve before judging starts (P1, P2 on 2026-11-15), one on its second day (P3), the rest by April 2027. `make predictions` resolves those whose date has passed; results go to [`predictions/RESULTS.md`](predictions/RESULTS.md).

Reading so far, on data to {{data_to}} (not a resolution): **P1** {{p1_so_far}} against a threshold of 5.0; **P2** {{p2_so_far}} against 140M; **P3** {{p3_so_far}}. The daily refresh updates these on the dashboard's Checks section.

## What NEAR's own dashboard shows, and what this adds

NEAR published [revenue.near.org](https://revenue.near.org/) in November 2026, after this rebuild. It shows **how much**; this audit asks what it is worth.

| Question | revenue.near.org | This audit |
| --- | --- | --- |
| How much revenue, how many NEAR bought? | Yes | Rebuilt independently from the chain; wallets agree within {{wallets_gap}}; its revenue series runs {{series_over_wallets}} above them |
| Who pays it? | No | Per integrator and per asset on {{oc_swaps}} 1Click swaps, to {{oc_to}} |
| What did the growth cost? | No | Drop 1 of NEAR@3.33 cost {{drop1_over_uplift}} of the revenue uplift; net {{net_near}} NEAR removed |
| Will it last? | No | Pre-registered kill criteria, a fit that failed out of sample, dated predictions |
| What does it mean for the token? | Offset to date | The break-even identity ({{breakeven_now}}, {{breakeven_cut}} after HSP-029, vs {{near_captured_mult}} today), a 2027 Monte Carlo with a backtest, peers, holder risk and dilution |

## Method

| Pillar | Question | Main sources |
| --- | --- | --- |
| 1. Ledger | Does reported revenue reach NEAR's wallets, and does it stay there? | NearBlocks (3 revenue wallets), DefiLlama, revenue.near.org, DAO proposals read on-chain |
| 2. Supply | Do buybacks offset issuance? | Archival RPC total supply, revenue wallets, HSP-029 on `vote.dao` |
| 3. Quality of revenue | Who pays, through which channel, on which asset? | {{oc_swaps}} 1Click swaps (NEAR Intents Explorer API), NEAR's Dune dashboard |
| 4. Incentives | How much growth is bought (NEAR@3.33)? | NEAR's Dune dashboard and revenue.near.org (confidential volume and TVL) |
| 5. Valuation | Where does it go by end-2027? | Monte Carlo (joint block bootstrap), walk-forward backtest |
| 6. Context | Peers, competitors, usage vs price, the holder's view | DefiLlama, CoinGecko, NearBlocks charts, RPC validators |

## NEAR integration

A data project: NEAR is the subject and the main source. It reads mainnet through RPC and archival RPC (total supply at chosen blocks, validators, protocol config, `intents.near` views for the fee and fee collector, the House of Stake proposal on `vote.dao`), NearBlocks (wallet histories, `intents.near` admin calls, daily chain activity), the NEAR Intents Explorer API (per-swap 1Click data), and NEAR's own Dune and revenue dashboards. Nothing is written to the chain and no key is used, except the read-only Explorer API key, which stays in a git-ignored `.env`.

## Data sources and how they were obtained

- **DefiLlama API** (fees, revenue, holders revenue, volume of NEAR Intents; NEAR and BTC prices; peers), **CoinGecko** (market caps), **NEAR RPC and archival RPC**, **NearBlocks API**.
- **NEAR Intents Explorer API**: per-swap 1Click data; needs a partner key in `INTENTS_JWT` (git-ignored `.env`, never committed). The raw swaps are not committed; their aggregates in `data/processed/` are. Collected up to {{oc_to}}.
- **NEAR's Dune dashboard** ([dune.com/near/near-intents](https://dune.com/near/near-intents)): Dune's API needs a paid plan, so the public result tables were read page by page in a browser and saved as text in `data/raw/dune/`, with each query id in the file header.
- **NEAR's revenue dashboard** ([revenue.near.org](https://revenue.near.org/)): its series are embedded in the page; `make refresh` saves them to `data/raw/near_revenue/`.

## Hackathon disclosures

- **Timeline**: first commit 2026-10-29, after the 2026-10-19 announcement (Q-001); everything here was built in the hackathon window.
- **One project**: this is the author's only submission to NEAR HACKATHON.
- **Libraries and tools** (Q-005): Python (requests, pandas, numpy, pytest, opentimestamps-client), Playwright for screenshots, vanilla HTML/SVG for the dashboard, Vercel for hosting. Code written with the help of AI assistants (Claude).
- **Not investment advice.** Independent research, not affiliated with NEAR Foundation.

## License

MIT
