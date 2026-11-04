# NEAR Revenue Audit: the thesis

*Draft, 2026-10-30. Live figures: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app). Working notes, dead ends and corrections: [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Hypotheses, written before the tests: [`HYPOTHESES.md`](HYPOTHESES.md). Not investment advice.*

## The question

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. The public story is that this will make NEAR scarce. We asked three things:

1. Is the revenue **real**: does what is reported actually reach NEAR's wallets?
2. Is it **durable**: who pays it, how concentrated is it, and does it depend on incentives?
3. Does it **matter for the token**: does it offset the NEAR that is issued every day, now or by end-2027?

## The answer in five lines

- **Real.** Rebuilt from the chain, captured revenue matches DefiLlama to 0.1% ($7.29M since the fee switch). Almost nothing has left the wallets (1.6%, traced to corrections returned to the bridge operator).
- **Growing, but partly bought.** NEAR's cut of volume doubled from mid-September (about 2.2 to 5.4 bps). Most of the rise comes from **confidential swaps**, which went from 13% of Intents volume in August to 41% in October and pay NEAR roughly 7–12 bps, against under 1 bp on public swaps. That surge coincides with an airdrop campaign (NEAR@3.33) that rewards confidential balances and swaps; its first drop cost about $1.4M in NEAR, a third to a half of the revenue the channel brought.
- **Not owned.** On 1Click, integrators keep about 91% of the fee pool. The largest one (SwapKit, 40% of volume, 71% of app fees) pays NEAR almost nothing. Half of NEAR's 1Click revenue comes from users without an integrator, and about half from one asset, ZEC.
- **Too small for the supply story.** Buybacks offset about **one fifth** of issuance: 19 NEAR bought back for every 100 issued over the last 30 days. Market cap is about **210 times** annual captured revenue; break-even needs **41 times**.
- **Still true at end-2027 in the base case.** In 10,000 simulated paths, buybacks offset a median 21% of 2027 issuance; there is a 9% chance that 2027 is net deflationary. Break-even needs about $750M of daily volume at today's take, against $135M now.

## Evidence

### 1. The revenue is real

| Check | Result | Where |
| --- | --- | --- |
| Reported revenue reaches NEAR's wallets | $7,287,030 rebuilt from NearBlocks vs $7,295,035 on DefiLlama (ratio 0.999); each month within ±5% | log 2, `make revenue` |
| Scope | Three wallets, not one: buyback multisig (60%), front-end fund (32%), 1Click fund (8%) | log 2 |
| Bought NEAR stays put | 57,036 NEAR (1.6%) left; both outflows forwarded to `bridge-mng.near` the same day, one DAO proposal titled "Fees accrued by mistake" | log 3, 9 |
| Executed at market | Front-end fund conversions: +0.04% vs market, volume-weighted | log 4 |

One caveat changes the reading of "buyback". The front-end fund holds about 1.95M NEAR (47% of all NEAR captured to date). It is a Sputnik DAO run by accounts that appear to belong to Aurora's finance team. It has not sold, but nothing on-chain commits it not to, and it paid four 50,000 USDC invoices from revenue. **Bought is not retired.**

### 2. The revenue is growing, mostly through confidential swaps, which an incentive is paying for

Source: NEAR's own Dune dashboard (@near, "NEAR Intents"), read from its public result tables (log 24).

| | Aug 2026 | Sep 2026 | Oct 2026 |
| --- | --- | --- | --- |
| Confidential share of Intents volume | 13% | 28% | 41% |
| Confidential volume | $0.43B | $1.35B | $1.63B |
| Captured revenue, bps of all volume | ~2.3 | ~3.7 | ~5.5 |

- Weekly, Aug–Oct (12 complete weeks): captured revenue ≈ **0.7 bps × public volume + 12 bps × confidential volume** (R² 0.86). Confidential volume tracks inflows to the buyback wallet (correlation 0.97; public volume 0.34). Dune's own fee table puts all confidential fees at 7.4 bps of confidential volume, all time. On either figure, confidential swaps explain **most of the September–October jump**: from about 60% (at 7.4 bps) to nearly all of it (at 12 bps).
- **Why it grew**: NEAR@3.33 (NEAR Foundation, announced 2026-06-15) rewards users who keep a confidential balance on near.com and swap confidentially. Drop 1, 333,333 NEAR, was triggered when confidential TVL reached $70M (mid-September) and converts to NEAR once NEAR holds $3.33 for three days, which happened around 2026-09-21 (about **$1.39M** at that price). Later rounds require more activity, which is consistent with TVL still growing after the snapshot.
- **Cost against revenue**: confidential volume from the launch to October ≈ $3.75B, i.e. **$2.8M–4.6M** of revenue at 7.4–12 bps. Drop 1 alone cost **30–50%** of it, paid in NEAR that enters circulation, against about 1M NEAR captured by the revenue wallets in September and October.
- **H4.1 is rejected**: confidential TVL did not leave after the snapshot. It was $71M on 2026-09-16, $155M thirty days later, peaked at $187M on 2026-09-27 and was $143M on 2026-10-31.

#### On 1Click (public swaps)


- Captured revenue / volume, 14-day rolling: about 2.2 bps in mid-August, 3.0 in mid-September, 5.4 in mid-October. Gross fees stayed at 14–16 bps, so NEAR's share of fees rose from about 15–20% to 35%. (log 7, 10)
- On 1Click (2.42M swaps collected from the Explorer API), NEAR's take went from 2.23 to 4.64 bps between the four weeks before the NEAR@3.33 snapshot and the last two weeks. Shift-share of the +2.4 bps (log 12):
  - +1.2 bps from a **new flow**: Trust Wallet's ZEC swaps at 20 bps to NEAR, from October;
  - about +1.4 bps from **higher fees in existing segments**: swaps without integrator 3.0 → 7.0 bps, Rango 0.6 → 4.2;
  - about −0.7 bps from a source that disappeared.
- The modal fee did not change (1 bp). The slice paying NEAR 11–20 bps went from 1% to 15% of volume and now brings 64% of NEAR's 1Click revenue.

### 3. NEAR does not own the customer

1Click swaps, last 30 days (log 11, 18):

| Integrator | Volume | App fees | NEAR's revenue |
| --- | --- | --- | --- |
| SwapKit | 40% | 71% | 1% |
| No integrator | 20% | 6% | 46% |
| Anonymous referral `e1a72603…` | 0.7% | 2% | 12% |
| Trust Wallet | 2.5% | 1% | 11% |

- NEAR keeps about 9% of the 1Click fee pool; integrators keep the rest.
- **ZEC** is 18.6% of 1Click volume over 76 days but about half of NEAR's 1Click revenue in the last two weeks. (log 13)
- **Users do not stay.** 3–5% of the addresses active in a given week come back in the same week three months later; at most 9–19% are seen again at any time over 2.5 months. These are lower bounds (a returning user with a new address counts as new). (log 14)
- Reading: NEAR's 1Click revenue rests on unattributed users, a few direct deals and one asset. Distribution partners own the flow, and could route it elsewhere.

Coverage limit: 1Click is about 28% of Intents volume, and confidential swaps are not visible in the Explorer API. NEAR's Dune datasets are needed to extend these results to all of Intents.

### 4. It does not offset issuance

- Net issuance measured from archival-RPC total supply: **2.42% a year**, 2.4–2.7M NEAR a month. (log 5)
- NEAR captured, Feb–Oct 2026: 3.49M NEAR vs 23.70M issued = **14.7%**. Monthly: 4% to 25%. (log 5)
- Buybacks are reflexive: NEAR captured per month stayed roughly flat while the price rose about 4x from February to October. More dollars did not buy more NEAR.
- The invariant that matters, independent of volume: NEAR is net deflationary when **market cap / annual captured revenue < 1 / issuance rate ≈ 41x**. Today: about 210x. (log 6)
- The often-quoted "about $177M of daily volume makes NEAR deflationary" assumes 100% of fees buy NEAR. With the share that is actually captured, the threshold is about $750M a day at today's price and take. (log 6, 17)

### 5. End-2027

Monte Carlo, 10,000 paths, volume and price drawn jointly in 30-day blocks from history (log 17, `make montecarlo`):

| Scenario | Share of 2027 issuance offset, median (p10–p90) | P(2027 net deflationary) |
| --- | --- | --- |
| Base: last 365 days, take at 5.41 bps, no price drift | 21% (6–90%) | 9% |
| Take falls back to May–Aug (2.63 bps) | 10% (3–44%) | 3% |
| Only the buyback wallet counts as retired | 12% (3–54%) | 4% |
| Take doubles again (10.8 bps) | 41% (11–181%) | 21% |
| Last 180 days (volume ~10x by Dec 2027) | 92% (21–422%) | 47% |

Break-even at today's price: about $750M/day at 5.4 bps, $500M/day at 8 bps, $250M/day at 15 bps.

### 6. Against peers and competitors

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **22x** market cap / annualised holders revenue (12 peers, interquartile 6–28x). NEAR trades at **212x**. At the peer median, NEAR Intents' revenue would support about $0.6B of market cap, against $5.6B: about 90% of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 61–79% each month since May 2026; THORChain fell from 84% to 16–32%. NEAR won its category on volume; it has not yet turned that share into enough captured revenue.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Oct 2026): NEAR's volatility is about **103% a year** against 44% for BTC; its worst drawdown was **−88%** (Dec 2024 to Feb 2026), with 692 days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds 2.4% of supply a year; buybacks at the last 30 days' pace remove 0.4%. Supply still grows about **2.0% a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers (45% of supply) earn about 5.3% gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, last 30 days): swaps whose volatile leg is BTC bring 30% of NEAR's revenue, ZEC 23%, ETH 16%. Stablecoin-to-stablecoin swaps are 30% of volume but 9% of revenue, at 1.3 bps.

## Bull case and bear case

**Bull.** The take rate is a lever NEAR can still pull: it doubled in two months and the sensitivity table shows that 8–15 bps with 2–4x today's volume reaches break-even. A single deal with the largest integrator, which now pays NEAR almost nothing, would add more revenue than any volume growth. The revenue is clean, reconciles to the chain and is not being sold.

**Bear.** The rise came from pricing, on flows NEAR controls (users without integrator, ZEC). Those are the flows most exposed to competition from other routes. Integrators own the users, users do not stay, and half the 1Click revenue rides on one asset. If the take falls back to its May–Aug level, buybacks offset a tenth of issuance. Nearly half of what is called "buyback" sits in a treasury with no commitment not to sell.

## What would change our mind

Kill criteria, registered in advance and monitored live on the dashboard. Each invalidates the thesis if it holds for 30 consecutive days.

| Criterion | Status, 2026-10-30 |
| --- | --- |
| 30-day revenue below 50% of its trailing 180-day average | Not triggered: about 205% of the average |
| Buyback inflows stop for more than 14 days while fees continue | Not triggered: inflow yesterday |
| Top integrator above 60% of fees | **Triggered on 1Click** (SwapKit, 65–73% of app fees, all year), though SwapKit brings 1% of NEAR's revenue. The criterion did not say whose fees; we report it as written. All-Intents measure pending. |

The third result is a lesson as much as a finding: a kill criterion should measure the quantity the thesis depends on, NEAR's captured revenue, not a proxy.

## Catalysts to watch

- Whether the September take-rate increase holds through Q4, or competition pulls it back.
- A revenue-sharing deal with SwapKit or other large integrators.
- An on-chain commitment (or a sale) by the front-end fund.
- ZEC flows: their share of NEAR's revenue, and whether Trust Wallet's deal lasts.
- Confidential-intents flows after the NEAR@3.33 snapshot (H4.1, not yet testable).

## Conviction and limits

- **High** on "real" and on "too small to offset issuance today": both follow from on-chain data and an identity.
- **Medium** on durability: the swap-level evidence covers 1Click only (28% of volume), and the September change is not explained for the other 72%.
- **Low** on end-2027 paths: the bootstrap can only replay the past, and the take rate is a policy choice.
- A walk-forward check of the simulation engine (log 21) shows it **overestimated** buyback capacity in 2026: realised outcomes fell below the 10th percentile in a third of 90-day forecasts. If anything, the 21% base case is too generous, which makes "net inflationary through 2027" a conservative conclusion.

Open questions for the NEAR team, to be asked once NEAR's Dune datasets have been checked: what changed in mid-September, how integrator fees are set, the status of the front-end fund's NEAR, and a source for confidential-intents TVL.

## Reproduce

```bash
pip install -r requirements.txt
make data            # optional: fresh snapshots (committed ones are in data/raw/)
make revenue supply  # pillars 1 and 2
make montecarlo test # pillar 5 and model checks
make dashboard dashboard-serve
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
