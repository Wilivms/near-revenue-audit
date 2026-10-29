# Research log

Written as the work goes, dead ends included. Figures are provisional until `REPORT.md`.
Each entry states the question, the method, the result and the next question.
Pre-registered hypotheses: [`HYPOTHESES.md`](HYPOTHESES.md) (not edited after the fact).

## Hypothesis scorecard (provisional, 2026-10-29)

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| H1.1 reported revenue reaches the revenue wallets | **Holds** once the scope is the 3 revenue wallets | rebuilt $7.280M vs DefiLlama $7.295M (entry 2) |
| H1.2 bought-back NEAR stays in the buyback wallet | **Holds** for the buyback wallet (0.6% left); 1.4% across all 3 wallets | entry 3 |
| H1.3 buybacks executed at market | **Holds** for the front-end fund's conversions (+0.04%) | entry 4 |
| H2.1 buybacks offset < 20% of issuance | **Holds**: 14.7% Feb–Oct 2026 | entry 5 |
| H2.2 public ~$177M/day threshold is right within 30% | **Rejected**: 3–4x too low | entry 6 |
| H3.3 take rate stable | **Rejected, opposite direction**: captured rate doubled | entry 7 |
| H3.1 top-3 integrators > 50% | **Supported on 1Click**: 55% of volume, 68% of NEAR's revenue | entries 8, 11 |
| H3.2 ZEC > 20% of volume | **Supported on 1Click**: 22.5% of volume, 42% of NEAR's revenue (1 month); 90-day check pending | entries 8, 11 |
| H3.4, H4.1, H5.1 | Pending (H4.1 needs a source that sees confidential swaps) | collection in progress |

## 2026-10-29

### 1. Can the thesis be built on data anyone can re-run?

- DefiLlama API: daily fees, revenue and holders revenue of NEAR Intents since 2025, daily volume, TVL per chain, NEAR price.
- NEAR RPC and archival RPC: total supply at any block, protocol config. On-chain `max_inflation_rate` = 1/40 = **2.5%**, `protocol_reward_rate` = 0.
- NearBlocks API: full history of any account.
- NEAR Intents Explorer API (partner key): per-swap assets, chains, USD amounts, referral, app fees, deposit type including `CONFIDENTIAL_INTENTS`. History starts March 2025.
- Known limitation: the daily NEAR price series has gaps (583 of ~728 days), filled by interpolation. To fix before the final report.

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
