# NEAR Revenue Audit: the thesis

*Updated 2026-11-11 (first draft 2026-10-30). Live figures: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app). Working notes, dead ends and corrections: [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Hypotheses, written before the tests: [`HYPOTHESES.md`](HYPOTHESES.md). Not investment advice.*

## The question

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. The public story is that this will make NEAR scarce. We asked three things:

1. Is the revenue **real**: does what is reported actually reach NEAR's wallets?
2. Is it **durable**: who pays it, how concentrated is it, and does it depend on incentives?
3. Does it **matter for the token**: does it offset the NEAR that is issued every day, now or by end-2027?

## The answer in five lines

- **Real.** Rebuilt from the chain, captured revenue matches DefiLlama to 0.6% ($7.96M since the fee switch), and NEAR's own revenue dashboard, published after this rebuild, agrees within 0.2% on the NEAR received by the three wallets. Almost nothing has left the wallets (57,000 NEAR, 1.3% of what they received, traced to corrections returned to the bridge operator).
- **Growing, but partly bought.** NEAR's cut of volume more than doubled between August and October (2.2 to 5.5 bps). The largest identified driver is **confidential swaps**, which went from 13% of Intents volume to 41% and pay NEAR more than public swaps: about 5 to 11 bps against 1 to 3, depending on the method. That surge coincides with an airdrop campaign (NEAR@3.33) that rewards confidential balances and swaps; the timing fits, but the data cannot prove the campaign caused it. Its first drop cost about $1.4M in NEAR, a third to a half of the revenue the channel brought. In the first ten days of November, with confidential TVL 25% below its peak, the take fell back to 3.9 bps.
- **Not owned.** On 1Click, integrators keep about 91% of the fee pool. The largest one (SwapKit, 40% of volume, 71% of app fees) pays NEAR almost nothing. Half of NEAR's 1Click revenue comes from users without an integrator, and about half from one asset, ZEC.
- **Too small for the supply story.** Buybacks offset about **one sixth** of issuance: 15 NEAR bought back for every 100 issued since February on this audit's count, 16 on NEAR's own. Market cap is about **210 times** annual captured revenue; break-even needs **41 times**, or **64 times** once the issuance cut approved on 2 November is fully phased in.
- **Still true at end-2027 in the base case.** In 10,000 simulated paths, buybacks offset a median 17% of 2027 issuance (18% with the issuance cut); there is a 5–6% chance that 2027 is net deflationary. Break-even needs about $620M of daily volume at today's take, against about $130M now.

## Evidence

### 1. The revenue is real

| Check | Result | Where |
| --- | --- | --- |
| Reported revenue reaches NEAR's wallets | $7,960,601 rebuilt from NearBlocks vs $8,008,957 on DefiLlama (ratio 0.994, 2026-02-23 to 2026-11-10); each complete month within ±5% | log 2, `make revenue` |
| Scope | Three wallets, not one: buyback multisig (61%), front-end fund (32%), 1Click fund (7%) | log 2 |
| NEAR's own dashboard agrees | All-time NEAR received by the same three wallets: 4.304M rebuilt vs 4.298M on revenue.near.org (0.14% apart) | log 29, `make official` |
| Bought NEAR stays put | 57,036 NEAR (1.3% of all NEAR received) left; both outflows forwarded to `bridge-mng.near` the same day, one DAO proposal titled "Fees accrued by mistake" | log 3, 9 |
| Executed at market | Front-end fund conversions: +0.04% vs market, volume-weighted | log 4 |

Two caveats. First, NEAR's dashboard also publishes a monthly revenue series, and it runs about **20% above** the NEAR that reaches the three wallets it lists (ratio 1.14 to 1.23 each month since August, 1.21 in dollars over March–October). The ratio is stable, so trends agree, but where the difference goes is not visible on-chain from these wallets; the question has been put to NEAR (log 32). This audit counts only what reaches the wallets.

Second, the reading of "buyback". The front-end fund holds about 2.0M NEAR (47% of all NEAR captured to date). It is a Sputnik DAO run by accounts that appear to belong to Aurora's finance team. It has not sold, but nothing on-chain commits it not to, and it paid four 50,000 USDC invoices from revenue. **Bought is not retired.**

### 2. The revenue grew, with confidential swaps as the largest identified driver, under an incentive

Source: NEAR's own Dune dashboard (@near, "NEAR Intents"), read from its public result tables (log 24).

| | Aug 2026 | Sep 2026 | Oct 2026 |
| --- | --- | --- | --- |
| Confidential share of Intents volume | 13% | 28% | 41% |
| Confidential volume | $0.43B | $1.35B | $1.63B |
| Captured revenue, bps of all volume | 2.2 | 3.6 | 5.5 |

- **The fit.** Weekly, Aug–Oct (13 complete weeks): captured revenue ≈ **1.0 bps × public volume + 11 bps × confidential volume** (R² 0.85; bootstrap 90% interval on the confidential coefficient 9.7–13.4 bps; 10.7–12.2 when any one week is left out; a daily fit gives 9.2). Confidential volume tracks inflows to the buyback wallet (correlation 0.97; public volume 0.19).
- **How far to trust it.** Thirteen points, and both series rise over the window, so a fit in levels can pick up a shared trend. The same fit on **week-to-week changes** gives 5.5 bps on confidential volume (90% interval 2.2–9.0) and 2.9 on public. Dune's own fee table puts all confidential fees at 7.4 bps of confidential volume, all time, inside that interval. So confidential swaps do pay NEAR more, but the premium is somewhere between about 3 and 10 bps (log 32).
- **How much of the jump it explains.** NEAR's take rose 3.3 bps between August and October while the confidential share rose 28 points. The move to confidential swaps accounts for about **84%** of the rise with the levels fit, **54%** with Dune's fee table and **22%** with the fit on changes. "Most of it" holds only on the first; the rest is repricing on public flows (see 1Click below).
- **What NEAR's own page shows.** NEAR captured 19% of gross fees all-time and 37% over the last 30 days. All three of its collection mechanisms rose: front-end fees from 12% to 22% of gross fees, partner revenue-sharing from 5% to 11%, quote improvement from 2% to 4% (revenue.near.org, 2026-11-11). The rise is broad, with NEAR's own front-end the largest part.
- **Why it grew**: NEAR@3.33 (NEAR Foundation, announced 2026-06-15) rewards users who keep a confidential balance on near.com and swap confidentially. Drop 1, 333,333 NEAR, was triggered when confidential TVL reached $70M (mid-September) and converts to NEAR once NEAR holds $3.33 for three days, which happened around 2026-09-21 (about **$1.39M** at that price). Later rounds require more activity, which is consistent with TVL still growing after the snapshot. This is timing, not proof: near.com also launched new products over the same months, and there is no control group.
- **Cost against revenue**: confidential volume from the launch to October ≈ $3.75B, i.e. **$2.8M–4.1M** of revenue at 7.4–11 bps. Drop 1 alone cost **a third to a half** of it, paid in NEAR that enters circulation, against about 1M NEAR captured by the revenue wallets in September and October.
- **Did it pay for itself?** At the May–Aug take rate, Sep–Oct volume would have produced $2.09M; NEAR captured $3.96M. The $1.87M uplift is about 1.35x Drop 1's cost. In NEAR terms: the uplift bought about 479k NEAR while Drop 1 released 333k NEAR into circulation, a net 146k NEAR, or 0.01% of supply (log 25, 32). This credits the whole uplift to the incentive and counts only Drop 1 as its cost, so it is the favourable reading. Even so, the incentive moved revenue a lot and net supply hardly at all.
- **If the incentive ends** and the take rate falls back to its May–Aug level, the Monte Carlo puts the 2027 offset at a median 9% of issuance, half the base case; if it winds down over six months instead, 10% (log 26).
- **H4.1 is rejected**: confidential TVL did not leave after the snapshot. It was $71M on 2026-09-16, $155M thirty days later, peaked at $187M on 2026-09-27, and was $140M on 2026-11-09 (NEAR's revenue dashboard): still twice the snapshot level, but 25% below the peak.

#### Since November: the first out-of-sample test fails

- **The fit overshoots.** For the week of 2026-11-02, the levels fit predicted $0.90M of revenue and the fit on changes $0.47M; NEAR captured **$0.36M** (log 30, 32). Part of the miss is the label change below; part is a real fall.
- **The fall is in three sources.** The take on all Intents volume was 3.9 bps over 1–8 November (5.5 in October) while gross fees stayed at 16 bps: NEAR kept 25% of fees instead of 34%. DefiLlama's holders revenue gives 3.8 bps. NEAR's own monthly series stays the same 1.14–1.23 times the wallets, so it implies about 4.6 bps against 6.3 in October: the same fall of about 30%.
- **The label changed.** From 2026-11-03, NEAR's Dune dataset labels almost all volume confidential (89%), while the Explorer API still shows at least $20M of public 1Click swaps in half a day. The confidential share of volume can no longer be tracked, so the weekly fit is reported for Aug–Oct only, and the post-hoc criterion now watches confidential TVL.
- **Reading.** The September premium is real in the data through October. Ten days of November are not a trend, but they are the first data after TVL started falling, and they point down.

#### On 1Click (public swaps)


- Captured revenue / volume, 14-day rolling: about 2.2 bps in mid-August, 3.0 in mid-September, 5.4 in mid-October. Gross fees stayed at 14–16 bps, so NEAR's share of fees rose from about 15–20% to 35%. (log 7, 10)
- On 1Click (2.42M swaps collected from the Explorer API), NEAR's take went from 2.23 to 4.64 bps between the four weeks before the NEAR@3.33 snapshot and the last two weeks. Shift-share of the +2.4 bps (log 12):
  - +1.2 bps from a **new flow**: Trust Wallet's ZEC swaps at 20 bps to NEAR, from October;
  - about +1.4 bps from **higher fees in existing segments**: swaps without integrator 3.0 → 7.0 bps, Rango 0.6 → 4.2;
  - about −0.7 bps from a source that disappeared.
- The modal fee did not change (1 bp). The slice paying NEAR 11–20 bps went from 1% to 15% of volume and now brings 64% of NEAR's 1Click revenue.

### 3. NEAR does not own the customer

1Click swaps, 30 days to 2026-10-29, the last day collected (log 11, 18):

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

Coverage limit: 1Click is about 28% of Intents volume, and confidential swaps were not visible in the Explorer API over the period collected. These results describe 1Click, not all of Intents.

### 4. It does not offset issuance

- Net issuance measured from archival-RPC total supply: **2.42% a year**, 2.4–2.7M NEAR a month. (log 5)
- NEAR captured, Feb–Oct 2026: 3.53M NEAR vs 23.86M issued = **14.8%**. Monthly: 7% to 25%. NEAR's own dashboard gives 16.3% over the same months: it counts 1.5% more emissions and, as noted above, more revenue than reaches the wallets. Same order of magnitude. (log 5, 27, 29)
- **Issuance cut (HSP-029).** Governance approved on 2026-11-02 to lower maximum issuance from 2.5% to 1.6% a year over 24 months, pending ratification and a protocol upgrade. Fully phased in, it lifts break-even from 41× to 64× annual captured revenue. It narrows the gap by about a third. (log 31)
- Buybacks are reflexive: NEAR captured per month stayed in a 0.2–0.6M range with no upward trend while the price rose more than 4x from February to October. More dollars did not buy more NEAR.
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

Break-even at today's price ($3.58): about $620M/day at 5.0 bps, $390M/day at 8 bps, $210M/day at 15 bps. Figures as of the 2026-11-11 refresh; the dashboard recomputes them daily.

What the simulation assumes, and what that does to the result:

- **The take rate is fixed** at its last-30-day value in each scenario (or follows the stated ramp). It is a policy choice, not a random variable, which is why it is varied by scenario.
- **Volume and price are redrawn from the past**, together, in 30-day blocks. A regime that has not happened yet (a second product, a collapse) is outside the fan.
- **Issuance** is the measured rate applied to today's supply; the HSP-029 scenarios scale it by the approved schedule from an assumed start (2027-02-01, the earliest plausible).
- **Track record.** In a walk-forward test the engine was too optimistic in 2026 (log 21), so the percentages above are more likely too high than too low.

### 6. Against peers and competitors

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **20x** market cap / annualised holders revenue (12 peers with material holders revenue, interquartile 6–26x; 22x when first measured). NEAR trades at **220x**. At the peer median, NEAR Intents' revenue would support about $0.45B of market cap, against $4.9B: about 90% of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 58–79% each month from May to October 2026, while THORChain fell from 84% to 4–31%. November to date reverses it (NEAR 35%, THORChain 53%): DefiLlama shows THORChain volume above $180M a day from 4 November. That is eight days of data and may be a reporting artefact; it is flagged, not concluded. NEAR led its category on volume for six months; it has not yet turned that share into enough captured revenue.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Nov 2026): NEAR's volatility is about **103% a year** against 44% for BTC; its worst drawdown was **−88%** (Dec 2024 to Feb 2026), with 703 days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds 2.4% of supply a year; buybacks at the last 30 days' pace remove 0.4%. Supply still grows about **2.1% a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers (44% of supply) earn about 5.5% gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, 30 days to 2026-10-29): swaps whose volatile leg is BTC bring 30% of NEAR's revenue, ZEC 23%, ETH 16%. Stablecoin-to-stablecoin swaps are 30% of volume but 9% of revenue, at 1.3 bps.

## Bull case and bear case

**Bull.** Confidential swaps are a product NEAR monetises better than public swaps (about 5–11 bps against 1–3), and they reached 41% of volume. If a part of that use outlives the airdrop, the take rate stays well above its old level. The take rate is a lever NEAR can still pull: it doubled in two months and the sensitivity table shows that 8–15 bps with 2–4x today's volume reaches break-even. A single deal with the largest integrator, which now pays NEAR almost nothing, would add more revenue than any volume growth. The revenue is clean, reconciles to the chain and is not being sold.

**Bear.** The rise came mostly from confidential swaps whose growth coincides with an airdrop (Drop 1 cost about three quarters of the revenue uplift over its two best months), with each parked dollar swapped every 2–3 days. On 1Click, it came from pricing on flows NEAR controls (users without integrator, ZEC), the flows most exposed to competition. Integrators own the users, users do not stay, and half the 1Click revenue rides on one asset. If the take falls back to its May–Aug level, buybacks offset a tenth of issuance. Nearly half of what is called "buyback" sits in a treasury with no commitment not to sell.

## What would change our mind

Kill criteria were registered before the analysis and are monitored live on the dashboard. They are tripwires on the quality of the revenue: each one, if it holds for 30 consecutive days, would make the picture worse than this report describes. What would change the conclusion in NEAR's favour is listed under the catalysts below.

| Criterion | Status, 2026-11-11 |
| --- | --- |
| 30-day revenue below 50% of its trailing 180-day average | Not triggered: about 160% of the average |
| Buyback inflows stop for more than 14 days while fees continue | Not triggered: inflow yesterday |
| Top integrator above 60% of fees | **Triggered on 1Click** (SwapKit, 65–73% of app fees, all year), though SwapKit brings 1% of NEAR's revenue. The criterion did not say whose fees; we report it as written. All-Intents measure pending. |
| *Added after the fact, reported separately:* confidential TVL back below its level on the NEAR@3.33 snapshot day ($71M) | Not triggered: $140M, but −25% from the peak |

The third result is a lesson as much as a finding: a kill criterion should measure the quantity the thesis depends on, NEAR's captured revenue, not a proxy.

## Catalysts to watch

- Whether the take rate holds above 5 bps through Q4: the first ten days of November (3.9 bps) say it may not.
- Ratification and start date of the HSP-029 issuance cut.
- A revenue-sharing deal with SwapKit or other large integrators.
- An on-chain commitment (or a sale) by the front-end fund.
- ZEC flows: their share of NEAR's revenue, and whether Trust Wallet's deal lasts.
- Confidential TVL and NEAR's take once NEAR@3.33 rounds stop (further drops are "tba", per NEAR's moderators): the test of whether the take-rate jump is durable.

## Conviction and limits

- **High** on "real" and on "too small to offset issuance today": both follow from on-chain data and an identity.
- **Medium-low** on durability: the September jump is partly explained (confidential swaps account for a fifth to five sixths of it depending on the method, log 24, 32), and that channel grew under an incentive whose causal role is plausible but unproven. The fee NEAR earns on confidential swaps is estimated (about 5–11 bps), not published, and early November fell below every version of the fit.
- **Low** on end-2027 paths: the bootstrap can only replay the past, and the take rate is a policy choice.
- A walk-forward check of the simulation engine (log 21) shows it **overestimated** buyback capacity in 2026: realised outcomes fell below the 10th percentile in a third of 90-day forecasts. If anything, the 17% base case is too generous, which makes "net inflationary through 2027" a conservative conclusion.

Questions sent to the NEAR team (Discord ticket 2026-11-04, then near.com support, forwarded internally, no answer yet): the fee on confidential intents and who receives it, further NEAR@3.33 drops (answer: "tba"), and whether the front-end fund's NEAR is ever sold. One more is open since 2026-11-11: why NEAR's revenue series is about 20% above what the three wallets receive. Confidential TVL now has a public source (revenue.near.org).

## Reproduce

```bash
pip install -r requirements.txt
make data            # optional: fresh snapshots (committed ones are in data/raw/)
make revenue supply  # pillars 1 and 2
make montecarlo test # pillar 5 and model checks
make dashboard dashboard-serve
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
