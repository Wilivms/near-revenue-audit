# Pre-registered hypotheses

Written on 2026-10-29, **before** running the analysis. The git timestamp of this file is the proof.
Each hypothesis states what we expect, how we test it, and what result would prove us wrong.
Results are reported against this file in `REPORT.md`, including the ones we got wrong.

## Pillar 1 — Ledger: does the money exist?

**H1.1** Every dollar of protocol revenue reported by DefiLlama shows up as NEAR arriving in `buybacks.multisignature.near` within 7 days.
- Test: daily reconciliation of DefiLlama holders revenue vs on-chain inflows (NearBlocks), valued at the daily NEAR price.
- Wrong if: the cumulative gap is above 10%, or there are periods with revenue but no inflows.
- Note from the data probe (2026-10-29): the first inflow from `intents.near` is dated April 2026, while the fee switch is dated 23 Feb 2026. To explain.

**H1.2** The NEAR bought back stays in the buyback wallet (no material outflows).
- Test: sum of outflows from the wallet since creation.
- Wrong if: outflows exceed 1% of inflows.

**H1.3** The buyback execution is not worse than a naive daily TWAP.
- Test: effective NEAR acquired per dollar of revenue vs daily average price.
- Wrong if: the program bought at a price more than 3% above TWAP over the period.

## Pillar 2 — Supply: issuance vs buybacks

**H2.1** Buybacks offset less than 20% of new issuance since the fee switch.
- Probe estimate: ~12.5% (2.12M NEAR in the wallet vs ~17M NEAR issued over the same 6.2 months at 2.5%).
- Test: monthly net supply flow = issuance − buybacks − burnt fees, from RPC and NearBlocks.
- Wrong if: the ratio is above 20%.

**H2.2** The publicly quoted deflation threshold (~$177M/day of Intents volume) is in the right order of magnitude.
- Test: recompute with the observed take rate, price and issuance.
- Wrong if: our estimate differs by more than 30%.

## Pillar 3 — Quality of revenue

**H3.1** Revenue is concentrated: the top 3 integrators (referrals) generate more than 50% of fees.
- Test: Herfindahl index and top-N shares from the Intents Explorer API (`referral`, `appFees`).
- Wrong if: top-3 share is below 30%.

**H3.2** ZEC-related flows are a large and recent driver of volume (more than 20% of volume over the last 90 days).
- Test: share of volume where origin or destination asset is ZEC.
- Wrong if: below 10%.

**H3.3** The protocol take rate (revenue / fees) is stable over time.
- Test: rolling 30-day ratio from DefiLlama.
- Wrong if: it drops by more than 25% between the first and last quarter observed.

**H3.4** Users show weak retention: fewer than 20% of senders active in month M are active in month M+3.
- Test: monthly sender cohorts from the Explorer API.

## Pillar 4 — Incentives

**H4.1** A significant share of confidential TVL left after the NEAR@3.33 snapshot (17 Sep 2026).
- Test: confidential flows and balances before and after the snapshot; retention of addresses that entered in the 30 days before it.
- Wrong if: confidential TVL 30 days after the snapshot is above its level at the snapshot.

## Pillar 5 — Valuation

**H5.1** Under base-case growth, NEAR stays net inflationary through end-2027.
- Test: Monte Carlo on volume growth (block bootstrap of historical daily growth), take rate and price.
- Wrong if: the median path is net deflationary before end-2027.

## Kill criteria (monitored live on the dashboard)

The thesis is invalidated if any of these holds for 30 consecutive days:
- 30-day Intents protocol revenue below 50% of its trailing 180-day average.
- Top integrator share above 60% of fees.
- Buyback inflows stop for more than 14 days while fees continue.
