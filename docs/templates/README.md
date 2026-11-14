# NEAR Revenue Audit

[![tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml/badge.svg)](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)

*Investment Thesis track (`thesis`), NEAR HACKATHON 2026. Data to {{data_to}}.*

**[Live dashboard](https://near-revenue-audit.vercel.app)** · **[One-page thesis](THESIS.md)** · **[Full report](REPORT.md)** · **[Headline numbers, exactly](#the-headline-numbers-exactly)** · **[Where we were wrong](#where-we-were-wrong-and-what-changed)** · rebuild everything: `make setup && . .venv/bin/activate && make check-clean`

[![The live dashboard: NEAR's captured revenue against issuance](docs/img/hero.jpg)](https://near-revenue-audit.vercel.app)

**Is NEAR's protocol revenue real, durable, or bought?** Since 2026-02-23, NEAR Intents fees buy back NEAR. This project rebuilds that revenue from the chain and answers what the dashboards do not: why it moved, who pays it, what the growth cost, and what it means for the token.

## For judges: the project in 3 minutes

**1. The answer**
- **Real.** Rebuilt from NEAR's three revenue wallets, it matches DefiLlama within {{rev_gap}}, NEAR's own dashboard within {{wallets_gap}} and NEAR's BigQuery dataset to the last digit.
- **Too small for the token.** Buybacks offset {{offset_rebuilt}} of new NEAR ({{offset_window}}). Market cap is {{near_captured_mult}} captured revenue; supply stops growing only below {{breakeven_now}}.
- **Partly bought.** NEAR's take doubled from {{take_aug}} to {{take_oct}} bps in two months, a fifth to most of it from confidential swaps during an airdrop whose first drop cost {{drop1_over_uplift}} of the revenue it added. It is already easing ({{take_last_week}} bps in early November).
- **NEAR does not own the customer.** On 1Click, integrators keep {{oc_integrators_keep}} of the fee pool.
- **Priced level with its rivals.** In {{qr_rounds}} live quote rounds against Relay, Across and LI.FI, 1Click paid users the most in {{qr_best_share}} of swaps, median {{qr_median}} from the best: rivals are not undercutting NEAR Intents so far.

**2. Follow $100** ({{f100_from}} to {{f100_to}}, {{f100_vol}} of Intents volume)

| Of every $100 swapped through NEAR Intents | |
| --- | --- |
| Paid by users in fees (all parties) | {{f100_fees}} (DefiLlama's fee rate up to {{f100_fees_to}}: its later days were still being revised) |
| Reaches NEAR's three revenue wallets | **{{f100_near}}** (buyback multisig {{f100_bb}}, front-end fund {{f100_fe}}) |
| New NEAR issued over the same days | **{{f100_issued}}** |
| Revenue as a share of new issuance | **{{f100_cover}}** ({{offset_rebuilt}} over {{offset_window}}) |

And on 1Click (about a quarter of Intents volume, where the retail apps and their fees are), each swap records what was sent and what was delivered, so the user's whole cost can be split. Per $100 on average: **{{sc_cost_100}}**, of which {{sc_int_100}} to integrators, **{{sc_near_100}} to NEAR** and {{sc_rest_100}} to solvers and networks ({{sc_near_share}} to NEAR, F18). By size:

{{sc_follow_table}}

Each row applies the measured cost of real swaps in the band from that size to three times it ($10–30, $100–300, …); the $1M row uses swaps of $300k–1M, as there were only a handful above $1M. The cost falls with size until about $3k (small swaps carry fixed network costs), is flat at {{sc_flat_lo}}–{{sc_flat_hi}} bps from $3k to $100k, then rises again above $100k as the solvers' spread widens, while NEAR's slice shrinks.

For supply to stop growing, the second bold line has to reach the third. On 1Click alone, a $100 swap pays {{f100_oc_pool}} in fees: {{f100_oc_int}} to integrators, {{f100_oc_near}} to NEAR.

**3. See it live: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app)**
- **Top of the page:** NEAR bought back per 100 issued, recomputed in your browser from live data.
- **"What would it take?"**: drag daily volume and NEAR's take rate until supply stops growing.
- **"Verify it in your browser"** (Checks section): one click reads the hash anchored on NEAR testnet, hashes the raw files, rebuilds the revenue from the raw receipts and compares it with this audit and NEAR's own dashboard. No key, no install.
- **"Every finding is a test"**: the {{claims_n}} findings, {{public_claims_n}} public claims about NEAR, six dated predictions and their on-chain anchors, all updated daily.

**4. Re-run it** (about 2 minutes, no key, no network after setup)

```
git clone https://github.com/Wilivms/near-revenue-audit && cd near-revenue-audit
make setup && . .venv/bin/activate
make check-clean     # → {{outputs_n}}/{{outputs_n}} outputs match the committed ones, {{claims_passed}} findings hold
make verify          # → prints every finding and the headline numbers above
```

**5. What only this project brings**
- **Revenue confirmed four independent ways, and it never revises**: DefiLlama, NEAR's dashboard, NEAR's BigQuery dataset and the withdrawals from `intents.near` agree within 0.5%; {{rv_rb_moved}} of {{rv_rb_pairs}} daily readings of the rebuilt revenue changed across {{rv_rb_snaps}} dated snapshots, while the aggregators revised their latest day of fees by up to {{rv_fee_factor}} (F16).
- **The questions the dashboards skip, answered with data**: the airdrop's role, who pays, and where the revenue now comes from: {{pool_share_late}} of what reaches the wallets since late September is paid out of the confidential pool (about $136M), worth {{pool_bps}} bps of confidential volume against {{pool_rest_bps}} on public ([REPORT section 10](REPORT.md#10-the-two-questions-near-did-not-answer-and-what-the-data-says)). And the user's whole cost of a swap, $10 to $1M: NEAR keeps {{sc_near_share}} of it (F18).
- **What the price implies, run backwards**: at a 15% discount rate and 3% growth, NEAR's market cap needs {{im_mid}}x today's captured revenue, or {{im_g5}} a year of growth for five years (REPORT section 4).
- **Events tested against a placebo, not narrated**: the October exploit and six other NEAR events (halving, fee switch, airdrop, HSP-029…), each compared with the same before/after split at every ordinary date of the year (F17, REPORT section 11).
- **Held to account**: every finding re-run in CI and stress-tested under {{rob_variants}} alternative choices (the one fragile finding says so); {{public_claims_n}} public claims tested at their own dates; six predictions timestamped on Bitcoin; [five corrections](#where-we-were-wrong-and-what-changed) dated in the research log.
- **Keeps itself current**: the dashboard refreshes every day, 1Click included, and each update is anchored on NEAR.

**Want more?** [`THESIS.md`](THESIS.md) is the one-page thesis (5 min). [`REPORT.md`](REPORT.md) is the full argument. [`FAQ.md`](FAQ.md) answers reviewers' objections. Everything below is the detail, with every number traceable to a command.

---

## The headline numbers, exactly

Each number with its window, its source and the command that rebuilds it. None of these commands needs a key or the network, and `make verify` prints all four.

| Number | What it is, exactly | Rebuild it |
| --- | --- | --- |
| **{{offset_rebuilt}}** of new NEAR offset | NEAR received by NEAR's three revenue wallets ÷ NEAR issued, {{offset_window}} (whole months since the 2026-02-23 fee switch). NEAR's own dashboard gives {{offset_official}} | `make supply official` |
| **{{near_captured_mult}}** market cap ÷ captured revenue | Market cap on {{mcap_date}} ({{near_mcap}}, CoinGecko) ÷ revenue the wallets received from {{r30_from}} to {{r30_to}}, annualised ×365/30 ({{r30_annual}} a year). Not the {{near_holders_mult}} on DefiLlama's holders revenue, which is used only to compare with peers on one definition | `make revenue comps` |
| **{{breakeven_now}}** break-even multiple | Supply stops growing when buybacks equal issuance ({{issuance}} of supply a year), so when market cap ÷ captured revenue falls to 1 ÷ {{issuance}}. At today's take that is about {{be_vol_now}} of daily volume | `make supply montecarlo` |
| **{{oc_integrators_keep}}** of the 1Click fee pool kept by integrators | 1Click swaps from {{oc_from}} to {{oc_to}} (partner API); fee pool = integrators' app fees + NEAR's protocol fee | `make oneclick-offline` recomputes it from the committed daily aggregates |

## Reading paths

| Time | Do | You see |
| --- | --- | --- |
| 2 min | Open the **[live dashboard](https://near-revenue-audit.vercel.app)** | the live reading (NEAR bought back per 100 issued, recomputed in your browser), then the simulator: move volume and take rate, see break-even |
| 5 min | Read **[`THESIS.md`](THESIS.md)** | the claim, evidence for and against, what would change our mind, what could not be computed, on one page |
| 2 min | Run `make setup && . .venv/bin/activate && make check-clean` | every output rebuilt from committed data and compared: `{{outputs_n}}/{{outputs_n}} outputs match`, `{{claims_passed}} findings hold` |
| 3 min | Open **[REPORT section 9](REPORT.md#9-public-claims-checked)** | {{public_claims_n}} public claims about NEAR tested at their own dates |
| as needed | **[`REPORT.md`](REPORT.md)** (the full argument), **[`FAQ.md`](FAQ.md)** (reviewer questions), **[`RESEARCH_LOG.md`](RESEARCH_LOG.md)** ({{log_n}} dated entries, dead ends and corrections), **[`HYPOTHESES.md`](HYPOTHESES.md)** (written before the tests), **[`predictions/`](predictions/)** | |

## Why this thesis is different

**Findings this thesis adds**
- **The doubling was partly bought.** NEAR's take went from {{take_aug}} to {{take_oct}} bps between August and October; confidential swaps under the NEAR@3.33 airdrop explain {{jump_fd}}–{{jump_levels}} of the rise, and the first drop cost {{drop1_over_uplift}} of the revenue it added.
- **NEAR does not own the customer.** On {{oc_swaps_30}} 1Click swaps from the partner API, integrators keep {{oc_integrators_keep}} of the fee pool; the 20 bps that NEAR's published fee schedule sets for integrator swaps is paid on a small part of their volume. November's drop came from one integrator's burst ending, while NEAR's own front-end revenue held.
- **NEAR's own revenue series runs {{series_over_wallets}} above what its three revenue wallets receive**, every month, while the wallet totals agree within {{wallets_gap}}.
- **It is already easing, and the model said so by failing.** The weekly fit missed its first unseen week ({{oos_actual}} against {{oos_pred_fd}}–{{oos_pred}} predicted). In early November the take fell to {{take_last_week}} bps on three sources while confidential TVL fell {{tvl_from_peak}} from its peak.
- **The two questions NEAR did not answer, narrowed to testable hypotheses:** confidential swaps pay about {{oq_bb_conf}} bps into the buyback multisig (matching NEAR's Dune fee table), and most of the {{series_over_wallets}} gap is quote-improvement revenue that never reaches the wallets that buy NEAR (without it: {{oq_gap_ytd_ex}} this year). [REPORT section 10](REPORT.md#10-the-two-questions-near-did-not-answer-and-what-the-data-says).
- **Most of NEAR's revenue now comes out of the confidential pool.** On the public chain, the share of the NEAR reaching the buyback multisig and the front-end fund that passes through accounts funded by the confidential pool (about $136M, the size of NEAR's confidential TVL) rose from {{pool_share_jun}} in June to {{pool_share_oct}} in October ({{pool_share_late}} since late September). Per dollar of confidential volume it is worth {{pool_bps}} bps, against {{pool_rest_bps}} bps for the rest on public volume: the confidential premium, measured from the payouts. (`make bigquery`)
- **Transaction counts mislead.** Over two 12-day windows (20–31 October, 1–12 November), transactions to `intents.near` changed {{bq_is_tx}} while NEAR's captured revenue changed {{bq_is_rev}}. NEAR's BigQuery dataset shows why: {{bq_is_self_inc}} of the increase is `intents.near` signing its own transactions; transactions from everyone else changed {{bq_is_others}}. A dashboard that counts transactions reads November as a boom. (`make bigquery`)
- **Valuation:** valued like peers whose holders receive revenue, this revenue supports about {{price_at_peer}} a NEAR, against {{price_now}} (daily close, {{price_date}}).

**Every number checked against independent sources**
- Revenue rebuilt from the chain matches DefiLlama within {{rev_gap}} and NEAR's own dashboard within {{wallets_gap}}; NEAR's public BigQuery dataset matches the wallet histories **to the last digit** ({{bq_rev_near}} NEAR) and issuance within {{bq_supply_gap}}.

**Held to account in public**
- {{claims_passed}} findings with explicit pass conditions, re-checked in CI on every commit; documents rendered from the outputs, so no figure is typed by hand.
- {{public_claims_n}} claims by NEAR, Nansen, analysts and the press tested at their own dates: {{public_claims_survive}} survive, {{public_claims_close}} are close, {{public_claims_fail}} do not hold.
- Hypotheses and kill criteria written before the analysis; the weekly model missed its first unseen week and the report says so.
- Six dated predictions, frozen on 2026-11-11, timestamped in Bitcoin and anchored on NEAR (testnet); two resolve before judging (P1 so far: {{p1_so_far}}, threshold 5.0).

**Reproducible by anyone**
- Offline from committed snapshots, one command, no key: `make check-clean`. Works with any Python (`make setup` fetches 3.12 if needed) and on a ZIP download.
- The 1Click results, which come from a partner API, are recomputed from published daily aggregates without the key (`make oneclick-offline`, finding F15); see [1Click data](#1click-data-what-you-can-check-without-a-key).

## Where we were wrong, and what changed

Kept in the open because a thesis is only as good as its corrections. Each one is dated in [`RESEARCH_LOG.md`](RESEARCH_LOG.md).

| What we said | What the data then showed | What changed | Log |
| --- | --- | --- | --- |
| A weekly fit explains NEAR's revenue from public and confidential volume | It missed its first unseen week: {{oos_actual}} actual against {{oos_pred_fd}}–{{oos_pred}} predicted | The airdrop is now "the largest identified driver" of the jump, {{jump_fd}}–{{jump_levels}} of it, not "most of it" | 30, 32 |
| Confidential swaps pay NEAR about 11 bps | The 11 bps came from a trend in the front-end fund; fitted wallet by wallet, the buyback multisig gets {{oq_bb_conf}} bps | Matches NEAR's own Dune fee table (7.4 bps) | 42 |
| The airdrop's cost cancels the revenue it added | Drop 1 cost {{drop1_over_uplift}} of the uplift, not all of it | Reported as a net gain, small against supply | 32 |
| The Monte Carlo engine sizes 2027 | In a walk-forward test it was too optimistic for 2026 | The 2027 figures are flagged as more likely too high than too low | 21 |
| The 92% integrator share covered 2.6M swaps | 2.6M was every swap collected at the time ({{oc_swaps}} now); the 30-day window holds {{oc_swaps_30}} | Both counts published separately; the 92% itself was right | 36 |

## Findings, each one a check

`make verify` rebuilds every document from the outputs and re-runs these checks; it fails if a finding no longer follows from the data or a document has drifted from it. Result on the committed data: **{{claims_passed}} hold**.

{{claims_table}}

## Try it (do X → see Y)

| What would it take? (simulator) | Every finding as a live check |
|---|---|
| [![Simulator](docs/img/simulator.jpg)](https://near-revenue-audit.vercel.app/#simulator) | [![Checks](docs/img/checks.jpg)](https://near-revenue-audit.vercel.app/#checks) |

Everything below runs offline on the committed snapshots in `data/raw/` (listed with their sha256 in `data/raw/MANIFEST.json`). Needs Python 3.12 or later (pandas 3, numpy 2.5; `make setup` gets it if yours is older) and `make`; no key, no account, no network. `make check-clean` takes about a minute; it also works on a ZIP download without git.

```bash
git clone https://github.com/Wilivms/near-revenue-audit && cd near-revenue-audit
make setup && . .venv/bin/activate   # Python 3.12+ and four pinned packages; fetches Python 3.12 with uv if yours is older
make check-clean      # rebuilds everything, runs the tests, then compares every output with the committed one
make verify           # renders README/REPORT/FAQ/THESIS from the outputs and re-checks the findings
```

| Command | You should see |
| --- | --- |
| `make check-clean` | the tests pass, then `{{outputs_n}}/{{outputs_n}} outputs match the committed ones` (text exactly, numbers to 1e-9) |
| `make verify` | `{{claims_passed}} findings hold` and no stale document |
| `make revenue` | revenue rebuilt from the 3 revenue wallets vs DefiLlama: {{rev_rebuilt_exact}} vs {{rev_llama_exact}} since the fee switch |
| `make official` | the same wallets against NEAR's own dashboard ({{wallets_gap}} apart), the take rate on both revenue definitions, capture by mechanism |
| `make confidential` | the weekly fit ({{fit_pub}} bps public, {{fit_conf}} confidential; {{fd_conf}} on week-to-week changes), the share of the jump explained, the airdrop counterfactual, the out-of-sample week, H4.1 |
| `make supply` | Feb–Oct 2026: {{issued_feb_oct}} NEAR issued, {{captured_feb_oct}} captured ({{offset_rebuilt}}) |
| `make montecarlo` | 11 scenarios to end-2027; base case {{mc_base}} of 2027 issuance offset; break-even at {{be_vol_now}}/day of volume at {{take_now}} bps |
| `make governance` | HSP-029 read from `vote.dao`: {{hsp_for}} of veNEAR cast in favour, timelock ends {{hsp_timelock_end}} |
| `make leadlag` | {{ll_tests}} lead-lag tests of usage against price, {{ll_sig}} significant after Holm |
| `make bigquery` | NEAR's BigQuery dataset against the pipeline's sources: revenue wallets {{bq_rev_near}} NEAR on both, issuance within {{bq_supply_gap}}, daily activity identical on {{bq_days}} days |
| `make anchor-check` | the hashes anchored on NEAR testnet read back with a view call and matched to the files: predictions, raw-snapshot manifest, daily bundle (`anchors: OK`; needs network) |
| `make oneclick-offline` | the 1Click figures (integrator shares, the November take, the fee-schedule test) recomputed from `data/processed/oneclick_daily.csv`, the published daily aggregates, without the partner key: `all agree` (finding F15) |
| `make swaps` | without a partner key: a message that the per-swap 1Click data is private and not committed; its aggregates in `data/processed/` are what the documents read. With `INTENTS_JWT` in `.env`: `python3 -m src.ingest.intents_explorer`, then `make swaps` |
| `make predictions` | six frozen predictions, resolved as their dates pass |
| `make dashboard-serve` | the dashboard at http://localhost:8000 |

With network access, `make refresh` fetches fresh snapshots and re-runs everything. A daily GitHub Action does this and commits `dashboard/live.json`, which the hosted dashboard loads first; `dashboard/data.json` stays the reproducible one.

## 1Click data: what you can check without a key

The 1Click results come from the NEAR Intents Explorer API, which needs a partner key. Its terms do not allow archiving or redistributing the swaps, so they are not in the repository.

| | Without a key | With a free partner key |
| --- | --- | --- |
| Integrators' share of the fee pool ({{oc_integrators_keep}}), each integrator's share of app fees and of NEAR's revenue | ✅ `make oneclick-offline` recomputes them from `data/processed/oneclick_daily.csv` (daily sums by integrator, route type, NEAR fee tier, ZEC; no swap or address) | rebuilt from the swaps |
| November: NEAR's 1Click take with and without Trust Wallet, revenue without an integrator, ZEC | ✅ same | rebuilt from the swaps |
| NEAR's fee schedule against what integrators pay | ✅ same | rebuilt from the swaps |
| Sender concentration and round trips ({{q_rt_vol}} of volume), retention across sample weeks | committed results only (`oneclick_quality.json`, `retention.csv`) | ✅ rebuilt from the swaps |

**Getting a key:** sign in at [partners.near-intents.org](https://partners.near-intents.org/home) and copy the JWT from the Partner Dashboard (the 1Click docs: [authentication](https://docs.near-intents.org/integration/distribution-channels/1click-api/authentication)). Put it in `.env` as `INTENTS_JWT=...`, then `python3 -m src.ingest.intents_explorer --since 2026-10-11T00:00:00Z --until 2026-11-11T00:00:00Z` (about 45 minutes: the API allows one request every 5 seconds) and `make swaps`.

## Judging map

| Criterion | Where to check it |
| --- | --- |
| Runs as described | `make check-clean` (CI runs it on every push: badge above); `make verify`; `data/raw/MANIFEST.json` with a test that every snapshot matches its hash |
| Evidence, not conviction | {{claims_n}} findings with explicit pass conditions (above); hypotheses and kill criteria registered before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), unchanged since its first commit); results against expectations reported as written (H4.1 rejected, the fit's out-of-sample miss, a kill criterion triggered on 1Click) |
| Technical implementation | revenue rebuilt from wallet histories ([`revenue_wallets.py`](src/analysis/revenue_wallets.py)); supply from archival-RPC headers ([`supply.py`](src/analysis/supply.py)); {{oc_swaps}} swaps from the Intents Explorer API ([`intents_explorer.py`](src/ingest/intents_explorer.py), [`swaps.py`](src/analysis/swaps.py)); robustness of the channel fit ([`confidential.py`](src/analysis/confidential.py)); joint block bootstrap with a walk-forward backtest ([`montecarlo.py`](src/analysis/montecarlo.py), [`backtest_mc.py`](src/analysis/backtest_mc.py)); governance read on-chain ([`governance.py`](src/analysis/governance.py)) |
| Design | the dashboard: a what-if simulator on the break-even identity, live kill criteria, a scenario fan chart, a "show the numbers" table under each chart and the sources listed on the page; light theme, phone widths, reduced-motion support |
| Impact | findings that change how NEAR's revenue should be read: the September jump decomposed and costed, the integrator economics of 1Click, a {{series_over_wallets}} gap inside NEAR's own revenue reporting, a public threshold ($177M/day) shown to be 3–6× too low |
| Originality | swap-level data no other thesis uses; an incentive's cost set against the revenue it bought; a model whose own failure is published; NEAR's dashboard audited against the chain |
| Sustainability | `make refresh` and a daily Action; predictions that resolve from 2026-11-15 to 2027-04-02 with a resolver; MIT licence |

## Predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv): sha256 committed next to it (checked by a test) and timestamped in Bitcoin with OpenTimestamps, confirmed in block 975,397 (`ots verify predictions/PREDICTIONS.csv.ots`), and anchored on NEAR: the same sha256 is stored in SocialDB on testnet under `near-revenue-audit.testnet/audit/predictions` (transaction {{anchor_pred_tx}}). The raw-snapshot manifest ({{anchor_snap_tx}}) and the dashboard bundle ({{anchor_daily_tx}}) are anchored the same way at each release (`node anchor/anchor.mjs`); the daily refresh also anchors its bundle when the `NEAR_TESTNET_KEY` repository secret is set. `make anchor-check` reads them back with a view call, no key needed. Two resolve before judging starts (P1, P2 on 2026-11-15), one on its second day (P3), the rest by April 2027. `make predictions` resolves those whose date has passed; results go to [`predictions/RESULTS.md`](predictions/RESULTS.md).

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

A data project: NEAR is the subject and the main source. It reads mainnet through RPC and archival RPC (total supply at chosen blocks, validators, protocol config, `intents.near` views for the fee and fee collector, the House of Stake proposal on `vote.dao`), NearBlocks (wallet histories, `intents.near` admin calls, daily chain activity), NEAR's public BigQuery dataset (a third-source check, `sql/`), the NEAR Intents Explorer API (per-swap 1Click data), and NEAR's own Dune and revenue dashboards. It also writes to NEAR, on testnet: the sha256 of the frozen predictions, of the raw-snapshot manifest and of each day's dashboard bundle go to SocialDB under `near-revenue-audit.testnet` (`anchor/anchor.mjs`, near-api-js), so anyone can check with a view call that what is published is what was anchored, and when. No mainnet transaction, no real money; the testnet key and the read-only Explorer API key stay in a git-ignored `.env`.

## Data sources and how they were obtained

- **DefiLlama API** (fees, revenue, holders revenue, volume of NEAR Intents; NEAR and BTC prices; peers), **CoinGecko** (market caps), **NEAR RPC and archival RPC**, **NearBlocks API**.
- **NEAR Intents Explorer API**: per-swap 1Click data; needs a partner key in `INTENTS_JWT` (git-ignored `.env`, never committed; a key is free at partners.near-intents.org). Its terms do not allow archiving or redistributing the swaps, so they are not committed. What is committed: `data/processed/oneclick_daily.csv`, daily sums by integrator, route type, NEAR fee tier and ZEC flag (no swap, sender or address), from which `make oneclick-offline` recomputes every 1Click figure the documents quote (finding F15); the collector (`python3 -m src.ingest.intents_explorer`) rebuilds the rest with your own key. Collected up to {{oc_to}}. The daily refresh keeps the live dashboard's 1Click figures current with the same key (a repository secret): it holds a rolling 31-day window of swaps in this repository's private GitHub Actions cache, collects only the new days, and commits only the dashboard bundle; per-swap data is never committed or published (the key holder checked this use with the provider for a non-profit project).
- **NEAR's Dune dashboard** ([dune.com/near/near-intents](https://dune.com/near/near-intents)): Dune's API needs a paid plan, so the public result tables were read page by page in a browser and saved as text in `data/raw/dune/`, with each query id in the file header.
- **NEAR's revenue dashboard** ([revenue.near.org](https://revenue.near.org/)): its series are embedded in the page; `make refresh` saves them to `data/raw/near_revenue/`.
- **NEAR's public BigQuery dataset** (`bigquery-public-data.crypto_near_mainnet_us`): four queries in [`sql/`](sql/), run by hand in the free BigQuery sandbox on 2026-11-13, results in `data/raw/bigquery/`. `make bigquery` compares them with the pipeline's sources: the NEAR sent to the three revenue wallets is the same to the last digit as the NearBlocks histories ({{bq_rev_near}} NEAR to {{bq_rev_to}}), net issuance Feb–Oct is within {{bq_supply_gap}} of the archival-RPC series, and daily transactions and signers match NearBlocks' charts on all {{bq_days}} days (finding F14). The wallet query scans about 850 GB, most of the sandbox's free monthly terabyte.

## Hackathon disclosures

- **Timeline**: first commit 2026-10-29, after the 2026-10-19 announcement (Q-001); everything here was built in the hackathon window.
- **One project**: this is the author's only submission to NEAR HACKATHON.
- **Libraries and tools** (Q-005): Python (requests, pandas, numpy, pytest, opentimestamps-client), Playwright for screenshots, vanilla HTML/SVG for the dashboard, Vercel for hosting. Code written with the help of AI assistants (Claude).
- **Not investment advice.** Independent research, not affiliated with NEAR Foundation.

## License

MIT for the code and the analysis. The snapshots in `data/raw/` are public API responses (DefiLlama, CoinGecko, NearBlocks, NEAR RPC, revenue.near.org, results of our own queries on NEAR's BigQuery dataset), kept unchanged and dated so that every number can be re-run and checked against its anchor; they remain under their providers' terms and are used here for non-commercial research, with attribution in [Data sources](#data-sources-and-how-they-were-obtained). A provider that wants its snapshots removed can open an issue; `make refresh` re-fetches them. Per-swap 1Click data is not in the repository (see above).
