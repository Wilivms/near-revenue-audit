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
| H3.1, H3.2, H3.4, H4.1, H5.1 | Pending swap-level data | collection in progress |

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
