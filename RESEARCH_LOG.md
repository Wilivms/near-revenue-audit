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
| H3.3 take rate stable | **Rejected, opposite direction**: captured rate doubled, mostly from the surge of confidential swaps (7–12 bps to NEAR) | entries 7, 12, 24 |
| H3.1 top-3 integrators > 50% | **Supported on 1Click**: 55% of volume, 68% of NEAR's revenue | entries 8, 11 |
| H3.2 ZEC > 20% of volume | **Not supported over 76 days** on 1Click: 18.6% (above 20% only since mid-Sep); but ~half of NEAR's 1Click revenue | entries 8, 11, 13 |
| H3.4 < 20% of senders active again at M+3 | **Supported at address level**: 3–5% (same week M+3), at most 9–19% | entry 14 |
| H4.1 confidential TVL left after the snapshot | **Rejected**: $71M at the snapshot, $155M thirty days later (Dune) | entries 15, 24 |
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

## 2026-10-31

### 22. Other angles while waiting for Dune: protocol fee, peers, market share

**Is the September jump a protocol fee change? No.** Read on-chain (`intents.near` views and every `set_fee` / `set_fee_collector` call via NearBlocks):
- the protocol fee of `intents.near` is **1 pip** (0.0001% of each trade, about 0.01 bps), unchanged since 2025-03-10 (set by `intents.sputnik-dao.near`; later `set_fee` calls by other accounts did not change the stored value: the view still returns 1);
- its collector is an implicit account (`7066024d…`, since 2025-10-03), not one of the three revenue wallets;
- the revenue wallets hold almost nothing inside `intents.near` (one token each): fees are converted and withdrawn as they arrive.
- So NEAR's revenue does not come from the protocol fee. It comes from app fees (1Click, front-ends) paid to NEAR's wallets, which is where the September change must be (entry 12 on 1Click).

**Peers: market cap / annualised holders revenue** (`src/analysis/comps.py`, `make comps`; DefiLlama holders revenue summed per parent protocol, CoinGecko market caps, 2026-10-30):

| | Multiple |
| --- | --- |
| Peers with reported holders revenue (12) | median **22x** (interquartile 6–28x); e.g. HYPE 27x, UNI 46x, JUP 36x, PUMP 5.5x |
| NEAR (NEAR Intents + chain fees burnt) | **212x** |
| Break-even for NEAR supply | 41x |

- At the peer median, NEAR Intents' current holders revenue would support about **$0.58B** of market cap, against $5.6B. About 90% of NEAR's value is priced on something other than this revenue: an L1 premium, staking, optionality on Intents' growth.
- Caveat: NEAR is a layer 1, peers are mostly applications; not all peers are comparable, and AAVE, ENA, LDO, RUNE and JTO report no holders revenue on DefiLlama, so they are left out rather than counted as zero.

**Market share among cross-chain swap venues** reporting to DefiLlama (NEAR Intents, THORChain, Chainflip, Maya): NEAR Intents went from **6%** of their combined volume in June 2025 to **45%** in October 2025 and **61–79%** in each month since May 2026. THORChain fell from 84% to 16–32%.
- This supports the "real" half of the thesis: NEAR Intents won its category on volume. It does not change the "not enough" half: volume share has not turned into enough captured revenue.
- Caveat: bridges and aggregators (Relay, Across, LI.FI, deBridge) are tracked separately by DefiLlama and are not in this denominator; several of them route through NEAR Intents.

### 23. The holder's view, revenue by asset, dashboard context section

- **Risk** (`src/analysis/token_risk.py`, `make risk`; NEAR and BTC daily prices from DefiLlama coins, Nov 2024 to Oct 2026): NEAR volatility 103% a year vs BTC 44%; max drawdown −88% (BTC −53%); 692 days under water; 95% daily CVaR 12.3% vs 5.1%; correlation 0.63 and beta 1.46 to BTC (1.29 over the last year). The rolling 90-day correlation fell from ~0.8 in early 2026 to ~0.3 in June–July, when NEAR moved on its own.
- **Dilution** (stake from the RPC `validators` call: 593M NEAR staked, 45% of supply): issuance 2.42% a year, buybacks 0.40% at the last 30 days' pace and prices, net supply growth **2.0%**. Unstaked holders lose about 2% of their share a year; stakers earn about 5.3% gross before commission.
- **Revenue by asset** (1Click, last 30 days, labelled by the volatile leg): BTC 30% of NEAR's revenue, ZEC 23%, ETH 16%, stablecoin↔stablecoin 9% (30% of volume, 1.3 bps). This labelling counts ZEC↔BTC swaps once, by origin, so ZEC's share here is lower than the "ZEC on either side" measure of entry 13.
- **Dashboard**: new "Context" section (peers on a log scale with the 41x break-even, cross-chain market share, holder tiles) and a "What NEAR earns on, by asset" chart in the distribution section.

## 2026-11-03

### 24. Confidential swaps explain the September jump, and an airdrop explains confidential swaps

Dune's free plan has no API and no trial for this account, so the data was read from the public result tables of NEAR's own dashboard ([dune.com/near/near-intents](https://dune.com/near/near-intents)), page by page in the browser, and saved as text in `data/raw/dune/` with each query id. Code: `src/analysis/confidential.py` (`make confidential`).

**What Dune shows that the Explorer API could not**
- Confidential swaps are **41% of Intents volume in October** ($1.63B of $3.99B), up from 2–4% in April–May, 13% in August and 28% in September. Their volume is included in DefiLlama's total (Dune and DefiLlama totals for October match).
- All-time fees generated (all recipients): $59.0M, of which confidential $3.09M (7.4 bps of confidential volume) and protocol fee $35k. By channel: SwapKit $42.1M, ZODL $3.2M, confidential intents $3.0M, Zashi $3.0M.

**Does it explain the take-rate jump (entries 7, 10, 12)? Mostly yes.**
- Weekly regression, no intercept, 12 complete weeks Aug 3–Oct 25: captured revenue = 0.65 bps × public + **12.2 bps × confidential** (R² 0.86). On the buyback wallet alone: 0.51 and 8.1 bps (R² 0.94). Correlation of weekly confidential volume with buyback-wallet inflows: 0.97; public volume: 0.34.
- The two regressors are correlated and the sample is short, so the split is rough. Dune's own fee table gives 7.4 bps for confidential swaps (all time, all recipients). Taken together: confidential swaps account for roughly 60% to nearly all of the rise in captured revenue since August. The 1Click repricing (entry 12) is the rest.
- This revises entry 10 ("the jump came from channels the Explorer API does not see"): the main channel is now identified.

**Why confidential swaps grew: NEAR@3.33**
- NEAR Foundation program announced 2026-06-15: users with a sustained confidential balance above $100 on near.com and at least one confidential swap earn locked milestone tokens. Drop 1: 333,333 tokens (2% cap per wallet), snapshot when confidential TVL reaches $70M, conversion 1:1 into NEAR once NEAR's 3-day VWAP is at or above $3.33. Later rounds are announced and require more activity.
- Confidential TVL (query 8644298): $70M first crossed 2026-09-11, $71.4M on 2026-09-16; NEAR closed above $3.33 three days running by 2026-09-21 (daily closes, a proxy for the VWAP rule). Drop 1 ≈ $1.39M at that price.
- **H4.1 rejected**: confidential TVL 30 days after the snapshot ($154.9M) is above its level at the snapshot ($71.4M). It peaked at $187.3M on 2026-09-27 and stood at $143.0M on 2026-10-31 (−24% from the peak).
- **Cost vs revenue**: confidential volume from 2026-06-15 to October ≈ $3.75B → $2.8M (7.4 bps) to $4.6M (12.2 bps) of revenue. Drop 1 cost 30–50% of that, in NEAR entering circulation; about 1M NEAR were captured by the revenue wallets over September–October, so Drop 1 offsets about a third of two months of buybacks.

**What it changes in the thesis**
- "Real": unchanged.
- "Durable": weaker. The fastest-growing source of NEAR's revenue is a channel whose growth is being paid for by an incentive with more rounds announced. The test is what confidential volume does once the rounds stop.
- "Bought with incentives": now measurable. Roughly a third to a half of the confidential channel's revenue so far was handed back as Drop 1.
- New kill criterion candidate, not pre-registered and therefore reported separately: confidential share of volume falling back below 15% for 30 days after the last NEAR@3.33 round.

### 25. Did the airdrop pay for itself? Roughly, and it nets out in NEAR

- **Counterfactual** (`counterfactual()` in `confidential.py`): at the May–Aug take rate (2.38 bps of all volume, when confidential swaps were 4–13% of volume), the $8.79B of Sep–Oct volume would have produced **$2.09M**; actual captured revenue was **$3.81M**. Uplift: **$1.72M** in two months.
- Drop 1 of NEAR@3.33 cost about **$1.39M** (333,333 NEAR at ~$4.16). If all of the uplift is attributed to the program, it returned about 1.2x its cost in two months, before any later round.
- **In NEAR, it nets out.** Daily, Sep 1–Oct 29: the uplift bought about **408k NEAR**; Drop 1 released **333k NEAR** into circulation. The program's net effect on circulating supply so far is about +75k NEAR retired, against 2.6M NEAR issued per month. The incentive moved revenue a lot and supply hardly at all.
- **Turnover**: daily confidential volume / confidential TVL went from 0.19 (July) to 0.39 (August), 0.46 (September) and 0.35 (October): each dollar parked in a confidential balance is swapped every 2–3 days. Consistent with activity farming for later rounds (allocation weights reward activity), though the data cannot separate farming from genuine use.
- Where the fee goes: Aurora's docs for confidential swaps say fees "behave exactly as they do today", and a user report puts a near.com confidential ETH→USDC swap at about 3x the cost of the same swap on Rabby, mostly attributed to solver spreads. Neither states the bps NEAR receives, so the 7–12 bps range stays an estimate. Question kept for the NEAR team.
- Scenario link: the Monte Carlo scenario "take back to May–Aug level" (2.63 bps) is the "incentive ends" case. It offsets a median 10% of 2027 issuance, half the base case.

## 2026-11-04

### 26. How solid is the "12 bps on confidential swaps" estimate? And what if the incentive winds down?

- **Bootstrap** (5,000 resamples of the 12 weeks): 90% interval for NEAR's take on confidential volume **10.8–14.5 bps**; on public volume −0.1 to 1.2 bps. The confidential coefficient is well identified; the public one is not (the two volumes move together, and public revenue is small).
- **Daily fit** (90 days, noisier because buyback inflows are lumpy): 10.2 bps confidential, 1.3 bps public. Same conclusion.
- Dune's own fee table gives 7.4 bps for confidential swaps over all time (all recipients). The gap with 10–14 bps can come from timing (fees accrue before they reach the wallets), from public revenue that rose at the same time and is attributed to confidential volume by the fit, or from fees on confidential swaps not recorded in that table. The range kept in the report is 7–12 bps; the fee NEAR charges is the first question for the NEAR team.
- **New Monte Carlo scenario, "incentive winds down over 6 months"**: the take rate falls linearly from 5.41 bps to its May–Aug level (2.63) over 180 days, then stays there. 2027 offset: median **11%** of issuance (p10–p90 3–47%), 3% chance of a net deflationary 2027. Close to the "take back to May–Aug" case: by 2027 most of the wind-down has happened.
- **Post-hoc kill criterion** (not pre-registered, reported separately): confidential share of volume below 15% for 30 days after the last NEAR@3.33 round. Today: 42% (week of 2026-10-19), rounds ongoing.
- **Not done**: volume by asset for all of Intents (Dune query 5175131). The page's pagination did not give a consistent read (more rows collected than the 545 the table reports), so the figure is not used.

### 27. Daily refresh: two bugs found by running it

- The first scheduled runs spent over 30 minutes re-downloading the full history of the four revenue wallets from NearBlocks, 25 rows per call, with rate-limit back-offs. The fetch is now incremental: it reads the latest snapshot, then pulls only newer rows (newest first) until it meets one it already has. A day's refresh of all wallets now takes about a minute.
- The supply cache (archival RPC) was never extended after the first run, so revenue-wallet flows from November met no supply reading and the monthly share divided by zero. The cache now adds the current final block when it is more than 3 days old, and the monthly table keeps complete months only.
- Effect on the numbers: October now ends on a real supply reading instead of an interpolation. Feb–Oct 2026: 23.9M NEAR issued, 3.53M captured (**14.8%**, was 14.7%). Holder view unchanged (issuance 2.42% a year, net supply growth 2.0%).

### 28. First answer from the NEAR team (Discord support ticket, 2026-11-04)

- Further NEAR@3.33 drops after Drop 1: "tba". No size or schedule is public, so the report keeps two cases side by side: incentives continue (base case, take rate held at 5.4 bps) and incentives wind down over 6 months (11% of 2027 issuance offset). Nothing is assumed about Drop 2.
- The fee on confidential intents and whether fefundsadmin's NEAR is ever sold: the moderator redirected these to near.com support; the question was sent there. Until an answer arrives, the report keeps the 7–12 bps range.

### 29. NEAR's own revenue dashboard: an independent check (2026-11-10)

- NEAR published [revenue.near.org](https://revenue.near.org/) in November. The page embeds its series in the HTML (no API), so `src/analysis/official.py` saves them to `data/raw/near_revenue/` and runs offline on the snapshot (`make official`; `make refresh` fetches a new one).
- **Wallets.** NEAR names the same three revenue wallets this audit found in log 2. All-time NEAR received: 4,281,557 rebuilt here vs 4,279,730 on NEAR's page (**0.04% apart**). Front-end fund 1.0004, buyback wallet 1.0006, 1Click fund exact.
- **Offset.** NEAR's page gives revenue / emissions = **16.3%** over Feb–Oct 2026 and 15.9% year to date. This audit gives 14.8%. The gap is in both terms: NEAR counts 24.2M NEAR of emissions (gross; this audit uses net issuance from total supply, 23.9M) and 3.95M NEAR of revenue (this audit: 3.53M captured, NEAR priced at the daily close). Same conclusion: about one NEAR bought back for every six issued.
- **Volume.** NEAR's daily Intents volume equals the Dune all-time query used in log 24 (ratio 0.9999 over 94 days), so it extends that series daily without a browser.
- **Confidential TVL** (daily, NEAR-reported): $139.6M on 2026-11-09, **−25% from the 2026-09-27 peak** and −13% in 30 days. Still about twice its level on the NEAR@3.33 snapshot day ($71M), so H4.1 stays rejected, but the trend has turned.

### 30. The confidential-swap fit fails its first out-of-sample week

- Dune's daily volume query was read again on 2026-11-10 (`data/raw/dune/volume_daily_5179085_after.txt`). Days up to 2026-11-02 were unchanged. From 2026-11-03, "public" volume falls to $0.3–11M a day and "confidential" rises to 86–163M, so confidential would be 89% of volume in the week of 2026-11-02.
- That label does not match the swaps. On 2026-11-09, the Explorer API shows **11,790 successful 1Click swaps worth $20.3M between 12:38 and 24:00 UTC alone**, while Dune's "public" total for the whole day is $3.45M. 1Click swaps are public intents, so the source label (`source_type` in `dune.near.dataset_near_intents_metrics`) changed meaning around 2026-11-03, most likely because 1Click flows are now routed through the confidential rail by default. The query text itself did not change.
- **Out of sample.** The weekly fit (now 13 weeks, 11.0 bps on confidential, 90% interval 9.7–13.4) predicted $0.90M of revenue for the week of 2026-11-02 on the new labels (at least $0.79M on the low end of the interval). NEAR captured **$0.36M**, 0.39× the prediction. Either the label changed, as above, or the confidential premium did not survive the move. The two cannot be told apart from public data.
- **What still holds.** The fit was estimated on weeks before the change and explains Sep–Oct well; the airdrop counterfactual (log 25) does not depend on the label. **What does not.** "Confidential share of volume" can no longer be tracked from November, so the post-hoc criterion now watches confidential TVL (NEAR-reported) instead, and the dashboard says so.
- **Take rate.** On NEAR's own volume and fee series, the week of 2026-11-02 had gross fees of 15.9 bps (unchanged) and NEAR's take **3.9 bps**, down from 5.3 in October: NEAR kept 25% of fees, against 34% in October. The buyback wallet received $260k (October weeks: $290–390k) and the front-end fund $96k ($117–178k). One week is not a trend, but it is the first sign that the September premium is fading as TVL falls.

### 31. Issuance cut approved by governance (HSP-029)

- House of Stake approved HSP-029 on 2026-11-02 ([The Block](https://www.theblock.co/news/defi/2026-11-03-near-governance-approves-proposal-to-cut-token-issuance-432378)): maximum issuance goes from 2.5% to 1.6% a year, linearly over 24 months. It still needs Security Council ratification, a 90-day grace period and a protocol upgrade adopted by validators, so no start date is set.
- **Identity.** Fully phased in, the break-even multiple rises from 41× to **64×** annual captured revenue. NEAR trades at about **208×** (219× on holders revenue). The cut narrows the gap by a third; it does not close it.
- **Monte Carlo.** Two scenarios added, with the earliest plausible start (2027-02-01): base + cut gives a median **18%** of 2027 issuance offset (base 17%), and a 6% chance of a deflationary 2027 (base 5%); wind-down + cut gives 11%. The cut matters after 2027, not in it. New test: the schedule is 1 before the start and 0.64 once phased in, and a cut can only raise the offset.
- **Refresh, 2026-11-10.** Price $3.58. 30-day take 4.97 bps. Base case 2027: median 17% (p10–p90 5–66%), 5% chance of a deflationary 2027, down from 21% and 9% in the first run, mainly because the 30-day take fell from 5.41 to 4.97 bps and 30-day volume from $135M to $124M a day. Rebuilt revenue since the fee switch: $7.90M vs $7.95M on DefiLlama (0.994).

### 32. Full review before submission (2026-11-11): what was wrong, what was too strong

A second pass over every figure and every causal claim. Corrections, in order of weight.

**The weekly fit is weaker than the report said.**
- The fit in levels (11.0 bps on confidential volume, 13 weeks) survives leave-one-week-out (10.7–12.2) and an intercept (≈ $4k, i.e. zero). But both volumes trend over the window, and a fit in levels can pick up a shared trend. On **week-to-week changes** the same fit gives **5.5 bps** on confidential volume (90% interval 2.2–9.0) and 2.9 on public (−1.2 to 5.3).
- Dune's fee table (7.4 bps, all-time) sits inside that interval. The earlier "7–12 bps against under 1 bp" becomes "about 5–11 bps against 1–3". The premium is real in every version; its size is not pinned down.
- Share of the Aug → Oct rise in the take (+3.3 bps) that the move to confidential swaps accounts for: 84% (levels), 54% (Dune's fee), 22% (changes). The report said "most of the jump"; it now says "the largest identified driver, a fifth to five sixths".
- Out of sample (week of 2026-11-02): $0.90M predicted in levels, $0.47M on changes, $0.36M actual. Still a miss in both, by 2.5× and 1.3×.

**Causality.** "An airdrop is paying for it" was stated as fact. The evidence is timing: the campaign was announced 2026-06-15, the confidential share rose from 11% to 41%, and TVL crossed the Drop 1 threshold in mid-September. There is no control group, and near.com shipped other products over the same months. The documents now say "coincides with" and "grew under", and the FAQ says the cause is not proven.

**"The two cancel" was wrong on the current data.** Sep–Oct uplift: $1.87M, about 479k NEAR at daily prices, against 333k NEAR released by Drop 1: a net 146k NEAR, 0.01% of supply. Drop 1 cost about three quarters of the uplift, not all of it. The comparison credits the whole uplift to the incentive and counts only Drop 1, so it is the favourable reading.

**NEAR's dashboard has a second revenue number, about 20% above the wallets.**
- The page's monthly revenue series (`revenueSeries`) adds up to 5.03M NEAR all-time; its own wallet breakdown, and this audit, give 4.30M. By month the ratio is 1.21 (Aug), 1.23 (Sep), 1.14 (Oct), 1.18 (Nov to date); in dollars 1.21 over Mar–Oct.
- Not explained by fees waiting to be swept: the `fee_collector` account inside `intents.near` held about $400 of tokens on 2026-11-11 (243 tokens, 170 priced with the 1Click token list).
- Because the ratio is stable, both definitions show the same trends. The offset of issuance would be 16–17% instead of 15% on NEAR's number; no conclusion changes. Where the difference sits is an open question, added to the list for NEAR.
- `make official` now reports both definitions. Wallet totals are compared up to the snapshot day (the page is live): 4.304M vs 4.298M, 0.14% apart.

**The November fall holds on three sources.** Take over 1–8 November: 3.9 bps on wallet inflows, 3.8 on DefiLlama holders revenue, and about 4.6 implied by NEAR's series (6.3 in October): a fall of about 30% each way. A trap avoided here: NEAR's month-to-date revenue runs to the day before the page was read while its volume and fee series stop one to two days earlier. Dividing one by the other gives 5.9 bps and a "7-day capture rate" of 42% on NEAR's page, both inflated by the missing days. Days must be aligned before comparing.

**NEAR's capture by mechanism** (revenue.near.org, share of gross fees): front-end fees 12% all-time → 22% last 30 days; partner revenue-sharing 5% → 11%; quote improvement 2% → 4%. The rise is broad, led by NEAR's own front-end, which fits both readings (incentivised near.com users, or near.com simply growing).

**Stale or inconsistent figures fixed.**
- Report: regression still quoted from the 12-week run (0.7 / 12 bps, 10.8–14.5); revenue check quoted from October ($7.29M, 0.999); "one fifth" next to "16 per 100"; wind-down scenarios 10% / 11% in the text vs 9% / 10% in the table; uplift $1.72M vs $1.87M; peers $0.6B vs $5.6B at an old price; staking 45% / 5.3% vs 44% / 5.5%; 692 vs 703 days under water; cross-chain share "61–79% since May" when October was 58%.
- Scenario "take doubles again (11 bps)" carried a hard-coded label while the take was 9.9 bps; the sensitivity table's first row was hard-coded at $135M/day. Both now follow the data.
- Dashboard: integrator shares were labelled "last 30 days to 2026-11-09" while the 1Click collection stops on 2026-10-29; scorecard H1.1 still showed October's totals; "the base case never reaches break-even" (it does in 5% of paths); the peers chart included JTO at 18,000× on $825 of holders revenue, which ran off the screen on a phone. Peers are now those with at least $100k of holders revenue in 30 days (12 tokens, median 20×).
- FAQ said H4.1's rejection "came out against the bull case". H4.1 was a bearish expectation (TVL would leave); its rejection favours NEAR. Fixed.
- Kill criteria were presented as what "would change our mind", but each would make the picture worse, not better. The section now says so and points to the catalysts for the other direction.

**New, flagged but not concluded.** DefiLlama shows THORChain volume above $180M a day from 2026-11-04, which puts NEAR Intents at 35% of cross-chain swap volume for November to date, against 58–79% from May to October. Eight days; it may be a reporting artefact.

**Checked and unchanged.** Wallet rebuild vs DefiLlama (0.994; every complete month within ±5%). Issuance 2.43% a year and the 41× / 64× identity. Feb–Oct offset 14.8% (NEAR: 16.3%). Monte Carlo table in section 5. H4.1 on the registered date (17 Sep: $79M → $152M thirty days later; the code uses 16 Sep, same conclusion). SwapKit 40% / 71% / 1%. Asset split. Risk metrics. Nothing new on Drop 2, on HSP-029's ratification or start date, or on Intents fees as of 2026-11-11.

### 33. Lessons from the other theses, and the track's own hypothesis (2026-11-11)

Read the 42 projects submitted to the track so far and the strongest repositories in full. Several reach this audit's two headline results on their own (revenue real; it offsets about a sixth of issuance, break-even needs several times more). What they did better, now done here:

- **No figure typed by hand.** README.md, REPORT.md and FAQ.md are now rendered from templates (`docs/templates/`) by `make docs`, with every volatile figure filled in from `data/processed/` (`src/figures.py`). The review in log 32 found about fifteen stale figures; this removes the cause.
- **Each headline finding is a check.** 13 findings, each with the number, how it is computed and an explicit pass condition; `make verify` re-renders the documents, fails if one has drifted, and fails if a finding stops holding.
- **The rebuild is checked against the committed outputs.** `make check-clean` rebuilds everything and compares each output with the committed one (text exactly, numbers to 1e-9: last-digit float noise differs between CPUs, a changed figure does not). CI runs it on every push. The bundle no longer carries a wall-clock timestamp, and the daily Action now writes `dashboard/live.json`, so `dashboard/data.json` stays reproducible. `data/raw/MANIFEST.json` lists every snapshot with its sha256, with a test.
- **Dated predictions.** Six, frozen in `predictions/PREDICTIONS.csv`, sha256 committed (test) and timestamped in Bitcoin with OpenTimestamps (an annotated git tag could not be pushed from this environment). P1 (take over 1–14 Nov below 5 bps) and P2 (confidential TVL on 14 Nov below $140M) resolve before judging.
- **HSP-029 read on-chain.** `vote.dao` proposal 29: 3,287,729 veNEAR for (99.97% of 3,288,799 cast), 36 voters, 62% of the snapshot's veNEAR; vote closed 2026-11-02 16:48 UTC, status Timelock until 2026-11-16 16:48 UTC. The proposal then foresees 90 days of grace and a validator-adopted upgrade, so the ramp starts on 2027-02-14 at the earliest; the Monte Carlo now takes that date from the chain (it assumed 2027-02-01).
- **The track's hypothesis, tested** (`make leadlag`). Is Intents volume a better signal of usage than price? Weekly, 98 complete weeks, NEAR's price net of BTC (beta 1.45). Intents volume, L1 transactions and L1 active accounts (NearBlocks charts), lags 1–4 weeks, both directions: 0 of 24 correlations significant after Holm; the strongest before correction is L1 transactions one week ahead, r = +0.15, p = 0.15. Over the last 30 days against a year earlier, Intents volume is +59% while L1 transactions are −85% and active accounts −76%. Weekly changes in captured revenue since March correlate 0.45 with Intents volume and, unexpectedly, 0.52 with L1 transactions (Intents settlement itself creates L1 transactions; not investigated further), against 0.11 with the price.

### 34. 1Click to 10 November: the late-October burst, and what held

The swap collection was extended from 2026-10-29 to 2026-11-10 (2.65M successful swaps in all; `make swaps`, new output `oneclick_november.json`).

- **The integrator picture holds.** Last 30 days (11 Oct–10 Nov): integrators keep 92% of the fee pool; SwapKit has 39% of volume and 75% of app fees and sends NEAR under 0.1% of its 1Click revenue. Users without an integrator bring 40% of NEAR's 1Click revenue on 17% of volume.
- **A one-off burst.** Trust Wallet routed $27.1M of swaps between 23 and 28 October, 99% of it ZEC, at NEAR's 20 bps fee: $54k of revenue in six days, 26% of NEAR's 1Click revenue over 16–29 October. Before and after, Trust Wallet's flow was a few tens of thousands of dollars a day.
- **November on 1Click.** NEAR's take fell from 4.6 bps (16–29 Oct) to 2.9 (1–10 Nov) while volume rose from $32M to $38M a day. Without Trust Wallet: 3.7 to 2.9. ZEC fell from 28% to 11% of volume and from 48% to 10% of NEAR's 1Click revenue. Revenue from swaps without an integrator held: $5.2k then $5.4k a day, now 49% of NEAR's 1Click revenue.
- **Reading.** Part of the fall that log 30 saw in early November is the end of one integrator's ZEC burst, not a repricing; the part NEAR controls did not fall. On all Intents the fall (5.5 → 3.9 bps) is larger than this burst can explain (it is about 3% of October's revenue), so the confidential channel easing (log 30) remains the main cause there.
- **The label check of log 30, now on full days:** 1Click alone settled $38M a day of public swaps in early November, against $0.3–11M a day of "public" volume on NEAR's Dune dataset. The dataset's label changed; the swaps did not.

### 35. The POA Bridge API closes; partner flow moves to 1Click (2026-11-12)

NEAR Intents' changelog of 2026-11-11 ([POA Bridge JSON-RPC is closing](https://docs.near-intents.org/changelog/entries/2026-11-11-poa-bridge-api)): from that day the bridge JSON-RPC (`deposit_address`, `supported_tokens`, `notify_deposit`, `recent_deposits`, `withdrawal_status` and the rest) closes, and the 1Click Swap API becomes the partner integration surface. Deposit addresses come from a 1Click quote; a standing deposit address per user is a 1Click quote with `ANY_INPUT` that returns the coin sent.

- **The pipeline is unaffected.** This audit never called the bridge RPC: revenue comes from the wallets, 1Click from the Explorer API, supply and fees from the NEAR RPC.
- **What it can change in the data.** Partner deposits that went through the bridge directly now go through 1Click quotes, where an integrator can set its own app fee. From 11 November, a rise in 1Click volume or in its share of Intents volume may be this migration, not new demand, and the integrator shares of log 34 may move for the same reason. To check on 14 November with the swap collection extended: 1Click volume and NEAR's take on it before and after 11 November, and the share of swaps with the new `1cs_v1:any` origin asset.
- **Nothing on fees.** The entry announces no change to the protocol fee, app fees or confidential intents.

### 36. Is the 1Click volume real? Sender concentration and round trips (2026-11-12)

Prompted by a newer entry in the track (Toll Road), which measures volume quality on a 1.2% sample of `intents.near` transactions. This audit has the full 1Click record, so the same question is answered on every swap of the last 30 days (`quality()` in `src/analysis/swaps.py`, output `oneclick_quality.json`): 504k successful swaps, 11 Oct–10 Nov.

- **Broad.** 85% of swaps carry a sender (hash of the first deposit address); 231k distinct senders, 78% of them swapped once. The top 10 send 19% of volume and 16% of NEAR's revenue; the top 100, 35% and 38% (HHI 86). 98 senders with 100 swaps or more (bots, market makers, integrator hot wallets) send 18% of volume and 14% of NEAR's revenue.
- **Not wash-traded.** Round trips (a sender swaps asset family A into B, then B back into A within 24 hours) are 2.7% of volume and 1.1% of NEAR's revenue; 77% of that round-trip volume goes through LI.FI, which looks like rebalancing rather than self-dealing. Toll Road's sample gives about 1% outside market makers; the two methods agree.
- **Limits.** One person can use several addresses, so concentration is a lower bound and the one-swap share an upper bound. Confidential swaps are not in the Explorer API and cannot be checked this way.
- **Correction.** `oneclick_november.json` labelled the number of swaps collected (2.65M, all periods) as the last-30-day count; the README's sentence on integrators keeping 92% of the fee pool therefore read as if it covered 2.6M swaps. It covers the last 30 days (504k swaps). Both counts are now separate (`swaps`, `swaps_collected`) and the documents say which is which. The 92% figure itself was computed on the right window and is unchanged.

### 37. Screening pass from a fresh clone (2026-11-13)

The README was followed literally in a clean clone and virtual environment, as the judges' automated screening will do. Every `make` target in the "do X → see Y" table ran. Two problems were fixed: `make swaps` crashed with a pandas traceback when the private per-swap data is absent (it now explains that the data needs a partner key and that its aggregates are committed), and the README quoted a stale output count (`29/29`, now rendered from the data). Four figures typed by hand in the templates (a 20% gap, a ~210× multiple, SwapKit's 1%) were replaced by rendered values, and the reading of the lead-lag section was reworded: on the current data L1 transactions correlate with weekly revenue as well as Intents volume does.

### 38. Public claims ledger, 5 → 26 claims (2026-11-13)

Every dated public figure found about NEAR's revenue, buybacks, issuance and usage (NEAR's revenue dashboard, Nansen's Q3 report as quoted by Altcoin Buzz, SVRN's CEO on Bankless, Bankless, Crypto Briefing, Bitwise, House of Stake), tested on the committed snapshots at the claim's own date (`public_claims()` in `src/figures.py`, REPORT section 9). 14 survive, 5 are close, 7 do not hold as stated. Usage and volume figures quoted in public are accurate (Nansen's Q3 transaction counts and confidential TVL match to the unit). The claims that fail are about value reaching holders: "$177M a day makes NEAR deflationary", "permanently remove", "more than $8M captured" (the wallets had $7.96M by 11 November; only NEAR's own, 21% higher series passes $8M), issuance "more than six times" buybacks (5.4×), and the Intents-flywheel price story (0 of 24 lead-lag tests).

### 39. NEAR's BigQuery dataset as a third source (2026-11-13)

Three queries (`sql/`) run in the free BigQuery sandbox on `bigquery-public-data.crypto_near_mainnet_us`, results in `data/raw/bigquery/`, compared by `make bigquery` (finding F14):

- NEAR transferred into the three revenue wallets since the fee switch: 3,250,386 NEAR to 10 November, identical to the NearBlocks histories to the last digit, every month.
- Total supply at each day's last block: the archival-RPC samples agree within 0.002%; net issuance Feb–Oct 23.87M NEAR against 23.86M in `supply_monthly.csv` (0.06%).
- Daily transactions and distinct signers: identical to NearBlocks' charts on all 406 days, so the lead-lag inputs are the dataset's own numbers. Transactions sent to `intents.near` went from 1.6% of all transactions in October 2025 to 8.9% in October 2026.

The wallet query scans about 850 GB because of the `args` column, most of the sandbox's free monthly terabyte; it is documented as such.

### 40. Four more public claims: NEAR's own words and fee schedule (2026-11-13)

- **Evolving NEAR Tokenomics** (near.org, 24 Feb): "already directed revenue to over 1M in $NEAR buyback" survives (1.05M NEAR, $1.73M, had reached the wallets by then). "Staked, locked, or otherwise removed from liquid circulation" is not shown: `view_account` on the three revenue wallets (new snapshot `data/raw/wallet_state/`, now fetched by `make refresh`) gives 4.29M NEAR, none staked or locked.
- **The published 1Click fee schedule** (docs.near-intents.org/resources/fees), tested on the last 30 days of swaps (`fee_policy()`, output `oneclick_fee_policy.json`): swaps without an integrator follow it (66% of cross-asset volume pays NEAR's wallets 20 bps or more; 80% of same-asset volume pays 1 bp). Swaps with an integrator do not: the "at least 20 bps to 1Click" applies to 13% of their cross-asset volume, and 74% pays NEAR nothing. The schedule's "custom agreements" are the norm, which is the integrator finding of section 3 seen from NEAR's own documentation.
- The ledger now has 30 claims; repeated sources are written out in full so each row stands alone.

### 41. Anchored on NEAR, 1Click checkable without a key, screening hardened (2026-11-13)

- **On NEAR.** The sha256 of the frozen predictions, of the raw-snapshot manifest and of the dashboard bundle are written to SocialDB on testnet under `near-revenue-audit.testnet/audit` (`anchor/anchor.mjs`); `make anchor-check` reads them back with a view call. The daily refresh anchors its bundle with a repository secret.
- **1Click without the partner key.** The Explorer API terms do not allow archiving or redistributing swaps, so a daily aggregate with no swap, sender or address is published instead (`oneclick_daily.csv`); `make oneclick-offline` recomputes the 30 quoted 1Click figures from it and matches the outputs of `make swaps` within 1.5% (finding F15).
- **Screening.** Simulated as a judge on a clean machine: the pinned pandas 3 and numpy 2.5 need Python 3.12, so `make setup` now fetches it with uv when the system Python is older, and `make check-clean` gives a clear message instead of a pip error. A ZIP download without git compared nothing; the outputs are now copied before the rebuild. Project tests went from 9 to 44.
- **Bitcoin.** The predictions' OpenTimestamps proof was upgraded: block 975,397.

### 42. The two unanswered questions, narrowed to hypotheses (2026-11-13)

NEAR's team did not answer on any of three channels (Discord support, near.com support, the NearBuilders Telegram; the support assistants pointed to the fee schedule, which has no confidential rate, and had no rule for the revenue series). `src/analysis/open_questions.py` tests what the committed data can say.

- **Confidential fee, per wallet.** The weekly fit on total revenue mixed two wallets. Split, the buyback multisig follows confidential volume almost one for one (r = 0.97, against 0.19 with public volume): 7.6 bps on confidential volume (bootstrap 7.0–8.8, leave-one-week-out 7.4–8.1, 5.3 on week-to-week changes), 0.7 on public. The front-end fund's 3.4 bps on confidential volume falls to 0.3 on week-to-week changes: a trend both share, not a fee. Hypothesis H-A: confidential swaps pay NEAR about 7.5 bps into the buyback multisig, which is where NEAR's Dune fee table puts them (7.4). It explains why the total fit (11) sat above Dune: the front-end trend.
- **Revenue-series gap, by mechanism.** revenue.near.org reports what NEAR captures as front-end fees, B2B partner fees and quote improvement, over 7 days, 30 days, year to date and all time; its revenue series equals that capture times its gross fee series (to the dollar, all time). Against the wallets over the same windows the series is 28%, 10%, 18% and 20% higher; without quote improvement, 13%, -1.6%, 4.5% and 8.3%. Quote improvement is 10-11% of reported revenue in every window. Hypothesis H-B: most of the gap is quote-improvement revenue, which NEAR counts but which does not reach the three wallets that fund buybacks; the 7-day residual is sweep timing, the all-time one the 2025 USDC period. Not explained by fees held inside `intents.near` (the three wallets hold dust there) or by the fee collector (about $400).
- Both go in REPORT section 10 with what would confirm and what would refute each.

### 43. Refresh to 12 November, and a fix to `make refresh` (2026-11-13)

- **Data to 2026-11-12.** All public sources re-fetched; every finding still holds. Revenue rebuilt from the wallets is within 0.8% of DefiLlama and 0.16% of NEAR's dashboard; market cap is 205x captured revenue against 41x for break-even; the Monte Carlo base case offsets 18% of 2027 issuance (was 17%).
- **Predictions, readings so far (not resolutions).** P1: NEAR's take is 4.1 bps from 1 to 12 November, under the 5.0 threshold. P2: confidential TVL is $137.9M on 12 November, under the $140M threshold (it was $139.6M on the 9th).
- **Open questions on the new snapshot.** The per-wallet confidential fee is unchanged (buyback multisig 7.6 bps). The gap between NEAR's revenue series and the wallets is now 6%, 9%, 18% and 20% over 7 days, 30 days, year to date and all time; quote improvement is 10–11% of the reported figure in every window. Without it, the series runs from 6% under to 8% over the wallets, so most of the gap is still explained by quote improvement, as hypothesis H-B says; over the last 7 days it over-explains it, which a short window with lumpy wallet transfers can do.
- **Fix.** `make refresh` ran the tests before re-rendering the documents, so a refresh on new data failed the documents-match-data test even though nothing was wrong. It now renders the documents first. The daily workflow uses the same target. Two dashboard figures that were typed in (the 2027 offset in the guide strip and the reconciliation figure in the ticker) are now read from the data.

### 44. An independent screening, and what it changed (2026-11-13)

An outside AI screening of the thesis track, run from a neutral prompt (same procedure and rubric for every project, random order), read this repository as a judge would. Its points, and what was done:
- *Headline numbers carry no window, so a reviewer checking today's DefiLlama finds a few percent of difference.* The README now opens with "The headline numbers, exactly": each number with its window, source and the command that rebuilds it. THESIS.md labels 205x (market cap ÷ wallet revenue, last 30 days annualised) and 208x (DefiLlama holders revenue, used only for the peer comparison).
- *The model's miss is the best credibility signal and is buried.* New README section, "Where we were wrong, and what changed": five corrections with their log entries.
- *No unit test targets the code that makes the revenue match true.* New `tests/test_core.py`: on hand-made fixtures, a receipt listed twice counts once, failed receipts and gas refunds are not revenue, internal hops between the three wallets are not revenue, other tokens are not NEAR, decimals are applied, fee basis points split between NEAR and integrators, and the 1Click offline recomputation.
- *Which dashboard bundle is the reproducible one?* The page now says which bundle it loaded (daily refresh or committed snapshot) and that `dashboard/data.json` is the one `make check-clean` rebuilds.
- *The 92% needs the partner key.* It does not: `make oneclick-offline` recomputes it from committed daily aggregates (log 41). The README's first screen now links straight to it.

### 45. November's jump in transactions to intents.near, and confidential settlement (2026-11-13)

- **Question.** Another entry reports that since late October swaps settle where public indexers cannot see them. Two things follow for this audit: does the wallet-based revenue still see NEAR's income, and what happened to on-chain activity?
- **Revenue is still visible.** Confidential Intents run in a private shard (NEAR Intents docs), but NEAR's fee still arrives as NEAR or wNEAR in its three revenue wallets on mainnet. Inflows continue every day through 12 November and the wallet total still matches NEAR's dashboard within 0.16%.
- **Activity.** In NEAR's BigQuery dataset, transactions to `intents.near` averaged 65k a day in October and 123k a day over 1–12 November. Over two 12-day windows (20–31 Oct against 1–12 Nov): +85% transactions, of which 99.9% of the increase is `intents.near` signing its own transactions (85% of all of them in November); `escrow.ai.near` is flat; transactions from all other accounts +9%, number of those accounts +5%. NEAR's captured revenue over the same days: −18%.
- **Reading.** The doubling is the contract's own execution traffic, not more users. A dashboard that counts transactions reads November as a boom while revenue fell. Query in `sql/intents_signers.sql`, aggregates only (no account saved) in `data/raw/bigquery/intents_signers_2026-11-13.csv`; `make bigquery`, tested in `tests/test_project.py`.

### 46. 1Click data to 12 November, and a window fix in the offline check (2026-11-13)

- **Data.** 1Click swaps collected from the partner API through 12 November (about 66k more swaps); `make swaps` re-run. The 30-day window is now 14 October to 12 November: 512k swaps, integrators still keep 92% of the fee pool.
- **Fix.** `make oneclick-offline` dropped only the first day of the daily file to match the 30-day window. That was right while the file and the window started together (11 October); with newer data the window starts later, and seven fee-schedule figures drifted 2–4% from the published ones. The check now keeps the same 30 days as the published window and all 30 figures agree again. The finding (F15) had failed on the new data before the fix: the check did its job.
