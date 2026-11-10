# NEAR Revenue Audit: the thesis

*Updated 2026-11-10 (first draft 2026-10-30). Live figures: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app). Working notes, dead ends and corrections: [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Hypotheses, written before the tests: [`HYPOTHESES.md`](HYPOTHESES.md). Not investment advice.*

## The question

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. The public story is that this will make NEAR scarce. We asked three things:

1. Is the revenue **real**: does what is reported actually reach NEAR's wallets?
2. Is it **durable**: who pays it, how concentrated is it, and does it depend on incentives?
3. Does it **matter for the token**: does it offset the NEAR that is issued every day, now or by end-2027?

## The answer in five lines

- **Real.** Rebuilt from the chain, captured revenue matches DefiLlama to 0.6% ($7.90M since the fee switch), and NEAR's own revenue dashboard, published after this rebuild, agrees to 0.04% on the NEAR received by the three wallets. Almost nothing has left the wallets (1.6%, traced to corrections returned to the bridge operator).
- **Growing, but partly bought.** NEAR's cut of volume doubled from mid-September (about 2.2 to 5.4 bps). Most of the rise comes from **confidential swaps**, which went from 13% of Intents volume in August to 41% in October and pay NEAR roughly 7–12 bps, against under 1 bp on public swaps. That surge coincides with an airdrop campaign (NEAR@3.33) that rewards confidential balances and swaps; its first drop cost about $1.4M in NEAR, a third to a half of the revenue the channel brought. In the first week of November, with confidential TVL 25% below its peak, the take fell back to 3.9 bps.
- **Not owned.** On 1Click, integrators keep about 91% of the fee pool. The largest one (SwapKit, 40% of volume, 71% of app fees) pays NEAR almost nothing. Half of NEAR's 1Click revenue comes from users without an integrator, and about half from one asset, ZEC.
- **Too small for the supply story.** Buybacks offset about **one fifth** of issuance: about 16 NEAR bought back for every 100 issued since February, on this audit's count and on NEAR's own. Market cap is about **210 times** annual captured revenue; break-even needs **41 times**, or **64 times** once the issuance cut approved on 2 November is fully phased in.
- **Still true at end-2027 in the base case.** In 10,000 simulated paths, buybacks offset a median 17% of 2027 issuance (18% with the issuance cut); there is a 5–6% chance that 2027 is net deflationary. Break-even needs about $600M of daily volume at today's take, against $124M now.

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

- Weekly, Aug–Oct (12 complete weeks): captured revenue ≈ **0.7 bps × public volume + 12 bps × confidential volume** (R² 0.86). Bootstrap 90% interval on the confidential coefficient: 10.8–14.5 bps; a daily fit gives 10.2 bps (log 26). Confidential volume tracks inflows to the buyback wallet (correlation 0.97; public volume 0.34). Dune's own fee table puts all confidential fees at 7.4 bps of confidential volume, all time. On either figure, confidential swaps explain **most of the September–October jump**: from about 60% (at 7.4 bps) to nearly all of it (at 12 bps).
- **Why it grew**: NEAR@3.33 (NEAR Foundation, announced 2026-06-15) rewards users who keep a confidential balance on near.com and swap confidentially. Drop 1, 333,333 NEAR, was triggered when confidential TVL reached $70M (mid-September) and converts to NEAR once NEAR holds $3.33 for three days, which happened around 2026-09-21 (about **$1.39M** at that price). Later rounds require more activity, which is consistent with TVL still growing after the snapshot.
- **Cost against revenue**: confidential volume from the launch to October ≈ $3.75B, i.e. **$2.8M–4.6M** of revenue at 7.4–12 bps. Drop 1 alone cost **30–50%** of it, paid in NEAR that enters circulation, against about 1M NEAR captured by the revenue wallets in September and October.
- **Did it pay for itself?** At the May–Aug take rate, Sep–Oct volume would have produced $2.09M; NEAR captured $3.81M. The $1.72M uplift is about 1.2x Drop 1's cost. In NEAR terms the two cancel: the uplift bought about 408k NEAR while Drop 1 released 333k NEAR into circulation (log 25). The incentive moved revenue a lot and net supply hardly at all.
- **If the incentive ends** and the take rate falls back to its May–Aug level, the Monte Carlo puts the 2027 offset at a median 10% of issuance, half the base case; if it winds down over six months instead, 11% (log 26).
- **H4.1 is rejected**: confidential TVL did not leave after the snapshot. It was $71M on 2026-09-16, $155M thirty days later, peaked at $187M on 2026-09-27, and was $140M on 2026-11-09 (NEAR's revenue dashboard): still twice the snapshot level, but 25% below the peak.

#### Since November: the first out-of-sample test fails

- **The fit overshoots.** For the week of 2026-11-02, the fit predicted $0.90M of revenue; NEAR captured **$0.36M** (log 30). The take on all Intents volume fell to 3.9 bps (5.3 in October) while gross fees stayed at 16 bps: NEAR kept 25% of fees instead of 34%.
- **The label changed.** From 2026-11-03, NEAR's Dune dataset labels almost all volume confidential (89%), while the Explorer API still shows at least $20M of public 1Click swaps in half a day. The confidential share of volume can no longer be tracked, so the weekly fit is reported for Aug–Oct only, and the post-hoc criterion now watches confidential TVL.
- **Reading.** The September premium is real in the data through October. Whether it survives depends on the incentive, and the first week after TVL started falling says it is fading.

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
- NEAR captured, Feb–Oct 2026: 3.53M NEAR vs 23.86M issued = **14.8%**. Monthly: 7% to 25%. NEAR's own dashboard gives 16.3% over the same months (it counts gross emissions and its own revenue pricing); same order of magnitude. (log 5, 27, 29)
- **Issuance cut (HSP-029).** Governance approved on 2026-11-02 to lower maximum issuance from 2.5% to 1.6% a year over 24 months, pending ratification and a protocol upgrade. Fully phased in, it lifts break-even from 41× to 64× annual captured revenue. It narrows the gap by about a third. (log 31)
- Buybacks are reflexive: NEAR captured per month stayed roughly flat while the price rose about 4x from February to October. More dollars did not buy more NEAR.
- The invariant that matters, independent of volume: NEAR is net deflationary when **market cap / annual captured revenue < 1 / issuance rate ≈ 41x**. Today: about 210x. (log 6)
- The often-quoted "about $177M of daily volume makes NEAR deflationary" assumes 100% of fees buy NEAR. With the share that is actually captured, the threshold is about $600M a day at today's price and take (5.0 bps). (log 6, 17)

### 5. End-2027

Monte Carlo, 10,000 paths, volume and price drawn jointly in 30-day blocks from history (log 17, `make montecarlo`):

| Scenario | Share of 2027 issuance offset, median (p10–p90) | P(2027 net deflationary) |
| --- | --- | --- |
| Base: last 365 days, take at 4.97 bps (last 30 days), no price drift | 17% (5–66%) | 5% |
| Base + approved issuance cut (HSP-029, from Feb 2027) | 18% (5–72%) | 6% |
| Take falls back to May–Aug (2.63 bps) | 9% (3–35%) | 2% |
| Incentive winds down over 6 months | 10% (3–38%) | 2% |
| Wind-down + issuance cut | 11% (3–41%) | 2% |
| Only the buyback wallet counts as retired | 10% (3–40%) | 2% |
| Take doubles again (9.9 bps) | 33% (10–132%) | 15% |
| Last 180 days (volume ~5x by Dec 2027) | 48% (12–200%) | 25% |

Break-even at today's price ($3.58): about $620M/day at 5.0 bps, $390M/day at 8 bps, $210M/day at 15 bps. Figures as of the 2026-11-10 refresh; the dashboard recomputes them daily.

### 6. Against peers and competitors

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **22x** market cap / annualised holders revenue (12 peers, interquartile 6–28x). NEAR trades at **212x** (220x on the 2026-11-10 refresh). At the peer median, NEAR Intents' revenue would support about $0.6B of market cap, against $5.6B: about 90% of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 61–79% each month since May 2026; THORChain fell from 84% to 16–32%. NEAR won its category on volume; it has not yet turned that share into enough captured revenue.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Oct 2026): NEAR's volatility is about **103% a year** against 44% for BTC; its worst drawdown was **−88%** (Dec 2024 to Feb 2026), with 692 days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds 2.4% of supply a year; buybacks at the last 30 days' pace remove 0.4%. Supply still grows about **2.0% a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers (45% of supply) earn about 5.3% gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, last 30 days): swaps whose volatile leg is BTC bring 30% of NEAR's revenue, ZEC 23%, ETH 16%. Stablecoin-to-stablecoin swaps are 30% of volume but 9% of revenue, at 1.3 bps.

## Bull case and bear case

**Bull.** Confidential swaps are a product NEAR monetises well (7–12 bps against under 1 bp on public swaps), and they reached 41% of volume. If a part of that use outlives the airdrop, the take rate stays well above its old level. The take rate is a lever NEAR can still pull: it doubled in two months and the sensitivity table shows that 8–15 bps with 2–4x today's volume reaches break-even. A single deal with the largest integrator, which now pays NEAR almost nothing, would add more revenue than any volume growth. The revenue is clean, reconciles to the chain and is not being sold.

**Bear.** The rise came mostly from confidential swaps whose growth an airdrop is paying for (Drop 1 ≈ the revenue uplift it created), with each parked dollar swapped every 2–3 days. On 1Click, it came from pricing on flows NEAR controls (users without integrator, ZEC), the flows most exposed to competition. Integrators own the users, users do not stay, and half the 1Click revenue rides on one asset. If the take falls back to its May–Aug level, buybacks offset a tenth of issuance. Nearly half of what is called "buyback" sits in a treasury with no commitment not to sell.

## What would change our mind

Kill criteria, registered in advance and monitored live on the dashboard. Each invalidates the thesis if it holds for 30 consecutive days.

| Criterion | Status, 2026-11-10 |
| --- | --- |
| 30-day revenue below 50% of its trailing 180-day average | Not triggered: about 160% of the average |
| Buyback inflows stop for more than 14 days while fees continue | Not triggered: inflow yesterday |
| Top integrator above 60% of fees | **Triggered on 1Click** (SwapKit, 65–73% of app fees, all year), though SwapKit brings 1% of NEAR's revenue. The criterion did not say whose fees; we report it as written. All-Intents measure pending. |

| *Added after the fact, reported separately:* confidential TVL back below its level on the NEAR@3.33 snapshot day ($71M) | Not triggered: $140M, but −25% from the peak |

The third result is a lesson as much as a finding: a kill criterion should measure the quantity the thesis depends on, NEAR's captured revenue, not a proxy.

## Catalysts to watch

- Whether the take rate holds above 5 bps through Q4: the first week of November (3.9 bps) says it may not.
- Ratification and start date of the HSP-029 issuance cut.
- A revenue-sharing deal with SwapKit or other large integrators.
- An on-chain commitment (or a sale) by the front-end fund.
- ZEC flows: their share of NEAR's revenue, and whether Trust Wallet's deal lasts.
- Confidential TVL and NEAR's take once NEAR@3.33 rounds stop (further drops are "tba", per NEAR's moderators): the test of whether the take-rate jump is durable.

## Conviction and limits

- **High** on "real" and on "too small to offset issuance today": both follow from on-chain data and an identity.
- **Medium-low** on durability: the September jump is now explained (confidential swaps, log 24), and that channel is incentive-driven. The fee NEAR earns on confidential swaps is estimated (7–12 bps), not published, and the first week of November fell well below the fit.
- **Low** on end-2027 paths: the bootstrap can only replay the past, and the take rate is a policy choice.
- A walk-forward check of the simulation engine (log 21) shows it **overestimated** buyback capacity in 2026: realised outcomes fell below the 10th percentile in a third of 90-day forecasts. If anything, the 17% base case is too generous, which makes "net inflationary through 2027" a conservative conclusion.

Questions sent to the NEAR team (Discord ticket 2026-11-04, then near.com support, forwarded internally, no answer yet): the fee on confidential intents and who receives it, further NEAR@3.33 drops (answer: "tba"), and whether the front-end fund's NEAR is ever sold. Confidential TVL now has a public source (revenue.near.org).

## Reproduce

```bash
pip install -r requirements.txt
make data            # optional: fresh snapshots (committed ones are in data/raw/)
make revenue supply  # pillars 1 and 2
make montecarlo test # pillar 5 and model checks
make dashboard dashboard-serve
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
