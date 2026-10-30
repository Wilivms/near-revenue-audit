# Research log

Written as the work goes, dead ends included. Figures are provisional until `REPORT.md`.
Each entry states the question, the method, the result and the next question.
Pre-registered hypotheses: [`HYPOTHESES.md`](HYPOTHESES.md) (not edited after the fact).

## Hypothesis scorecard (provisional, 2026-10-30)

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| H1.1 reported revenue reaches the revenue wallets | **Holds** once the scope is the 3 revenue wallets | rebuilt $7.280M vs DefiLlama $7.295M (entry 2) |
| H1.2 bought-back NEAR stays in the buyback wallet | **Holds** for the buyback wallet (0.6% left); 1.4% across all 3 wallets | entry 3 |
| H1.3 buybacks executed at market | **Holds** for the front-end fund's conversions (+0.04%) | entry 4 |
| H2.1 buybacks offset < 20% of issuance | **Holds**: 14.7% Feb–Oct 2026 | entry 5 |
| H2.2 public ~$177M/day threshold is right within 30% | **Rejected**: 3–4x too low | entry 6 |
| H3.3 take rate stable | **Rejected, opposite direction**: captured rate doubled; on 1Click too (2.2 → 4.6 bps) | entries 7, 12 |
| H3.1 top-3 integrators > 50% | **Supported on 1Click**: 55% of volume, 68% of NEAR's revenue | entries 8, 11 |
| H3.2 ZEC > 20% of volume | **Not supported over 76 days** on 1Click: 18.6% (above 20% only since mid-Sep); but ~half of NEAR's 1Click revenue | entries 8, 11, 13 |
| H3.4 < 20% of senders active again at M+3 | **Supported at address level**: 3–5% (same week M+3), at most 9–19% | entry 14 |
| H4.1 confidential TVL left after the snapshot | **Untestable with this source**; 1Click proxy shows no exodus of pre-snapshot arrivals | entry 15 |
| Kill criterion 2 (top integrator > 60% of fees) | **Triggered on 1Click**: SwapKit 65–73% of app fees in every 30-day window since mid-Sep; but 1% of NEAR's revenue | entry 18 |
| H5.1 NEAR stays net inflationary through end-2027 | **Holds in the base case**: buybacks offset a median ~18–21% of issuance; 9% chance 2027 is net deflationary; walk-forward shows the engine leans optimistic | entries 17, 21 |

## 2026-10-29

### 1. Can the thesis be built on data anyone can re-run?

- DefiLlama API: daily fees, revenue and holders revenue of NEAR Intents since 2025, daily volume, TVL per chain, NEAR price.
- NEAR RPC and archival RPC: total supply at any block, protocol config. On-chain `max_inflation_rate` = 1/40 = **2.5%**, `protocol_reward_rate` = 0.
- NearBlocks API: full history of any account.
- NEAR Intents Explorer API (partner key): per-swap assets, chains, USD amounts, referral, app fees, deposit type including `CONFIDENTIAL_INTENTS`. History starts March 2025.
- Known limitation: the daily NEAR price series has gaps (583 of ~728 days), filled by interpolation. To fix before the final report. **Fixed in entry 16.**

### 2. Does reported revenue actually reach the revenue wallets? (H1.1)

- First pass, buyback wallet only (`src/analysis/ledger.py`): on-chain inflows covered **76%** of DefiLlama's holders revenue. Where is the rest?
- Lead: `1csfundsadmin.sputnik-dao.near` (the 1Click fund, a Sputnik DAO) received 555,340 NEAR from `intents.near` from 2026-01-31, mostly Feb–Apr. It forwarded 510,068 NEAR to the buyback wallet (7,274 on 2026-07-14, 502,793 on 2026-09-09). This explains why direct buyback inflows only start on 2026-04-23 although the fee switch is dated 2026-02-23.
- Lead: revenue.near.org lists **three** revenue wallets: `fefundsadmin.sputnik-dao.near` (front-end fund, 47% of NEAR captured all-time), `buybacks.multisignature.near` (39%), `1csfundsadmin.sputnik-dao.near` (14%).
- DefiLlama's adapter (`dimension-adapters/fees/near-intents/index.ts`) counts as revenue every NEAR/wNEAR entering any of the 3 wallets from outside, excludes hops between them, and labels everything after 2026-02-23 "Holders Revenue — NEAR Buyback".
- Rebuilt from raw NearBlocks data with the same rule (`src/analysis/revenue_wallets.py`): **$7,280,432 vs DefiLlama $7,295,035** since 2026-02-23 (ratio 0.998, each month within ±5%).
- Result: the 24% gap was scope, not missing money. Composition of "holders revenue" since the fee switch: buyback wallet 59.9%, front-end fund 32.5%, 1Click fund 7.5%.

### 3. Is everything labelled "buyback" retired? (H1.2, extended)

- Only one of the three wallets is a buyback wallet. The two others are DAO treasuries.
- NEAR that left the revenue wallets to outside accounts since Feb 2026: **57,036 NEAR** = 1.6% of the NEAR captured over the period:
  - 45,010 NEAR from the 1Click fund to an implicit account (`fdd59b04…`) on 2026-04-22,
  - 12,000 NEAR from the buyback wallet to an implicit account (`508aa185…`) on 2026-07-10,
  - small test amounts.
  Purpose unknown. Neutral reading: could be operating costs, a refund or a correction. To ask the NEAR team.
- The front-end fund holds **1,954,738 NEAR** today: it has not spent its NEAR so far. But a DAO treasury can spend, so "bought" is not "retired".
- Consequence for the thesis: measure **buy pressure** (NEAR purchased with revenue) and **retirement** (NEAR that provably stays out of circulation) separately.
- Open questions: membership and policy of the two DAOs; stated purpose of the two outflows.

### 4. How is the front-end fund's NEAR bought, and at what price? (H1.3)

- The front-end fund receives its fees in USDC from `intents.near` (1,339 transfers, ≈$2.12M).
- From Nov 2025 to Mar 2026 it converted **2,050,900 USDC → 1,270,358 NEAR** in 10 swaps with `auroraliqsupport.near`. Since April, its NEAR arrives directly from `intents.near` (684,375 NEAR all-time).
- Execution quality, effective price vs market price at the receipt timestamp: per swap −1.8% to +0.6%, typically +0.3% to +0.6% (a dealer spread), volume-weighted **+0.04%**. USDC out to NEAR in: usually under one hour.
- Also observed: 4 × 50,000 USDC to `aurorafinance.sputnik-dao.near` (Dec 2025–Mar 2026) not converted to NEAR, and a 200,000 USDC.e round trip with `aurorasupport.near`. Purpose unknown — possibly payments to the front-end operator. To ask.
- Note: NEAR purchases with front-end revenue started in **Nov 2025**, before the official buyback program. DefiLlama files them as treasury revenue.

### 5. Do buybacks offset issuance? (H2.1)

- Issuance measured from archival-RPC total supply (weekly samples, `src/analysis/supply.py`): 2.4–2.7M NEAR per month, consistent with 2.5% a year net of burnt fees.
- NEAR captured by the 3 wallets, Feb–Oct 2026: **3.49M NEAR vs 23.70M issued = 14.7%** (monthly 7%–25%).
- NEAR captured per month stayed roughly flat (0.2–0.6M) while the NEAR price rose about 4x from February to October. More dollars of revenue have not meant more NEAR bought. **Buybacks are reflexive: the higher the price, the fewer NEAR each dollar retires.**

### 6. Where does the public "~$177M/day" deflation threshold come from? (H2.2)

- The figure, from a community DefiLlama Pro dashboard, is consistent with assuming that **100% of gross fees** buy NEAR (fees ≈ 9 bps of volume over the trailing year at the time).
- Only the captured share buys NEAR: **2.4 bps** of volume in Q2 2026, while gross fees were 14.9 bps.
- Recomputed with the captured share: **~$650M/day** at Q2 2026 prices, **~$820M/day** at last-30-day prices, against ~$130M/day of actual volume (6.2x).
- Equivalent invariant, independent of volume: NEAR is net deflationary when **market cap / annual captured revenue < 1 / inflation = 40x**. Today ≈ 240x.

### 7. Why did the captured rate double in Sep–Oct? (H3.3, open)

- Captured revenue / volume: 2.3–2.6 bps May–Aug → 3.8 bps in Sep → 5.5 bps in Oct. Gross fees stayed at 14–16 bps of volume, so NEAR's share of fees rose from ~15–20% to ~35%.
- Not a volume effect (October volume is below September).
- Candidate explanations to test with swap-level data: a fee schedule change; a mix shift towards flows where NEAR keeps more (own front-end, confidential swaps, integrators without a partner key paying the default fee); quote improvement.

### 8. First look at swap-level data: 1Click, 2026-10-15 to 2026-10-28 (preliminary)

Source: Intents Explorer API, 217,156 swaps over 14 complete days. Only 1Click swaps are visible there.

- **Coverage limit.** 1Click volume = $453M vs $1,619M total Intents volume per DefiLlama (whose volume comes from NEAR's own Dune dataset `dataset_near_intents_metrics`): **28%**. No confidential swap appears in the API. Conclusions below describe the 1Click channel, not all of Intents. Full coverage needs NEAR's Dune datasets.
- Reliability: 97.2% of swaps succeed, 2.5% are refunded, 0.2% fail.
- **Fees are much higher on 1Click than overall**: volume-weighted app fee **44.4 bps**, vs ~16 bps of gross fees across all Intents. 31% of 1Click volume pays 50–100 bps and 14% pays more than 100 bps — mostly wallets distributed through aggregators.
- **NEAR's own cut rides on partner swaps**: `buybacks.multisignature.near` is a fee recipient on 45% of 1Click volume (36% of swaps). Its exact share per swap needs the per-recipient fees now stored by collector v2.
- **Distribution is concentrated**: SwapKit referrals = 38% of 1Click volume. Named top 3 (SwapKit, LI.FI, ZODL) = **55%**; HHI ≈ 1,900 (moderately concentrated). SwapKit also powers several wallet fee recipients (Ledger, Trust, Tangem, THORSwap), so the real dependency on one distribution partner is higher than its referral share.
- **ZEC matters a lot**: ZEC on either side in 5.4% of swaps but **28% of 1Click volume**.
- **Whales drive volume**: swaps ≥ $100k are 0.33% of swaps but **37% of volume**; median swap $50.
- 102,543 distinct senders over the 14 days.
- Provisional reading of H3.1 (top-3 integrators > 50%): supported on volume; fees pending v2 data. H3.2 (ZEC > 20% of volume): supported for 1Click over these two weeks; 90-day check pending.
- Method fix: v1 data stored only the total fee per swap. Collector v2 keeps each recipient's bps; the last two weeks are being re-collected in v2.

### 9. What were the outflows, and who controls the revenue wallets? (resolved)

Read on-chain: DAO policies (`get_policy`), every DAO proposal with its description (`get_proposals`), the buyback wallet's access keys, and the recipients' histories.

- **The 45,010 NEAR from the 1Click fund**: proposal #1 (2026-04-22) is titled *"Fees accrued by mistake"* (plus a 10 NEAR test). The recipient, a fresh implicit account, forwarded everything to `bridge-mng.near` the same day.
- **The 12,000 NEAR from the buyback wallet** (2026-07-10): same pattern, a fresh implicit account that forwarded everything to `bridge-mng.near` the same day. No description (multisig), but the pattern points to the same kind of correction.
- Reading: both outflows look like corrections returned to the bridge operator, not spending.
- **Control of the buyback wallet**: multisig requiring 2 of 4 keys, no full-access key.
- **Control of the 1Click fund**: Sputnik DAO, 4 anonymous members, majority vote. It held ~503k NEAR from Feb–Apr until 2026-09-09 (about 4.5 months) before forwarding them; some duplicate proposals are still "in progress".
- **Control of the front-end fund**: Sputnik DAO run by 5 accounts whose names point to Aurora's finance team (`aurorafinance1/2/3.near`, `auroracfo.near`, `paperclip-maximizer.near`), majority vote. It paid **4 invoices of 50,000 USDC** to `aurorafinance.sputnik-dao.near` (Dec 2025–Mar 2026, proposals titled "invoice", "Payment Request"): revenue used for operating costs, not converted to NEAR. No proposal since 2026-03-27; its 1.95M NEAR have not moved.
- Implication: retirement holds in practice so far, but ~47% of the NEAR captured all-time sits in a treasury controlled by accounts that appear to belong to Aurora, with no on-chain commitment not to sell.

### 10. Why did the captured rate double in Sep–Oct? (partly answered)

- Captured revenue / volume, 14-day rolling, all Intents: ~2.2 bps mid-Aug → ~3.0 mid-Sep → ~5.4 mid-Oct. The break starts in the second half of September, around the NEAR@3.33 snapshot (2026-09-15/17).
- By wallet, in bps of total volume, Aug → Oct: buyback wallet 1.76 → 3.74; front-end fund 0.80 → 2.01. Both rose.
- **NEAR's own fee on 1Click swaps did not change**: ~4.25 bps of 1Click volume over 2026-09-26..10-29, noisy day to day, no step.
- 1Click fees to NEAR wallets ≈ $533k over that month vs ≈ $2.06M captured by the 3 wallets in October: 1Click explains about a quarter of captured revenue.
- Provisional answer: the jump came from channels the Explorer API does not see (near.com front-end, confidential swaps, partner revenue shares, quote improvement). To confirm with NEAR's Dune datasets or NEAR's answer.
- **Revised in entry 12**: the "no change on 1Click" reading was wrong. The window started on 2026-09-26, after the change. With data from 2026-08-15, NEAR's take on 1Click doubled too.

### 11. Who pays NEAR on 1Click? (value capture)

1Click swaps 2026-09-26..10-29, $1.25B volume, fees split per recipient (collector v2):
- **NEAR keeps 4.25 bps, integrators keep 41.0 bps**: on its own rails, NEAR captures about 9% of the fee pool.
- **SwapKit**: 40% of volume, 1% of NEAR's 1Click revenue (NEAR 0.13 bps; SwapKit-side recipients 80 bps).
- **ZODL and Vizor** (Zcash wallets): 0 bps to NEAR, 67 bps to the integrator.
- **No referral**: 20% of volume but **46% of NEAR's 1Click revenue** (9.8 bps).
- Trust Wallet pays NEAR 20 bps (10% of NEAR's 1Click revenue). One anonymous referral (`e1a72603…`, 0.7% of volume, 72 bps) brings 12.5%.
- Concentration of NEAR's 1Click revenue: top 3 sources 68%, HHI ≈ 2,450.
- Fee schedule observed for NEAR: 1 bp on 50% of the paid volume, 20 bps on 28%, 5 bps on 9%.
- **ZEC**: 22.5% of 1Click volume but **42% of NEAR's 1Click revenue** (7.9 bps vs 3.2 for the rest). 64% of ZEC volume (ZODL, SwapKit, Vizor) pays NEAR nothing; the rest comes mostly through users without referral and Trust Wallet.
- Implication: on 1Click, distribution partners capture most of the economics. NEAR's revenue there rests on users who arrive without an integrator, on a few direct relationships and on ZEC. That is the "who owns the customer" risk.

## 2026-10-30

Data: 2.42M successful 1Click swaps (collector v2): continuous from 2026-08-15 to 2026-10-29, plus one sample week per month (days 8–14) from February to July. Code: `src/analysis/swaps.py` (`make swaps`). Everything below is about the 1Click channel only (~28% of Intents volume, no confidential swaps).

### 12. Did NEAR's take on 1Click change around the NEAR@3.33 snapshot? (H3.3, revises entry 10)

Four weeks before the snapshot (Aug 18–Sep 14) vs four weeks after (Sep 18–Oct 15) vs the last two weeks (Oct 16–29):

| | Before | After | Last 2 weeks |
| --- | --- | --- | --- |
| 1Click volume / day | $48.6M | $44.9M | $32.2M |
| NEAR revenue / day (1Click) | $10.8k | $15.8k | $15.0k |
| NEAR's take, bps of volume | 2.23 | 3.52 | **4.64** |
| All app fees, bps | 37.0 | 47.8 | 43.4 |
| NEAR's share of the fee pool | 6.0% | 7.4% | 10.7% |
| Senders / day | 16.9k | 12.0k | 8.9k |

- **NEAR's take on 1Click doubled**, in step with the take across all Intents (entry 10: 2.2 → 5.4 bps). Volume fell by a third, NEAR's revenue rose by 40%.
- **The modal fee did not move** (1 bp on most paid swaps, 0 on 55–73% of volume). What changed is the volume paying NEAR 11–20 bps: 1.1% of volume before, 7.5% after, 14.8% in the last two weeks. That slice now brings **64%** of NEAR's 1Click revenue (9% before).
- Shift-share decomposition, before → last 2 weeks (+2.4 bps):
  - **a new flow**: Trust Wallet's ZEC swaps, routed with referral `trustwallet` at 20 bps to NEAR from October. 6% of volume, **+1.2 bps**;
  - **higher NEAR fees inside existing segments**, about +1.4 bps: swaps with no referral 3.0 → 7.0 bps (ZEC ones 10.6 → 28.7), Rango 0.6 → 4.2, the anonymous referral `e1a72603…` 22 → 72;
  - **a lost source**, about −0.7 bps: `new.intents-referral.near` (8% of volume at 7.4 bps before, almost gone after).
- Timing: the no-referral fee rose in steps from 2026-09-12 (3 → ~8 bps around the snapshot, 7–11 bps late September). It coincides with the snapshot but this data cannot say why.
- Reading: on 1Click the jump is mostly **pricing, not mix**. NEAR charges more on the flows it can (unattributed users, ZEC) and signed at least one 20-bps distribution deal. Open question for NEAR: was there a fee change for default-fee swaps in mid-September?

### 13. ZEC over a longer window (H3.2)

- ZEC share of 1Click volume: **18.6%** from 2026-08-15 to 10-29 (76 days). By week: 8–13% in late August, 17–25% from mid-September, 25–32% in the last two weeks. Sample weeks Feb–Jul: 26%, 12%, 13%, 21%, 11%, 18%.
- So H3.2 (>20% over 90 days) is **not supported** on the longer window: the 22.5% of entry 8 was a recent peak, not the norm.
- Its weight in revenue is the real exposure: ZEC is **49% of NEAR's 1Click revenue in the last two weeks** (24% before the snapshot), because ZEC swaps pay NEAR 8 bps vs 3.3 for the rest.
- Implication: NEAR's 1Click revenue rests more and more on one asset and on a few ZEC distribution channels (Trust Wallet, users without referral).

### 14. Do 1Click senders come back? (H3.4)

Cohort = senders active on days 8–14 of month M (Feb–Jul; M+3 for Jun–Jul falls in Sep–Oct). Sender = first deposit address, hashed: someone coming back from another address or chain counts as new, so these are **lower bounds** on user retention.

| Cohort (M) | Senders | Same week, M+1 | Same week, M+3 | Any time Aug 15–Oct 29 |
| --- | --- | --- | --- | --- |
| Feb | 43.9k | 8.0% | 4.8% | 8.9% |
| Mar | 53.0k | 8.5% | 3.9% | 8.5% |
| Apr | 72.7k | 7.5% | 3.6% | 10.2% |
| May | 64.5k | 6.9% | – | 12.0% |
| Jun | 61.2k | 7.7% | 2.6% | 14.8% |
| Jul | 64.8k | – | 2.7% | 18.6% |

- Even the loosest measure (active at any time over 2.5 months, 1–6 months later) stays at 9–19%; the July cohort, closest to the window, is the highest. H3.4 (< 20% at M+3) is **supported at address level**.
- Volume is less fragile than senders: one sender in ten coming back still carries a large share of volume, because whales drive volume (swaps ≥ $100k ≈ 31–38% of volume, median swap $40–60).
- Reading: 1Click users are mostly transient. Volume depends on integrators bringing new users, which ties back to the "who owns the customer" risk (entry 11).

### 15. Did users who arrived just before the snapshot leave? (H4.1, 1Click proxy)

- H4.1 is about confidential TVL, which the Explorer API does not show. **It stays untestable** without NEAR's Dune data.
- Proxy on 1Click, symmetric design: cohorts = senders active over 14 days and not seen in the 17 days before; follow-up = 14 days, starting 14 days after the cohort ends.

| Cohort | New senders / day | Senders retained | Volume retained |
| --- | --- | --- | --- |
| Arrived Sep 1–14 (just before the snapshot) | 10.1k | 4.3% | 9.1% |
| Arrived Sep 18–Oct 1 (placebo) | 9.5k | 4.9% | 5.4% |

- No sign that pre-snapshot arrivals left faster than later ones on 1Click.
- But daily senders fell from ~17–19k (late Aug–early Sep) to ~9k (late Oct). Most of the drop is Rango: from ~11k swaps a day in early September to ~2k by mid-September, with larger swaps afterwards. That looks like the end of a burst of small swaps, possibly farming, through one integrator. The cause is not visible in this data.
- Next: confidential TVL before and after the snapshot needs NEAR's Dune datasets (`dune.near.dataset_near_intents_metrics`) or numbers from the NEAR team.

### 16. Fixing the price series (method)

- The 146 missing days were a bucketing bug, not missing data: DefiLlama returns points a few seconds either side of midnight (e.g. 23:59:59), and flooring to the day put two points on one day and left the next one empty.
- Fix: round to the nearest UTC day (`sources.py`, `ledger.py`). Now 729 daily prices, **0 gaps**, no interpolation needed.
- Effect on the reconciliation: rebuilt revenue $7,287,030 vs DefiLlama $7,295,035 (ratio 0.999, was 0.998). Nothing else moves materially, but the Monte Carlo needs real daily returns, not interpolated ones, to get volatility right.

### 17. Does NEAR become net deflationary before end-2027? (H5.1)

Code: `src/analysis/montecarlo.py` (`make montecarlo`), tests in `tests/`.

- **Model.** 10,000 paths, 2026-11-01 to 2027-12-31. Daily changes of Intents volume (7-day mean) and NEAR price are drawn **together** in 30-day blocks from history, so volatility, autocorrelation and the volume–price link are kept. NEAR captured = volume × take rate / price. Issuance = measured net rate **2.42%/yr** of supply (archival RPC). Price drift is removed by default: this is not a price forecast.
- **Start point.** Volume $135M/day (last 30 days), NEAR $4.67, take rate **5.41 bps** (last 30 days; 2.63 bps in May–Aug).
- **Identity behind it.** Deflation needs market cap / annual captured revenue < **41x**. Today: ~$6.1B / ~$27M ≈ **230x**.

| Scenario | Take | Median share of 2027 issuance offset (p10–p90) | P(2027 net deflationary) | First deflationary month, median path |
| --- | --- | --- | --- | --- |
| **Base**: 365-day history | 5.41 | **21%** (6–90%) | **9%** | never |
| Take back to May–Aug level | 2.63 | 10% (3–44%) | 3% | never |
| Zero volume drift | 5.41 | 13% (4–54%) | 4% | never |
| Price keeps its 365-day drift | 5.41 | 13% (4–54%) | 4% | never |
| Only the buyback wallet counts as retired | 5.41 × 0.6 | 12% (3–54%) | 4% | never |
| Take doubles again | 10.8 | 41% (11–181%) | 21% | never |
| 180-day history (volume ~10x by Dec 2027) | 5.41 | 92% (21–422%) | 47% | Sep 2027 |
| Full history since Mar 2025 (hyper-growth) | 5.41 | 300% (34–3,989%) | 73% | May 2027 |

- **H5.1 holds** in the base case: the median path never turns deflationary; buybacks offset about a fifth of issuance, and this share barely moves over the horizon (18% each month), because volume and price tend to move together.
- What breaks it: only scenarios where volume grows several times over **without** the price following. Two-way table at today's price (`montecarlo_sensitivity.csv`): deflation needs about **$750M/day at 5.4 bps**, $500M/day at 8 bps or $250M/day at 15 bps. Current volume is $135M/day.
- Reading: the "buyback makes NEAR deflationary" narrative needs a 5x jump in volume at today's take rate, or a mix of higher volume and higher take. The take rate is now the main lever, and entry 12 shows it is set by NEAR's pricing towards integrators, which faces competition.
- Limits: the bootstrap can only replay the past (the 180-day window contains the September spike); the take rate is fixed per path; the front-end fund's NEAR is counted as retired in the base case although nothing commits it (entry 9).

### 18. Kill criterion 2 is triggered on 1Click, and it was badly specified

- Pre-registered: "the thesis is invalidated if the top integrator's share stays above 60% of fees for 30 consecutive days".
- On 1Click, **SwapKit holds 65–73% of all app fees in every 30-day window from 2026-09-13 to 2026-10-28**, and 60–81% in each Feb–Jul sample week. As written, the criterion is triggered on this channel, and has been all year.
- But SwapKit brings **1.3%** of NEAR's own 1Click revenue (entry 11). The criterion did not say whose fees: the integrators' fee pool or NEAR's revenue. Measured on NEAR's revenue, the top source is users without an integrator (46%), and the top integrator (the anonymous referral `e1a72603…`) is at 12%.
- We do not re-word a pre-registered criterion after seeing the data. It is reported as **triggered on 1Click**, with this caveat, and it stays open for all of Intents (Dune).
- What it does say: NEAR does not own the customer on 1Click. The integrator that controls 40% of volume and 71% of fees pays NEAR almost nothing. If SwapKit routed elsewhere, NEAR would lose volume, not revenue. If SwapKit started paying NEAR, revenue would jump.
- Lesson for the method: write kill criteria against the quantity the thesis depends on (NEAR's captured revenue), not a proxy.

### 19. Live dashboard

`dashboard/index.html` (`make dashboard-serve`). Every visit:
- fetches DefiLlama (revenue, holders revenue and volume of NEAR Intents), DefiLlama coins (NEAR price) and the NEAR RPC (total supply);
- recomputes the headline ("for every 100 NEAR issued, revenue buys back X") and kill criteria 1 and 3;
- shows the committed outputs: monthly buybacks vs issuance, take rate (all Intents and 1Click), who owns the customer, Monte Carlo fan chart, scenarios, sensitivity table and the hypothesis scorecard;
- falls back to the repository snapshot if live sources are unreachable, and says so.
- First live reading (2026-10-30): **19 NEAR bought back per 100 issued** (last 30 days, at today's price), take rate 5.6 bps, market cap / annual captured revenue **213x** vs 41x break-even.

### 20. Dashboard v2: interactive

- **Simulator** ("What would it take?"): daily volume, take rate, NEAR price and "buyback wallet only" inputs, starting from today's live values; returns NEAR bought back per 100 issued, market cap / revenue and break-even volume from the identity of entry 6. Presets: today, take back to May–Aug, volume ×5, break-even volume. At today's take and price, break-even needs about 5x today's volume.
- **Monte Carlo explorer**: every scenario's monthly quantiles are now exported (`montecarlo_paths_all.csv`); the fan chart morphs between them.
- **Re-sortable distribution chart** (by app fees, NEAR's revenue or volume), buybacks chart switchable to the buyback wallet only, snapshot marker on both take-rate charts, row/column tracing on the sensitivity table.
- Motion kept to state changes and first reveals (Emil Kowalski's animation rules: transform/opacity only, strong ease-out, under 300 ms for UI, reduced-motion fallbacks). Palette re-validated for colour-blind separation in both themes.

### 21. Would the Monte Carlo have been right in the past? (walk-forward check)

Method borrowed from walk-forward validation in trading research ([quants.md](https://quants.md), QuantJourney backtester, Apache-2.0: anchored/rolling walk-forward, "a single good out-of-sample result is not proof"). Code: `src/analysis/backtest_mc.py` (`make backtest`), test in `tests/`.

- At each origin (weekly, Jul 2025 to Sep 2026), the joint block bootstrap is calibrated **only on data before the origin**, simulates 30 or 90 days ahead, and we record where the realised outcome fell (PIT). Target: buyback capacity = 7-day volume / NEAR price, the quantity that sets NEAR bought per dollar of take.
- Calibrated forecasts put about 80% of outcomes inside the 10th–90th band, with a mean PIT near 0.5.

Origins in 2026, 90-day horizon:

| Calibration window | Price drift | Inside 10–90 band | Below 10th pct | Mean PIT | Realised vs median |
| --- | --- | --- | --- | --- | --- |
| Rolling 365 days (base case) | removed | 67% | 33% | 0.18 | −67% (log −1.12) |
| Rolling 180 days | removed | 80% | 20% | 0.39 | −22% (log −0.25) |
| Expanding | removed | 67% | 33% | 0.15 | −72% |

- **The engine was biased upwards.** Realised buyback capacity fell below the simulated median far more often than half the time, and never above the 90th percentile at 90 days. With a 365-day window, 2026 forecasts still carried the 2025 hyper-growth in volume.
- Why: over the last 180 days, volume grew about 4x annualised but the NEAR price grew faster, so capacity (volume / price) fell about 60% annualised. The base case removes price drift; in the recent regime, that is generous to buybacks.
- **Consequence for H5.1**: the base-case "about 21% of 2027 issuance offset" is, on this evidence, more likely too high than too low. The conclusion that NEAR stays net inflationary through 2027 is conservative.
- Caveats: forecasts from origins less than 90 days apart overlap, so there are only about 4–5 independent 90-day checks in 2026; the 365-day window that misbehaved in early 2026 no longer contains the 2025 hyper-growth today.
- Also applied the same source's review checklist to our code: signals and calibration use only past data (trailing 7-day mean, no centred windows); no missing day is turned into a zero change since the price-series fix (entry 16); costs are not relevant here.
