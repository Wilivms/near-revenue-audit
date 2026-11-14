<!-- Generated from docs/templates/README.md by `make docs`; edit the template, not this file. -->
# NEAR Revenue Audit

[![tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml/badge.svg)](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)

*Investment Thesis track (`thesis`), NEAR HACKATHON 2026. Data to 2026-11-12.*

**[Live dashboard](https://near-revenue-audit.vercel.app)** · **[One-page thesis](THESIS.md)** · **[Full report](REPORT.md)** · **[Headline numbers, exactly](#the-headline-numbers-exactly)** · **[Where we were wrong](#where-we-were-wrong-and-what-changed)** · rebuild everything: `make setup && . .venv/bin/activate && make check-clean`

[![The live dashboard: NEAR's captured revenue against issuance](docs/img/hero.jpg)](https://near-revenue-audit.vercel.app)

**Is NEAR's protocol revenue real, durable, or bought?** Since 2026-02-23, NEAR Intents fees buy back NEAR. This project rebuilds that revenue from the chain and answers what the dashboards do not: why it moved, who pays it, what the growth cost, and what it means for the token.

**The verdict, for an investor** (a thesis on public data to 2026-11-12, not personal advice). **NEAR's fee capture does not support its price today, and is unlikely to within 12 months** (7% chance of a deflationary 2027 in our base case, 26% even if volume grows 4x; probably upper bounds, as the simulation was too optimistic when backtested on 2026). Own NEAR, if at all, for staking and for the option that NEAR Intents grows several-fold at a higher take, not for the buybacks.
- **Where it stands:** market cap is 205x captured revenue; supply stops growing below 41x. Valued as a perpetuity, the buybacks justify 2.0% to 16.2% of the market cap (4.1% on the last 30 days). Justifying the price on revenue alone needs 10–41x today's revenue (mid case 24x).
- **Horizon:** 12 months, to November 2027, checked against our [dated predictions](#predictions).
- **We turn constructive if two of these hold for a quarter:** the take stays at 5 bps or more after the airdrop (it is 3.9 bps now); revenue covers half of new issuance (it is 21%); a rule replaces the choice, with bought NEAR burned or locked on-chain (today none is, and 47% of it sits in a fund whose policy one Admin vote can change: [Rule or choice](#rule-or-choice-who-controls-the-revenue)).
- **It gets worse if:** the take falls back to its May–August level (2.4 bps), rivals start to beat 1Click's quotes, or the front-end fund sells or pays out its NEAR.

## For judges: the project in 3 minutes

**1. The answer**
- **Real.** Rebuilt from NEAR's three revenue wallets, it matches DefiLlama within 0.8%, NEAR's own dashboard within 0.16% and NEAR's BigQuery dataset to the last digit.
- **Too small for the token.** Buybacks offset 14.8% of new NEAR (February 2026 to October 2026). Market cap is 205x captured revenue; supply stops growing only below 41x.
- **Partly bought.** NEAR's take doubled from 2.2 to 5.5 bps in two months, a fifth to most of it from confidential swaps during an airdrop whose first drop cost 74% of the revenue it added. It is already easing (3.9 bps in early November).
- **NEAR does not own the customer.** On 1Click, integrators keep 92% of the fee pool.
- **A policy, not a rule.** Nothing bought is burned or locked; 47% of it sits in a fund whose policy one Admin vote can change ([Rule or choice](#rule-or-choice-who-controls-the-revenue)).
- **Priced level with its rivals.** In 5 live quote rounds against Relay, Across and LI.FI, 1Click paid users the most in 52% of swaps, median +0.1 bps from the best: rivals are not undercutting NEAR Intents so far.

**Also tested, and easy to miss**
- **The track's own hypothesis (usage leads price): no.** 0 of 24 lead-lag tests significant after Holm, 0 of 24 on human-scale signers (F13).
- **The jump is dated by the data.** A break search puts it in the week ending 20 Sep 2026 (90%: 30 Aug 2026 to 27 Sep 2026), the airdrop snapshot's week.
- **"Buyback" is not what the buyback wallet gets:** 67% of DefiLlama's figure ends there; 32% sits in the front-end fund ([decomposed to the dollar](REPORT.md#1-the-revenue-is-real)).
- **The buyback wallet, to a fraction of a NEAR:** 3,393 receipts rebuild its balance to within 0.31 NEAR of what the chain reads (F19).
- **Still works when swaps go dark:** confidential swaps are invisible, but their fees land in public wallets, which is where revenue is measured.
- **A pre-registered kill criterion triggered** and is reported as written; [`HYPOTHESES.md`](HYPOTHESES.md) is unchanged since [its first commit](https://github.com/Wilivms/near-revenue-audit/commit/8468ac7).

**2. Follow $100** (2026-10-14 to 2026-11-12, $3.77B of Intents volume)

| Of every $100 swapped through NEAR Intents | |
| --- | --- |
| Paid by users in fees (all parties) | $0.159 (DefiLlama's fee rate up to 2026-11-10: its later days were still being revised) |
| Reaches NEAR's three revenue wallets | **$0.049** (buyback multisig $0.035, front-end fund $0.014) |
| New NEAR issued over the same days | **$0.238** |
| Revenue as a share of new issuance | **21%** (14.8% over February 2026 to October 2026) |

*Which coverage is which: 14.8% is February to October 2026 on the three wallets (16.3% on NEAR's own revenue series); 21% is the 30 days to 2026-11-12 at the latest price; the dashboard's live figure is the 30 days to yesterday. Snapshot figures: every number in this README is from the committed data, to 2026-11-12. The dashboard shows the same measures on the live 30 days (refreshed daily), so they can differ from these by a point; each carries its date.*

And on 1Click (28% of Intents volume over the same days, where the retail apps and their fees are), each swap records what was sent and what was delivered, so the user's whole cost can be split. Per $100 on average: **$0.59**, of which $0.43 to integrators, **$0.04 to NEAR** and $0.12 to solvers and networks (6.4% to NEAR, F18). By size:

| You swap | You give up | to integrators | to NEAR | to solvers and networks | NEAR's share |
| --- | --- | --- | --- | --- | --- |
| $10 | **$0.14** (137 bps) | $0.05 | $0.01 | $0.08 | 4% |
| $100 | **$0.64** (64 bps) | $0.42 | $0.05 | $0.17 | 8% |
| $1,000 | **$6.09** (61 bps) | $4.81 | $0.48 | $0.80 | 8% |
| $10,000 | **$54.72** (55 bps) | $42.91 | $4.24 | $7.57 | 8% |
| $100,000 | **$626** (63 bps) | $439 | $28.21 | $159 | 5% |
| $1,000,000 | **$6,430** (64 bps) | $4,274 | $104 | $2,052 | 2% |

Each row applies the measured cost of real swaps in the band from that size to three times it ($10–30, $100–300, …); the $1M row uses swaps of $300k–1M, as there were only a handful above $1M. The cost falls with size until about $3k (small swaps carry fixed network costs), is flat at 55–56 bps from $3k to $100k, then rises again above $100k as the solvers' spread widens, while NEAR's slice shrinks.

For supply to stop growing, the second bold line has to reach the third. On 1Click alone, a $100 swap pays $0.469 in fees: $0.431 to integrators, $0.038 to NEAR.

**3. See it live: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app)**
- **Top of the page:** NEAR bought back per 100 issued, recomputed in your browser from live data.
- **"What would it take?"**: drag daily volume and NEAR's take rate until supply stops growing.
- **"Verify it in your browser"** (Checks section): one click reads the hash anchored on NEAR testnet, hashes the raw files, rebuilds the revenue from the raw receipts and compares it with this audit and NEAR's own dashboard. No key, no install.
- **"Every finding is a test"**: the 19 findings, 33 public claims about NEAR, six dated predictions and their on-chain anchors, all updated daily.

**4. Re-run it** (about 2 minutes, **no key, no account, no network after setup**: the private 1Click data enters only as committed daily aggregates, so `make oneclick-offline` rebuilds every 1Click table from them)

```
git clone https://github.com/Wilivms/near-revenue-audit && cd near-revenue-audit
make setup && . .venv/bin/activate
make check-clean     # → 58/58 outputs match the committed ones, 19/19 findings hold
make verify          # → prints every finding and the headline numbers above
```

**5. What only this project brings**
- **Revenue confirmed four independent ways, and it never revises**: DefiLlama, NEAR's dashboard, NEAR's BigQuery dataset and the withdrawals from `intents.near` agree within 0.5%; 0 of 1,143 daily readings of the rebuilt revenue changed across 5 dated snapshots, while the aggregators revised their latest day of fees by up to ×185 (F16).
- **The questions the dashboards skip, answered with data**: the airdrop's role, who pays, and where the revenue now comes from: 73% of what reaches the wallets since late September is paid out of the confidential pool (about $136M), worth 8.8 bps of confidential volume against 2.0 on public ([REPORT section 10](REPORT.md#10-the-two-questions-near-did-not-answer-and-what-the-data-says)). And the user's whole cost of a swap, $10 to $1M: NEAR keeps 6.4% of it (F18).
- **What the price implies, run backwards**: at a 15% discount rate and 3% growth, NEAR's market cap needs 24x today's captured revenue, or 83% a year of growth for five years (REPORT section 4).
- **Events tested against a placebo, not narrated**: the October exploit and six other NEAR events (halving, fee switch, airdrop, HSP-029…), each compared with the same before/after split at every ordinary date of the year (F17, REPORT section 11).
- **Every printed number traced**: [`NUMBERS.md`](NUMBERS.md) lists each of the 552 values in the documents and the dashboard with the line of code that computes it; tests re-render everything and include checks that must fail (a planted false finding, a tampered output).
- **Held to account**: every finding re-run in CI and stress-tested under 49 alternative choices (the one fragile finding says so); 33 public claims tested at their own dates; six predictions timestamped on Bitcoin; [five corrections](#where-we-were-wrong-and-what-changed) dated in the research log.
- **Keeps itself current**: the dashboard refreshes every day, 1Click included, and each update is anchored on NEAR (testnet).

**Want more?** [`THESIS.md`](THESIS.md) is the one-page thesis (5 min). [`REPORT.md`](REPORT.md) is the full argument. [`FAQ.md`](FAQ.md) answers reviewers' objections. Everything below is the detail, with every number traceable to a command.

---

## The headline numbers, exactly

Each number with its window, its source and the command that rebuilds it. None of these commands needs a key or the network, and `make verify` prints all four.

| Number | What it is, exactly | Rebuild it |
| --- | --- | --- |
| **14.8%** of new NEAR offset | NEAR received by NEAR's three revenue wallets ÷ NEAR issued, February 2026 to October 2026 (whole months since the 2026-02-23 fee switch). NEAR's own dashboard gives 16.3% | `make supply official` |
| **205x** market cap ÷ captured revenue | Market cap on 2026-11-13 ($4.6B, CoinGecko) ÷ revenue the wallets received from 2026-10-14 to 2026-11-12, annualised ×365/30 ($22.6M a year). Not the 208x on DefiLlama's holders revenue, which is used only to compare with peers on one definition | `make revenue comps` |
| **41x** break-even multiple | Supply stops growing when buybacks equal issuance (2.43% of supply a year), so when market cap ÷ captured revenue falls to 1 ÷ 2.43%. At today's take that is about $639M of daily volume | `make supply montecarlo` |
| **92%** of the 1Click fee pool kept by integrators | 1Click swaps from 2026-10-14 to 2026-11-12 (partner API); fee pool = integrators' app fees + NEAR's protocol fee | `make oneclick-offline` recomputes it from the committed daily aggregates |

## Reading paths

| Time | Do | You see |
| --- | --- | --- |
| 2 min | Open the **[live dashboard](https://near-revenue-audit.vercel.app)** | the live reading (NEAR bought back per 100 issued, recomputed in your browser), then the simulator: move volume and take rate, see break-even |
| 5 min | Read **[`THESIS.md`](THESIS.md)** | the claim, evidence for and against, what would change our mind, what could not be computed, on one page |
| 2 min | Run `make setup && . .venv/bin/activate && make check-clean` | every output rebuilt from committed data and compared: `58/58 outputs match`, `19/19 findings hold` |
| 3 min | Open **[REPORT section 9](REPORT.md#9-public-claims-checked)** | 33 public claims about NEAR tested at their own dates |
| as needed | **[`REPORT.md`](REPORT.md)** (the full argument), **[`FAQ.md`](FAQ.md)** (reviewer questions), **[`RESEARCH_LOG.md`](RESEARCH_LOG.md)** (68 dated entries, dead ends and corrections), **[`HYPOTHESES.md`](HYPOTHESES.md)** (written before the tests), **[`predictions/`](predictions/)** | |

## Why this thesis is different

**Findings this thesis adds**
- **The doubling was partly bought.** NEAR's take went from 2.2 to 5.5 bps between August and October; confidential swaps under the NEAR@3.33 airdrop explain 22%–84% of the rise, and the first drop cost 74% of the revenue it added.
- **NEAR does not own the customer.** On 512k 1Click swaps from the partner API, integrators keep 92% of the fee pool; the 20 bps that NEAR's published fee schedule sets for integrator swaps is paid on a small part of their volume. November's drop came from one integrator's burst ending, while NEAR's own front-end revenue held.
- **NEAR's own revenue series runs 21% above what its three revenue wallets receive**, every month, while the wallet totals agree within 0.16%.
- **It is already easing, and the model said so by failing.** The weekly fit missed its first unseen week ($355k against $475k–$901k predicted). In early November the take fell to 3.9 bps on three sources while confidential TVL fell 26% from its peak.
- **The two questions NEAR did not answer, narrowed to testable hypotheses:** confidential swaps pay about 7.6 bps into the buyback multisig (matching NEAR's Dune fee table), and most of the 21% gap is quote-improvement revenue that never reaches the wallets that buy NEAR (without it: 4.5% this year). [REPORT section 10](REPORT.md#10-the-two-questions-near-did-not-answer-and-what-the-data-says).
- **Most of NEAR's revenue now comes out of the confidential pool.** On the public chain, the share of the NEAR reaching the buyback multisig and the front-end fund that passes through accounts funded by the confidential pool (about $136M, the size of NEAR's confidential TVL) rose from 0% in June to 70% in October (73% since late September). Per dollar of confidential volume it is worth 8.8 bps, against 2.0 bps for the rest on public volume: the confidential premium, measured from the payouts. (`make bigquery`)
- **Transaction counts mislead.** Over two 12-day windows (20–31 October, 1–12 November), transactions to `intents.near` changed +85% while NEAR's captured revenue changed -18%. NEAR's BigQuery dataset shows why: 99.9% of the increase is `intents.near` signing its own transactions; transactions from everyone else changed +9%. A dashboard that counts transactions reads November as a boom. (`make bigquery`)
- **Valuation:** valued like peers whose holders receive revenue, this revenue supports about $0.33 a NEAR, against $3.42 (daily close, 2026-11-13).

**Every number checked against independent sources**
- Revenue rebuilt from the chain matches DefiLlama within 0.8% and NEAR's own dashboard within 0.16%; NEAR's public BigQuery dataset matches the wallet histories **to the last digit** (3.292M NEAR) and issuance within 0.06%.

**Held to account in public**
- 19/19 findings with explicit pass conditions, re-checked in CI on every commit; documents rendered from the outputs, so no figure is typed by hand.
- 33 claims by NEAR, Nansen, analysts and the press tested at their own dates: 18 survive, 6 are close, 9 do not hold.
- Hypotheses and kill criteria written before the analysis; the weekly model missed its first unseen week and the report says so.
- Six dated predictions, frozen on 2026-11-11, timestamped in Bitcoin and anchored on NEAR (testnet); two resolve before judging (P1 so far: 4.1 bps, 11-01 to 11-12, threshold 5.0).

**Reproducible by anyone**
- Offline from committed snapshots, one command, no key: `make check-clean`. Works with any Python (`make setup` fetches 3.12 if needed) and on a ZIP download.
- The 1Click results, which come from a partner API, are recomputed from published daily aggregates without the key (`make oneclick-offline`, finding F15); see [1Click data](#1click-data-what-you-can-check-without-a-key).

## Where we were wrong, and what changed

Kept in the open because a thesis is only as good as its corrections. Each one is dated in [`RESEARCH_LOG.md`](RESEARCH_LOG.md).

| What we said | What the data then showed | What changed | Log |
| --- | --- | --- | --- |
| A weekly fit explains NEAR's revenue from public and confidential volume | It missed its first unseen week: $355k actual against $475k–$901k predicted | The airdrop is now "the largest identified driver" of the jump, 22%–84% of it, not "most of it" | 30, 32 |
| Confidential swaps pay NEAR about 11 bps | The 11 bps came from a trend in the front-end fund; fitted wallet by wallet, the buyback multisig gets 7.6 bps | Matches NEAR's own Dune fee table (7.4 bps) | 42 |
| The airdrop's cost cancels the revenue it added | Drop 1 cost 74% of the uplift, not all of it | Reported as a net gain, small against supply | 32 |
| The Monte Carlo engine sizes 2027 | In a walk-forward test it was too optimistic for 2026 | The 2027 figures are flagged as more likely too high than too low | 21 |
| The 92% integrator share covered 2.6M swaps | 2.6M was every swap collected at the time (2.7M now); the 30-day window holds 512k | Both counts published separately; the 92% itself was right | 36 |

## Rule or choice: who controls the revenue

A buyback can be a rule (code that buys and burns or locks, whatever happens) or a choice (people who decide each time). Multisigs and DAOs are a normal way to run a treasury; this section only measures what a NEAR holder can count on today. Read with public view calls on NEAR mainnet on 2026-11-14 at block 224,505,096 (`make control-fetch`, no key; `make control` offline), together with each wallet's full history. Facts only; every payment, with its transaction, is listed in [REPORT appendix](REPORT.md#appendix-every-payment-from-the-two-revenue-daos).

| Link | Signatures needed (read on 2026-11-14) | What the history shows |
| --- | --- | --- |
| `intents.near` (where swaps settle) | protocol fee 1 pip (0.01 bps); no full-access key | NEAR's revenue comes from the fees 1Click and front-ends set, not from the contract's own fee |
| 1Click fund (`1csfundsadmin.sputnik-dao.near`) | DAO of 4 accounts; 2 approvals to pay | forwarded 510k NEAR to the buyback multisig; 4 proposals passed with one approval, while the threshold was one. One of them returned 45,010 NEAR described as "fees accrued by mistake" to one account in April, most likely a refund to whoever paid them |
| Buyback multisig (`buybacks.multisignature.near`) | 2 of 4 keys; no full-access key | 4 requests ever; holds 2.28M NEAR; has sent out 12,025 NEAR (0.5% of what it received) |
| Front-end fund (`fefundsadmin.sputnik-dao.near`) | DAO of 5 accounts; 2 approvals to pay; the policy itself can be changed with **1 Admin vote** (used once, on 2025-11-07) | holds 2.02M NEAR; has paid $2.45M in stablecoins to three `aurora…` accounts, $2.05M of it to `auroraliqsupport.near`, $657k after the buyback programme began. These are most likely payments to an operating partner of the front-end, and part predates the buybacks; the proposals give no further detail |

**Nothing is burned and nothing is locked.** The 4.30M NEAR bought back sits in two places that can move it with two approvals; 47% of it is in the fund whose policy one Admin vote can change. None of this says anyone will sell. It says the buyback is a policy, not a mechanism, and F3's offset counts on the policy holding. A burn or a time lock would make it a rule: that is the third condition in the verdict above.

## What NEAR could do, and how to use this

**Levers, measured on the same 30 days as Follow $100** (`make deeper`; no volume response assumed, and the fee test cannot rule one out):

| If… | Coverage of issuance (now 21%) |
| --- | --- |
| NEAR's published 20 bps applied to all integrator volume on 1Click | 38% |
| take back to its October level (5.5 bps) | 23% |
| twice today's volume | 41% |
| issuance cut (HSP-029) fully phased in | 32% |
| 20 bps on 1Click integrators and the issuance cut | 59% |
| take of 5.5 bps, twice the volume and the issuance cut | 72% |

No single lever reaches 100%; the best combination here reaches 72%. Today NEAR earns 2.8 bps on 1Click integrators' volume against the 20 bps it publishes; charging it would add about $1.53M a month if no one left.

**Path to rules.** Each link in [Rule or choice](#rule-or-choice-who-controls-the-revenue) could become a rule with tools NEAR already has: the buyback multisig could send what it buys to a contract that locks it (a time lock, or a burn); the front-end fund's policy could require more than one Admin vote to change; a House of Stake proposal (the way HSP-029 cut issuance) could make the fee and its destination a protocol commitment.

- **For a holder:** staking keeps your share of the network (+3.3% a year in real terms, before commission); not staking, −2.0% a year. Buybacks today justify 4.1% of the market cap (2.0% to 16.2% across cases).
- **For NEAR's teams:** the 21% gap in the published revenue series, the fee on confidential swaps and the front-end fund's policy are the three places where a published rule would remove doubt.
- **For builders and integrators:** the cost table above is what your users pay, band by band; NEAR keeps 6.4% of it. Every number here is rebuilt by `make check-clean` with no key.

## Findings, each one a check

`make verify` rebuilds every document from the outputs and re-runs these checks; it fails if a finding no longer follows from the data or a document has drifted from it. Result on the committed data: **19/19 hold**.

| ID | Finding | Number | How it is checked | Result |
| --- | --- | --- | --- | --- |
| F1 | Reported revenue reaches NEAR's wallets | $8.09M rebuilt vs $8.15M on DefiLlama (ratio 0.992) | NEAR inflows to the 3 revenue wallets (NearBlocks) at daily prices vs DefiLlama holders revenue, since the fee switch; holds if within ±2% (`make revenue`) | PASS |
| F2 | NEAR's own dashboard agrees on the wallets | 4.346M vs 4.339M NEAR (0.16% apart) | all-time NEAR received by the same 3 wallets vs revenue.near.org's wallet table; holds if within ±1% (`make official`) | PASS |
| F3 | Buybacks offset well under a fifth of issuance | 14.8% (NEAR's dashboard: 16.3%) | NEAR captured / net issuance from archival-RPC total supply, Feb–Oct 2026; holds if both definitions are below 20% (`make supply official`) | PASS |
| F4 | Market cap is far above break-even | 205x annual captured revenue vs 41x (64x after HSP-029) | identity: supply stops growing iff market cap / annual captured revenue < 1 / issuance; holds if above the post-cut threshold (`make montecarlo`) | PASS |
| F5 | NEAR's take doubled from August to October | 2.2 → 5.5 bps of volume (1.8x to 2.5x depending on the window: make robustness) | wallet revenue / NEAR-reported Intents volume, by month; holds if October ≥ 2× August (`make official`) | PASS |
| F6 | Confidential swaps pay NEAR more than public ones, in every method | 5.5–11 bps vs 1–3 (Dune fee table 7.4) | weekly fit in levels and in first differences, Aug–Oct; holds if the confidential coefficient exceeds the public one in both (`make confidential`) | PASS |
| F7 | They explain part, not all, of the jump | 22% to 84% of the +3.3 bps | (change in confidential share) × (confidential premium) / rise in take, under three premiums; holds if the range spans below 100% (`make confidential`) | PASS |
| F8 | Drop 1 of NEAR@3.33 cost less than the revenue uplift | $1.39M vs $1.87M (74%) | 333,333 NEAR at the conversion price vs Sep–Oct revenue above the May–Aug take rate; holds if cost < uplift (`make confidential`) | PASS |
| F9 | The fit missed its first unseen week | $355k actual vs $475k–$901k predicted | week of 2026-11-02, never used in the fit; holds (as a reported failure) if actual < both predictions (`make confidential`) | PASS |
| F10 | Confidential TVL did not leave after the snapshot (H4.1 rejected) | $71M → $155M 30 days later; $138M on 2026-11-12 | Dune confidential TVL around the NEAR@3.33 snapshot, then NEAR's dashboard; holds if TVL 30 days later > at the snapshot (`make confidential official`) | PASS |
| F11 | Supply still grows through 2027 in the base case | median 18% of 2027 issuance offset (7% chance of a deflationary 2027) | Monte Carlo, 10,000 paths, joint block bootstrap of volume and price; holds if the median is below 100% with and without HSP-029 (`make montecarlo`) | PASS |
| F12 | Peers are priced on their revenue, NEAR is not | 208x vs peer median 20x (12 peers) | market cap / annualised holders revenue (DefiLlama, CoinGecko); holds if NEAR is above every peer's interquartile range (`make comps`) | PASS |
| F13 | Usage does not lead NEAR's price (the track's hypothesis) | 0 of 24 lead-lag tests significant after Holm; best r = +0.15, p = 0.15 before correction (L1 transactions, 1-week lag) | weekly changes, NEAR price net of BTC, lags 1–4 weeks, Intents volume and L1 activity, both directions; holds if none is significant at 5% after Holm (`make leadlag`) | PASS |
| F14 | NEAR's BigQuery dataset agrees with the pipeline's sources | revenue wallets 3.292M NEAR on both, max monthly gap 0 (identical to the last digit); net issuance Feb–Oct 23.87M (0.06% apart) | queries in sql/ run on NEAR's public BigQuery dataset vs NearBlocks wallet histories and archival-RPC supply; holds if every month is within 0.1% and issuance within 0.5% (`make bigquery`) | PASS |
| F15 | The 1Click results recompute without the partner key | 30 figures (integrator shares, the November take, the fee-schedule test) recomputed from the published daily aggregates, all within 1.5% | data/processed/oneclick_daily.csv (daily sums by integrator, route type, NEAR fee tier, ZEC; no swap or address) recomputed and compared with the outputs of make swaps; holds if all agree within 1.5% (`make oneclick-offline`) | PASS |
| F16 | The rebuilt revenue never revises; the aggregators' latest days do | 0 of 1,143 daily readings of the rebuilt revenue changed across 5 dated snapshots; DefiLlama's gross fees for the latest day were revised up to ×185 (2026-11-10: $1,611 → $297,452), settled after 3 days | every dated snapshot in data/raw compared day by day with the latest (same rebuild code on each wallet snapshot); holds if no complete day of the rebuilt revenue moved by 1% or more (figures that use DefiLlama's gross fees stop at its settled days) (`make revisions`) | PASS |
| F17 | The exploit cost NEAR little revenue, but large integrators pulled back | 1Click stopped for 3.7 hours on 1 Oct (08:33 to 12:16 UTC), about $2,014 of NEAR revenue; in the two weeks after, NEAR's 1Click revenue changed −13% (inside the range of 21 placebo dates) while the 25 largest integrators' volume changed −39%, below every placebo date (−18% at worst); 3 of the 10 that cut back returned by November | 1Click swap aggregates: the longest gap with no swap on 1 Oct; the median day of 3-16 Oct against 15-28 Sep, ranked against the same split at every date whose windows avoid 27 Sep-4 Oct; holds if the halt lasted under 12 hours, NEAR's 1Click revenue change lies within the placebo range and the top-25 integrators' volume change lies below it (`make incident`) | PASS |
| F18 | Users pay about 60 bps a swap on 1Click; NEAR keeps about a sixteenth of it | 59 bps of what users send is gone on delivery (2026-10-14 to 2026-11-12, 507,526 swaps): integrators 43, NEAR 3.8, solvers and networks 12 (6.4% to NEAR) | dollar value sent and delivered per 1Click swap (Explorer API), split by the fees in each record, daily sums committed; holds if NEAR's share of the user's cost is under 10% and integrators' over half (`make swap-cost`) | PASS |
| F19 | The buyback wallet's balance is explained by its receipts, to a fraction of a NEAR | 2,274,593.09 NEAR rebuilt from 3,393 receipts vs 2,274,592.78 read on-chain at block 224,358,585 (gap −0.31 NEAR) | every NEAR in minus every NEAR out of buybacks.multisignature.near since its creation (committed history), against the archival-RPC balance at the block after the last receipt; holds if within 1 NEAR (`make control`) | PASS |

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
| `make check-clean` | the tests pass, then `58/58 outputs match the committed ones` (text exactly, numbers to 1e-9) |
| `make verify` | `19/19 findings hold` and no stale document |
| `make revenue` | revenue rebuilt from the 3 revenue wallets vs DefiLlama: $8,087,549 vs $8,149,355 since the fee switch |
| `make official` | the same wallets against NEAR's own dashboard (0.16% apart), the take rate on both revenue definitions, capture by mechanism |
| `make confidential` | the weekly fit (1.0 bps public, 11.0 confidential; 5.5 on week-to-week changes), the share of the jump explained, the airdrop counterfactual, the out-of-sample week, H4.1 |
| `make supply` | Feb–Oct 2026: 23.9M NEAR issued, 3.53M captured (14.8%) |
| `make montecarlo` | 11 scenarios to end-2027; base case 18% of 2027 issuance offset; break-even at $639M/day of volume at 4.9 bps |
| `make governance` | HSP-029 read from `vote.dao`: 99.97% of veNEAR cast in favour, timelock ends 2026-11-16 |
| `make leadlag` | 24 lead-lag tests of usage against price, 0 significant after Holm |
| `make bigquery` | NEAR's BigQuery dataset against the pipeline's sources: revenue wallets 3.292M NEAR on both, issuance within 0.06%, daily activity identical on 408 days |
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
| Integrators' share of the fee pool (92%), each integrator's share of app fees and of NEAR's revenue | ✅ `make oneclick-offline` recomputes them from `data/processed/oneclick_daily.csv` (daily sums by integrator, route type, NEAR fee tier, ZEC; no swap or address) | rebuilt from the swaps |
| November: NEAR's 1Click take with and without Trust Wallet, revenue without an integrator, ZEC | ✅ same | rebuilt from the swaps |
| NEAR's fee schedule against what integrators pay | ✅ same | rebuilt from the swaps |
| Sender concentration and round trips (2.9% of volume), retention across sample weeks | committed results only (`oneclick_quality.json`, `retention.csv`) | ✅ rebuilt from the swaps |

**Getting a key:** sign in at [partners.near-intents.org](https://partners.near-intents.org/home) and copy the JWT from the Partner Dashboard (the 1Click docs: [authentication](https://docs.near-intents.org/integration/distribution-channels/1click-api/authentication)). Put it in `.env` as `INTENTS_JWT=...`, then `python3 -m src.ingest.intents_explorer --since 2026-10-11T00:00:00Z --until 2026-11-11T00:00:00Z` (about 45 minutes: the API allows one request every 5 seconds) and `make swaps`.

## Judging map

| Criterion | Where to check it |
| --- | --- |
| Runs as described | `make check-clean` (CI runs it on every push: badge above); `make verify`; `data/raw/MANIFEST.json` with a test that every snapshot matches its hash |
| Evidence, not conviction | 19 findings with explicit pass conditions (above); hypotheses and kill criteria registered before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), unchanged since its first commit); results against expectations reported as written (H4.1 rejected, the fit's out-of-sample miss, a kill criterion triggered on 1Click) |
| Technical implementation | revenue rebuilt from wallet histories ([`revenue_wallets.py`](src/analysis/revenue_wallets.py)); supply from archival-RPC headers ([`supply.py`](src/analysis/supply.py)); 2.7M swaps from the Intents Explorer API ([`intents_explorer.py`](src/ingest/intents_explorer.py), [`swaps.py`](src/analysis/swaps.py)); robustness of the channel fit ([`confidential.py`](src/analysis/confidential.py)); joint block bootstrap with a walk-forward backtest ([`montecarlo.py`](src/analysis/montecarlo.py), [`backtest_mc.py`](src/analysis/backtest_mc.py)); governance read on-chain ([`governance.py`](src/analysis/governance.py)) |
| Design | the dashboard: a what-if simulator on the break-even identity, live kill criteria, a scenario fan chart, a "show the numbers" table under each chart and the sources listed on the page; light theme, phone widths, reduced-motion support |
| Impact | findings that change how NEAR's revenue should be read: the September jump decomposed and costed, the integrator economics of 1Click, a 21% gap inside NEAR's own revenue reporting, a public threshold ($177M/day) shown to be 3–6× too low |
| Originality | swap-level data no other thesis uses; an incentive's cost set against the revenue it bought; a model whose own failure is published; NEAR's dashboard audited against the chain |
| Sustainability | `make refresh` and a daily Action; predictions that resolve from 2026-11-15 to 2027-04-02 with a resolver; MIT licence |

## Predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv): sha256 committed next to it (checked by a test) and timestamped in Bitcoin with OpenTimestamps, confirmed in block 975,397 (`ots verify predictions/PREDICTIONS.csv.ots`), and anchored on NEAR: the same sha256 is stored in SocialDB on testnet under `near-revenue-audit.testnet/audit/predictions` (transaction [AWcwWsaf…](https://testnet.nearblocks.io/txns/AWcwWsafGXGUw9zh1rZsSwirScbaWDvo2Vct6ESWBB8t)). The raw-snapshot manifest ([92akEf38…](https://testnet.nearblocks.io/txns/92akEf38ouQ4D6JpHd9LZdtxrW8fcPjsMom82kXAiMdE)) and the dashboard bundle ([ASxmSMNY…](https://testnet.nearblocks.io/txns/ASxmSMNYuZxciwdyFkFAT3KoCvbJhvg3cJB3PzDCtst9)) are anchored the same way at each release (`node anchor/anchor.mjs`); the daily refresh also anchors its bundle when the `NEAR_TESTNET_KEY` repository secret is set. `make anchor-check` reads them back with a view call, no key needed. Two resolve before judging starts (P1, P2 on 2026-11-15), one on its second day (P3), the rest by April 2027. `make predictions` resolves those whose date has passed; results go to [`predictions/RESULTS.md`](predictions/RESULTS.md).

Reading so far, on data to 2026-11-12 (not a resolution): **P1** 4.1 bps, 11-01 to 11-12 against a threshold of 5.0; **P2** 137.9M USD on 2026-11-12 against 140M; **P3** passed, in its timelock (no veto so far). The daily refresh updates these on the dashboard's Checks section.

**What was fixed before the data, and what after.** Being plain about the order is the point of pre-registering.

| Rule | Fixed on | Before or after seeing the data | Where it is checked |
| --- | --- | --- | --- |
| Hypotheses H1.1–H5.1 and what would prove each wrong | 2026-10-29 ([`HYPOTHESES.md`](HYPOTHESES.md), unchanged since) | before the analysis (after a one-day data probe, noted in the file) | REPORT, each against its hypothesis |
| Kill criteria (three tripwires) | 2026-10-29 | before | the dashboard, live; one triggered and is reported as written |
| Confidential TVL tripwire | about 2026-11-10 (log 29) | after: marked "added after the fact" | reported separately |
| Predictions P1–P6 | 2026-11-11 (Bitcoin timestamp, NEAR testnet anchor) | before each outcome | `make predictions`; results written on testnet the day they resolve |
| The verdict's rule (two of three conditions for a quarter) and what would refute "partly bought" | 2026-11-14 | after the analysis; recomputed daily from then, so it cannot be tuned to future data | `make verdict`, dashboard banner |

**What would prove our main reading wrong.** If NEAR's take holds at 5 bps or more for 60 days (about nine weeks), the "partly bought" reading is wrong and the September jump was durable repricing. Tracked weekly: the current streak is 0 week(s).

## What NEAR's own dashboard shows, and what this adds

NEAR published [revenue.near.org](https://revenue.near.org/) in November 2026, after this rebuild. It shows **how much**; this audit asks what it is worth.

| Question | revenue.near.org | This audit |
| --- | --- | --- |
| How much revenue, how many NEAR bought? | Yes | Rebuilt independently from the chain; wallets agree within 0.16%; its revenue series runs 21% above them |
| Who pays it? | No | Per integrator and per asset on 2.7M 1Click swaps, to 2026-11-12 |
| What did the growth cost? | No | Drop 1 of NEAR@3.33 cost 74% of the revenue uplift; net 146k NEAR removed |
| Will it last? | No | Pre-registered kill criteria, a fit that failed out of sample, dated predictions |
| What does it mean for the token? | Offset to date | The break-even identity (41x, 64x after HSP-029, vs 205x today), a 2027 Monte Carlo with a backtest, peers, holder risk and dilution |

## Method

| Pillar | Question | Main sources |
| --- | --- | --- |
| 1. Ledger | Does reported revenue reach NEAR's wallets, and does it stay there? | NearBlocks (3 revenue wallets), DefiLlama, revenue.near.org, DAO proposals read on-chain |
| 2. Supply | Do buybacks offset issuance? | Archival RPC total supply, revenue wallets, HSP-029 on `vote.dao` |
| 3. Quality of revenue | Who pays, through which channel, on which asset? | 2.7M 1Click swaps (NEAR Intents Explorer API), NEAR's Dune dashboard |
| 4. Incentives | How much growth is bought (NEAR@3.33)? | NEAR's Dune dashboard and revenue.near.org (confidential volume and TVL) |
| 5. Valuation | Where does it go by end-2027? | Monte Carlo (joint block bootstrap), walk-forward backtest |
| 6. Context | Peers, competitors, usage vs price, the holder's view | DefiLlama, CoinGecko, NearBlocks charts, RPC validators |

**Why these tolerances.** Each finding's pass condition is in its row above; the bands are set by measured noise, not taste:
- **F1 (±2%)**: DefiLlama values revenue at its own prices and day boundaries, so a small gap is expected (measured: 0.8%); 2% leaves room for that while a missing flow would show. REPORT section 12 re-runs it with other prices and windows.
- **F2 (±1%)**: the same wallets read by two indexers should agree up to receipts indexed at different times (measured: 0.16%).
- **F3 (20%)**: the hypothesis written on 2026-10-29 (H2.1), kept as written.
- **F19 (1 NEAR)**: the only expected difference is the gas of the wallet's own calls, which its receipt list does not itemise (measured: −0.31 NEAR).
- Every finding is also re-run under 49 alternative choices (REPORT section 12); the one that moves (F5) says so.

## NEAR integration

A data project: NEAR is the subject and the main source. It reads mainnet through RPC and archival RPC (total supply at chosen blocks, validators, protocol config, `intents.near` views for the fee and fee collector, the House of Stake proposal on `vote.dao`), NearBlocks (wallet histories, `intents.near` admin calls, daily chain activity), NEAR's public BigQuery dataset (a third-source check, `sql/`), the NEAR Intents Explorer API (per-swap 1Click data), and NEAR's own Dune and revenue dashboards. It also writes to NEAR, on testnet: the sha256 of the frozen predictions, of the raw-snapshot manifest and of each day's dashboard bundle go to SocialDB under `near-revenue-audit.testnet` (`anchor/anchor.mjs`, near-api-js), so anyone can check with a view call that what is published is what was anchored, and when. No mainnet transaction, no real money; the testnet key and the read-only Explorer API key stay in a git-ignored `.env`.

## Data sources and how they were obtained

- **DefiLlama API** (fees, revenue, holders revenue, volume of NEAR Intents; NEAR and BTC prices; peers), **CoinGecko** (market caps), **NEAR RPC and archival RPC**, **NearBlocks API**.
- **NEAR Intents Explorer API**: per-swap 1Click data; needs a partner key in `INTENTS_JWT` (git-ignored `.env`, never committed; a key is free at partners.near-intents.org). Its terms do not allow archiving or redistributing the swaps, so they are not committed. What is committed: `data/processed/oneclick_daily.csv`, daily sums by integrator, route type, NEAR fee tier and ZEC flag (no swap, sender or address), from which `make oneclick-offline` recomputes every 1Click figure the documents quote (finding F15); the collector (`python3 -m src.ingest.intents_explorer`) rebuilds the rest with your own key. Collected up to 2026-11-12. The daily refresh keeps the live dashboard's 1Click figures current with the same key (a repository secret): it holds a rolling 31-day window of swaps in this repository's private GitHub Actions cache, collects only the new days, and commits only the dashboard bundle; per-swap data is never committed or published (the key holder checked this use with the provider for a non-profit project).
- **NEAR's Dune dashboard** ([dune.com/near/near-intents](https://dune.com/near/near-intents)): Dune's API needs a paid plan, so the public result tables were read page by page in a browser and saved as text in `data/raw/dune/`, with each query id in the file header.
- **NEAR's revenue dashboard** ([revenue.near.org](https://revenue.near.org/)): its series are embedded in the page; `make refresh` saves them to `data/raw/near_revenue/`.
- **NEAR's public BigQuery dataset** (`bigquery-public-data.crypto_near_mainnet_us`): four queries in [`sql/`](sql/), run by hand in the free BigQuery sandbox on 2026-11-13, results in `data/raw/bigquery/`. `make bigquery` compares them with the pipeline's sources: the NEAR sent to the three revenue wallets is the same to the last digit as the NearBlocks histories (3.292M NEAR to 2026-11-12), net issuance Feb–Oct is within 0.06% of the archival-RPC series, and daily transactions and signers match NearBlocks' charts on all 408 days (finding F14). The wallet query scans about 850 GB, most of the sandbox's free monthly terabyte.

## Hackathon disclosures

- **Timeline**: first commit 2026-10-29, after the 2026-10-19 announcement (Q-001); everything here was built in the hackathon window.
- **One project**: this is the author's only submission to NEAR HACKATHON.
- **Libraries and tools** (Q-005). Code written with the help of AI assistants (Claude).

  | Tool | Version | Licence | Used for |
  | --- | --- | --- | --- |
  | Python | 3.13 (3.12+ works) | PSF | every analysis step |
  | requests | 2.34.2 | Apache-2.0 | fetching public data |
  | pandas | 3.1.0 | BSD-3-Clause | tables and time series |
  | numpy | 2.5.4 | BSD-3-Clause | statistics, Monte Carlo |
  | pytest | 9.2.0 | MIT | tests |
  | uv | any | Apache-2.0 / MIT | `make setup` fetches Python if missing (optional) |
  | Node.js | 22 | MIT | writing anchors only |
  | near-api-js | 4.0.4 | MIT and Apache-2.0 | signing the testnet anchors |
  | opentimestamps-client | any | LGPL-3.0 | Bitcoin timestamp of the predictions (optional, to verify) |
  | Playwright | as installed | Apache-2.0 | screenshots of the dashboard (not needed to rebuild) |

  The dashboard is vanilla HTML, CSS and SVG with no library; it is hosted on Vercel. Exact Python versions are pinned in `requirements.txt`; CI rebuilds everything on a fresh checkout at every push ([tests](https://github.com/Wilivms/near-revenue-audit/actions/workflows/tests.yml)), and `scripts/fresh_clone_check.sh` does the same on your machine.
- **Not investment advice.** Independent research, not affiliated with NEAR Foundation.
- **Code frozen at the deadline.** The tag [`hackathon-submission`](https://github.com/Wilivms/near-revenue-audit/tree/hackathon-submission) marks the last human commit before 2026-11-14 23:59 UTC. Every later commit is the daily refresh workflow (data snapshots, `live.json`, the anchors log), committed as `near-revenue-audit bot`; no code changes after the tag.

## License

MIT for the code and the analysis. The snapshots in `data/raw/` are public API responses (DefiLlama, CoinGecko, NearBlocks, NEAR RPC, revenue.near.org, results of our own queries on NEAR's BigQuery dataset), kept unchanged and dated so that every number can be re-run and checked against its anchor; they remain under their providers' terms and are used here for non-commercial research, with attribution in [Data sources](#data-sources-and-how-they-were-obtained). A provider that wants its snapshots removed can open an issue; `make refresh` re-fetches them. Per-swap 1Click data is not in the repository (see above).
