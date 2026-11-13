<!-- Generated from docs/templates/README.md by `make docs`; edit the template, not this file. -->
# NEAR Revenue Audit

[![tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml/badge.svg)](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)

*Investment Thesis track (`thesis`), NEAR HACKATHON 2026. Data to 2026-11-10.*

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. Several public dashboards, NEAR's own included, now report how much. This project asks the questions they do not answer: **why** the revenue moved, **who** pays it, **what** the growth cost, whether it **lasts**, and what that means for the token. Every number below is computed from public data by code in this repository, and every document is rendered from those outputs.

- **Live dashboard:** https://near-revenue-audit.vercel.app. Headline figures and two kill criteria are recomputed in the browser from DefiLlama and the NEAR RPC on every visit; the rest refreshes daily.
- **The thesis on one page** (claim, evidence for and against, what would change our mind, what could not be computed): [`THESIS.md`](THESIS.md). **In full:** [`REPORT.md`](REPORT.md). **Working notes, dead ends and corrections:** [`RESEARCH_LOG.md`](RESEARCH_LOG.md). **Hypotheses written before the tests:** [`HYPOTHESES.md`](HYPOTHESES.md). **Reviewer FAQ:** [`FAQ.md`](FAQ.md). **Dated predictions:** [`predictions/`](predictions/).

> **For the jury, in 60 seconds**
> - **Verdict.** NEAR's protocol revenue is real (rebuilt from the chain: within 0.9% of DefiLlama, 0.14% of NEAR's own dashboard), but buybacks offset only 14.8% of new NEAR. Market cap is 217x annual captured revenue; supply stops growing below 41x. Valued like peers whose holders receive revenue, this revenue supports about $0.33 a NEAR, against $3.58. NEAR is not yet a scarcity asset.
> - **What only this thesis shows.** NEAR's take more than doubled (from 2.2 to 5.5 bps) partly because of an airdrop: confidential swaps under NEAR@3.33 explain 22%–84% of the rise, and the first drop cost 74% of the uplift. On the 504k 1Click swaps of the last 30 days (partner API, 2.6M collected), integrators keep 92% of the fee pool, and November's drop came from one integrator's burst ending. The volume is broad, not wash-traded: round trips are 2.7% of it. NEAR's own revenue series runs 21% above what its wallets receive.
> - **Held to account.** 14/14 findings re-checked in CI on every commit; 30 public claims by NEAR, analysts and the press tested at their own dates (16 survive, 5 close, 9 do not hold: [REPORT section 9](REPORT.md#9-public-claims-checked)); hypotheses written before the data; a model that failed out of sample and says so; six predictions frozen on 2026-11-11 with a Bitcoin timestamp and their sha256 anchored on NEAR testnet (P1 so far: 3.8 bps, 11-01 to 11-09, threshold 5.0).
> - **Next:** the [live dashboard](https://near-revenue-audit.vercel.app) (try the simulator), then [`THESIS.md`](THESIS.md) on one page.

[![The live dashboard: NEAR's captured revenue against issuance](docs/img/hero.jpg)](https://near-revenue-audit.vercel.app)

## The answer

NEAR's revenue is **real**: rebuilt from the chain, it matches DefiLlama within 0.9% and NEAR's own dashboard within 0.14%. It is **too small** to support the token on supply: buybacks offset 14.8% of issuance, and market cap is 217x annual captured revenue against 41x needed for supply to stop growing (64x once the approved issuance cut is phased in). Many theses in this track reach those two results. What this one adds is the **why**:

- **The doubling was partly bought.** NEAR's take went from 2.2 to 5.5 bps of volume between August and October. The largest identified driver is confidential swaps (13% → 41% of volume), which pay NEAR 5.5–11 bps against 1–3 on public swaps and explain 22% to 84% of the rise, depending on the method. They grew under an airdrop campaign (NEAR@3.33) whose first drop cost 74% of the revenue uplift.
- **It is already easing, and the model said so by failing.** The weekly fit missed its first unseen week ($355k against $475k–$901k predicted). In early November the take fell to 3.9 bps on three sources while confidential TVL fell 25% from its peak.
- **NEAR does not own the customer.** On the 504k 1Click swaps of the last 30 days, integrators keep about 92% of the fee pool; the largest (SwapKit) takes 75% of app fees and sends NEAR under 0.1% of its revenue. In November, NEAR's 1Click take fell from 4.6 to 2.9 bps, mostly because one integrator's burst (Trust Wallet, $27M of ZEC at 20 bps in late October) stopped; NEAR's own front-end revenue held. The volume itself is broad: 231k sending addresses, 78% of them swapping once; the top 10 send 19% of volume, and round trips (A to B and back within a day by the same address) are 2.7% of volume and 1.1% of NEAR's revenue.
- **NEAR's own revenue series runs 21% above what its three revenue wallets receive**, every month (1.14–1.33×), while the wallet totals agree within 0.14%. The gap is not fees waiting to be swept; it is an open question put to NEAR.
- **Usage does not lead the price.** The track's own hypothesis: 0 of 24 lead-lag tests are significant after Holm's correction, over 98 weeks.

## Findings, each one a check

`make verify` rebuilds every document from the outputs and re-runs these checks; it fails if a finding no longer follows from the data or a document has drifted from it. Result on the committed data: **14/14 hold**.

| ID | Finding | Number | How it is checked | Result |
| --- | --- | --- | --- | --- |
| F1 | Reported revenue reaches NEAR's wallets | $7.94M rebuilt vs $8.01M on DefiLlama (ratio 0.991) | NEAR inflows to the 3 revenue wallets (NearBlocks) at daily prices vs DefiLlama holders revenue, since the fee switch; holds if within ±2% (`make revenue`) | PASS |
| F2 | NEAR's own dashboard agrees on the wallets | 4.304M vs 4.298M NEAR (0.14% apart) | all-time NEAR received by the same 3 wallets vs revenue.near.org's wallet table; holds if within ±1% (`make official`) | PASS |
| F3 | Buybacks offset well under a fifth of issuance | 14.8% (NEAR's dashboard: 16.3%) | NEAR captured / net issuance from archival-RPC total supply, Feb–Oct 2026; holds if both definitions are below 20% (`make supply official`) | PASS |
| F4 | Market cap is far above break-even | 217x annual captured revenue vs 41x (64x after HSP-029) | identity: supply stops growing iff market cap / annual captured revenue < 1 / issuance; holds if above the post-cut threshold (`make montecarlo`) | PASS |
| F5 | NEAR's take more than doubled Aug to Oct | 2.2 → 5.5 bps of volume | wallet revenue / NEAR-reported Intents volume, by month; holds if October ≥ 2× August (`make official`) | PASS |
| F6 | Confidential swaps pay NEAR more than public ones, in every method | 5.5–11 bps vs 1–3 (Dune fee table 7.4) | weekly fit in levels and in first differences, Aug–Oct; holds if the confidential coefficient exceeds the public one in both (`make confidential`) | PASS |
| F7 | They explain part, not all, of the jump | 22% to 84% of the +3.3 bps | (change in confidential share) × (confidential premium) / rise in take, under three premiums; holds if the range spans below 100% (`make confidential`) | PASS |
| F8 | Drop 1 of NEAR@3.33 cost less than the revenue uplift | $1.39M vs $1.87M (74%) | 333,333 NEAR at the conversion price vs Sep–Oct revenue above the May–Aug take rate; holds if cost < uplift (`make confidential`) | PASS |
| F9 | The fit missed its first unseen week | $355k actual vs $475k–$901k predicted | week of 2026-11-02, never used in the fit; holds (as a reported failure) if actual < both predictions (`make confidential`) | PASS |
| F10 | Confidential TVL did not leave after the snapshot (H4.1 rejected) | $71M → $155M 30 days later; $140M on 2026-11-09 | Dune confidential TVL around the NEAR@3.33 snapshot, then NEAR's dashboard; holds if TVL 30 days later > at the snapshot (`make confidential official`) | PASS |
| F11 | Supply still grows through 2027 in the base case | median 17% of 2027 issuance offset (5% chance of a deflationary 2027) | Monte Carlo, 10,000 paths, joint block bootstrap of volume and price; holds if the median is below 100% with and without HSP-029 (`make montecarlo`) | PASS |
| F12 | Peers are priced on their revenue, NEAR is not | 220x vs peer median 20x (12 peers) | market cap / annualised holders revenue (DefiLlama, CoinGecko); holds if NEAR is above every peer's interquartile range (`make comps`) | PASS |
| F13 | Usage does not lead NEAR's price (the track's hypothesis) | 0 of 24 lead-lag tests significant after Holm; best r = +0.15, p = 0.15 before correction (L1 transactions, 1-week lag) | weekly changes, NEAR price net of BTC, lags 1–4 weeks, Intents volume and L1 activity, both directions; holds if none is significant at 5% after Holm (`make leadlag`) | PASS |
| F14 | NEAR's BigQuery dataset agrees with the pipeline's sources | revenue wallets 3.250M NEAR on both, max monthly gap none; net issuance Feb–Oct 23.87M (0.06% apart) | queries in sql/ run on NEAR's public BigQuery dataset vs NearBlocks wallet histories and archival-RPC supply; holds if every month is within 0.1% and issuance within 0.5% (`make bigquery`) | PASS |

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
| `make check-clean` | the tests pass, then `36/36 outputs match the committed ones` (text exactly, numbers to 1e-9) |
| `make verify` | `14/14 findings hold` and no stale document |
| `make revenue` | revenue rebuilt from the 3 revenue wallets vs DefiLlama: $7,939,319 vs $8,008,957 since the fee switch |
| `make official` | the same wallets against NEAR's own dashboard (0.14% apart), the take rate on both revenue definitions, capture by mechanism |
| `make confidential` | the weekly fit (1.0 bps public, 11.0 confidential; 5.5 on week-to-week changes), the share of the jump explained, the airdrop counterfactual, the out-of-sample week, H4.1 |
| `make supply` | Feb–Oct 2026: 23.9M NEAR issued, 3.53M captured (14.8%) |
| `make montecarlo` | 11 scenarios to end-2027; base case 17% of 2027 issuance offset; break-even at $626M/day of volume at 5.0 bps |
| `make governance` | HSP-029 read from `vote.dao`: 99.97% of veNEAR cast in favour, timelock ends 2026-11-16 |
| `make leadlag` | 24 lead-lag tests of usage against price, 0 significant after Holm |
| `make bigquery` | NEAR's BigQuery dataset against the pipeline's sources: revenue wallets 3.250M NEAR on both, issuance within 0.06%, daily activity identical on 406 days |
| `make anchor-check` | the hashes anchored on NEAR testnet read back with a view call and matched to the files: predictions, raw-snapshot manifest, daily bundle (`anchors: OK`; needs network) |
| `make swaps` | without a partner key: a message that the per-swap 1Click data is private and not committed; its aggregates in `data/processed/` are what the documents read. With `INTENTS_JWT` in `.env`: `python3 -m src.ingest.intents_explorer`, then `make swaps` |
| `make predictions` | six frozen predictions, resolved as their dates pass |
| `make dashboard-serve` | the dashboard at http://localhost:8000 |

With network access, `make refresh` fetches fresh snapshots and re-runs everything. A daily GitHub Action does this and commits `dashboard/live.json`, which the hosted dashboard loads first; `dashboard/data.json` stays the reproducible one.

## Judging map

| Criterion | Where to check it |
| --- | --- |
| Runs as described | `make check-clean` (CI runs it on every push: badge above); `make verify`; `data/raw/MANIFEST.json` with a test that every snapshot matches its hash |
| Evidence, not conviction | 14 findings with explicit pass conditions (above); hypotheses and kill criteria registered before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), unchanged since its first commit); results against expectations reported as written (H4.1 rejected, the fit's out-of-sample miss, a kill criterion triggered on 1Click) |
| Technical implementation | revenue rebuilt from wallet histories ([`revenue_wallets.py`](src/analysis/revenue_wallets.py)); supply from archival-RPC headers ([`supply.py`](src/analysis/supply.py)); 2.6M swaps from the Intents Explorer API ([`intents_explorer.py`](src/ingest/intents_explorer.py), [`swaps.py`](src/analysis/swaps.py)); robustness of the channel fit ([`confidential.py`](src/analysis/confidential.py)); joint block bootstrap with a walk-forward backtest ([`montecarlo.py`](src/analysis/montecarlo.py), [`backtest_mc.py`](src/analysis/backtest_mc.py)); governance read on-chain ([`governance.py`](src/analysis/governance.py)) |
| Design | the dashboard: a what-if simulator on the break-even identity, live kill criteria, a scenario fan chart, a "show the numbers" table under each chart and the sources listed on the page; light theme, phone widths, reduced-motion support |
| Impact | findings that change how NEAR's revenue should be read: the September jump decomposed and costed, the integrator economics of 1Click, a 21% gap inside NEAR's own revenue reporting, a public threshold ($177M/day) shown to be 3–6× too low |
| Originality | swap-level data no other thesis uses; an incentive's cost set against the revenue it bought; a model whose own failure is published; NEAR's dashboard audited against the chain |
| Sustainability | `make refresh` and a daily Action; predictions that resolve from 2026-11-15 to 2027-04-02 with a resolver; MIT licence |

## Predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv): sha256 committed next to it (checked by a test) and timestamped in Bitcoin with OpenTimestamps, confirmed in block 975,397 (`ots verify predictions/PREDICTIONS.csv.ots`), and anchored on NEAR: the same sha256 is stored in SocialDB on testnet under `near-revenue-audit.testnet/audit/predictions` (transaction [AWcwWsaf…](https://testnet.nearblocks.io/txns/AWcwWsafGXGUw9zh1rZsSwirScbaWDvo2Vct6ESWBB8t)). The raw-snapshot manifest ([68zRaJwF…](https://testnet.nearblocks.io/txns/68zRaJwFdfCjco1UHJxyA1MRdK61sXfG56wtYLWwEf1k)) and the dashboard bundle ([ASxmSMNY…](https://testnet.nearblocks.io/txns/ASxmSMNYuZxciwdyFkFAT3KoCvbJhvg3cJB3PzDCtst9)) are anchored the same way at each release (`node anchor/anchor.mjs`); the daily refresh also anchors its bundle when the `NEAR_TESTNET_KEY` repository secret is set. `make anchor-check` reads them back with a view call, no key needed. Two resolve before judging starts (P1, P2 on 2026-11-15), one on its second day (P3), the rest by April 2027. `make predictions` resolves those whose date has passed; results go to [`predictions/RESULTS.md`](predictions/RESULTS.md).

Reading so far, on data to 2026-11-10 (not a resolution): **P1** 3.8 bps, 11-01 to 11-09 against a threshold of 5.0; **P2** 139.6M USD on 2026-11-09 against 140M; **P3** Timelock. The daily refresh updates these on the dashboard's Checks section.

## What NEAR's own dashboard shows, and what this adds

NEAR published [revenue.near.org](https://revenue.near.org/) in November 2026, after this rebuild. It shows **how much**; this audit asks what it is worth.

| Question | revenue.near.org | This audit |
| --- | --- | --- |
| How much revenue, how many NEAR bought? | Yes | Rebuilt independently from the chain; wallets agree within 0.14%; its revenue series runs 21% above them |
| Who pays it? | No | Per integrator and per asset on 2.6M 1Click swaps, to 2026-11-10 |
| What did the growth cost? | No | Drop 1 of NEAR@3.33 cost 74% of the revenue uplift; net 146k NEAR removed |
| Will it last? | No | Pre-registered kill criteria, a fit that failed out of sample, dated predictions |
| What does it mean for the token? | Offset to date | The break-even identity (41x, 64x after HSP-029, vs 217x today), a 2027 Monte Carlo with a backtest, peers, holder risk and dilution |

## Method

| Pillar | Question | Main sources |
| --- | --- | --- |
| 1. Ledger | Does reported revenue reach NEAR's wallets, and does it stay there? | NearBlocks (3 revenue wallets), DefiLlama, revenue.near.org, DAO proposals read on-chain |
| 2. Supply | Do buybacks offset issuance? | Archival RPC total supply, revenue wallets, HSP-029 on `vote.dao` |
| 3. Quality of revenue | Who pays, through which channel, on which asset? | 2.6M 1Click swaps (NEAR Intents Explorer API), NEAR's Dune dashboard |
| 4. Incentives | How much growth is bought (NEAR@3.33)? | NEAR's Dune dashboard and revenue.near.org (confidential volume and TVL) |
| 5. Valuation | Where does it go by end-2027? | Monte Carlo (joint block bootstrap), walk-forward backtest |
| 6. Context | Peers, competitors, usage vs price, the holder's view | DefiLlama, CoinGecko, NearBlocks charts, RPC validators |

## NEAR integration

A data project: NEAR is the subject and the main source. It reads mainnet through RPC and archival RPC (total supply at chosen blocks, validators, protocol config, `intents.near` views for the fee and fee collector, the House of Stake proposal on `vote.dao`), NearBlocks (wallet histories, `intents.near` admin calls, daily chain activity), NEAR's public BigQuery dataset (a third-source check, `sql/`), the NEAR Intents Explorer API (per-swap 1Click data), and NEAR's own Dune and revenue dashboards. It also writes to NEAR, on testnet: the sha256 of the frozen predictions, of the raw-snapshot manifest and of each day's dashboard bundle go to SocialDB under `near-revenue-audit.testnet` (`anchor/anchor.mjs`, near-api-js), so anyone can check with a view call that what is published is what was anchored, and when. No mainnet transaction, no real money; the testnet key and the read-only Explorer API key stay in a git-ignored `.env`.

## Data sources and how they were obtained

- **DefiLlama API** (fees, revenue, holders revenue, volume of NEAR Intents; NEAR and BTC prices; peers), **CoinGecko** (market caps), **NEAR RPC and archival RPC**, **NearBlocks API**.
- **NEAR Intents Explorer API**: per-swap 1Click data; needs a partner key in `INTENTS_JWT` (git-ignored `.env`, never committed). The raw swaps are not committed; their aggregates in `data/processed/` are. Collected up to 2026-11-10.
- **NEAR's Dune dashboard** ([dune.com/near/near-intents](https://dune.com/near/near-intents)): Dune's API needs a paid plan, so the public result tables were read page by page in a browser and saved as text in `data/raw/dune/`, with each query id in the file header.
- **NEAR's revenue dashboard** ([revenue.near.org](https://revenue.near.org/)): its series are embedded in the page; `make refresh` saves them to `data/raw/near_revenue/`.
- **NEAR's public BigQuery dataset** (`bigquery-public-data.crypto_near_mainnet_us`): three queries in [`sql/`](sql/), run by hand in the free BigQuery sandbox on 2026-11-13, results in `data/raw/bigquery/`. `make bigquery` compares them with the pipeline's sources: the NEAR sent to the three revenue wallets is the same to the last digit as the NearBlocks histories (3.250M NEAR to 2026-11-10), net issuance Feb–Oct is within 0.06% of the archival-RPC series, and daily transactions and signers match NearBlocks' charts on all 406 days (finding F14). The wallet query scans about 850 GB, most of the sandbox's free monthly terabyte.

## Hackathon disclosures

- **Timeline**: first commit 2026-10-29, after the 2026-10-19 announcement (Q-001); everything here was built in the hackathon window.
- **One project**: this is the author's only submission to NEAR HACKATHON.
- **Libraries and tools** (Q-005): Python (requests, pandas, numpy, pytest, opentimestamps-client), Playwright for screenshots, vanilla HTML/SVG for the dashboard, Vercel for hosting. Code written with the help of AI assistants (Claude).
- **Not investment advice.** Independent research, not affiliated with NEAR Foundation.

## License

MIT
