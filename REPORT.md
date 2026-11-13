<!-- Generated from docs/templates/REPORT.md by `make docs`; edit the template, not this file. -->
# NEAR Revenue Audit: the thesis

*Data to 2026-11-12 (first draft 2026-10-30). Every figure in this file is rendered from `data/processed/` by `make docs`. Live figures: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app). Working notes, dead ends and corrections: [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Hypotheses, written before the tests: [`HYPOTHESES.md`](HYPOTHESES.md). Not investment advice.*

## The question

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. The public story is that this will make NEAR scarce. We asked three things:

1. Is the revenue **real**: does what is reported actually reach NEAR's wallets?
2. Is it **durable**: who pays it, how concentrated is it, and does it depend on incentives?
3. Does it **matter for the token**: does it offset the NEAR that is issued every day, now or by end-2027?

## The answer in five lines

- **Real.** Rebuilt from the chain, captured revenue matches DefiLlama within 0.8% ($8.09M since the fee switch), and NEAR's own revenue dashboard, published after this rebuild, agrees within 0.16% on the NEAR received by the three wallets. Almost nothing has left the wallets (57,037 NEAR, 1.3% of what they received, traced to corrections returned to the bridge operator).
- **Growing, but partly bought.** NEAR's cut of volume more than doubled between August and October (2.2 to 5.5 bps). The largest identified driver is **confidential swaps**, which went from 13% of Intents volume to 41% and pay NEAR more than public swaps: about 5.5–11 bps against 1–3, depending on the method. That surge coincides with an airdrop campaign (NEAR@3.33) that rewards confidential balances and swaps; the timing fits, but the data cannot prove the campaign caused it. Its first drop cost about $1.39M in NEAR, a third to a half of the revenue the channel brought. In the first full week of November, with confidential TVL 26% below its peak, the take fell back to 3.9 bps.
- **Not owned.** On 1Click, integrators keep about 92% of the fee pool. The largest one (SwapKit, 39% of volume, 75% of app fees) pays NEAR under 0.1% of its revenue. 39% of NEAR's 1Click revenue comes from users without an integrator.
- **Too small for the supply story.** Buybacks offset about **one sixth** of issuance: 15 NEAR bought back for every 100 issued since February on this audit's count, 16 on NEAR's own. Market cap is **205x** annual captured revenue; break-even needs **41x**, or **64x** once the issuance cut approved on 2 November is fully phased in.
- **Still true at end-2027 in the base case.** In 10,000 simulated paths, buybacks offset a median 18% of 2027 issuance (20% with the issuance cut); there is a 7% chance that 2027 is net deflationary (7% with the cut). Break-even needs about $639M of daily volume at today's take, against about $127M now.

## Evidence

### 1. The revenue is real

| Check | Result | Where |
| --- | --- | --- |
| Reported revenue reaches NEAR's wallets | $8,087,549 rebuilt from NearBlocks vs $8,149,355 on DefiLlama (ratio 0.992, 2026-02-23 to 2026-11-12); each complete month within -5% to +4% | log 2, `make revenue` |
| Scope | Three wallets, not one: buyback multisig (61%), front-end fund (32%), 1Click fund (7%) | log 2 |
| NEAR's own dashboard agrees | All-time NEAR received by the same three wallets: 4.346M rebuilt vs 4.339M on revenue.near.org (0.16% apart) | log 29, `make official` |
| Bought NEAR stays put | 57,037 NEAR (1.3% of all NEAR received) left; both outflows forwarded to `bridge-mng.near` the same day, one DAO proposal titled "Fees accrued by mistake" | log 3, 9 |
| Executed at market | Front-end fund conversions: +0.04% vs market, volume-weighted | log 4 |

Two caveats. First, NEAR's dashboard also publishes a monthly revenue series, and it runs about **21% above** the NEAR that reaches the three wallets it lists (ratio 1.14 to 1.33 each month since July; 21% more in dollars over March–October). The ratio is stable, so trends agree, but where the difference goes is not visible on-chain from these wallets; the question has been put to NEAR (log 32). This audit counts only what reaches the wallets.

Second, the reading of "buyback". The front-end fund holds about 2.0M NEAR (47% of all NEAR captured to date). It is a Sputnik DAO run by accounts that appear to belong to Aurora's finance team. It has not sold, but nothing on-chain commits it not to, and it paid four 50,000 USDC invoices from revenue. **Bought is not retired.**

### 2. The revenue grew, with confidential swaps as the largest identified driver, under an incentive

Source: NEAR's own Dune dashboard (@near, "NEAR Intents"), read from its public result tables (log 24).

| | Aug 2026 | Sep 2026 | Oct 2026 |
| --- | --- | --- | --- |
| Confidential share of Intents volume | 13% | 28% | 41% |
| Confidential volume | $0.43B | $1.35B | $1.63B |
| Captured revenue, bps of all volume | 2.2 | 3.6 | 5.5 |

- **The fit.** Weekly, Aug–Oct (13 complete weeks): captured revenue ≈ **1.0 bps × public volume + 11.0 bps × confidential volume** (R² 0.85; bootstrap 90% interval on the confidential coefficient 9.7–13.4 bps; 10.7–12.2 when any one week is left out; a daily fit gives 9.2). Confidential volume tracks inflows to the buyback wallet (correlation 0.97; public volume 0.19).
- **How far to trust it.** Thirteen points, and both series rise over the window, so a fit in levels can pick up a shared trend. The same fit on **week-to-week changes** gives 5.5 bps on confidential volume (90% interval 2.2–9.0) and 2.9 on public. Dune's own fee table puts all confidential fees at 7.4 bps of confidential volume, all time, inside that interval. So confidential swaps do pay NEAR more, but the premium is somewhere between about 3 and 10 bps (log 32).
- **How much of the jump it explains.** NEAR's take rose 3.3 bps between August and October while the confidential share rose 28 points. The move to confidential swaps accounts for about **84%** of the rise with the levels fit, **54%** with Dune's fee table and **22%** with the fit on changes. "Most of it" holds only on the first; the rest is repricing on public flows (see 1Click below).
- **What NEAR's own page shows.** NEAR captured 19% of gross fees all-time and 33% over the last 30 days. All three of its collection mechanisms rose: front-end fees from 12% to 19% of gross fees, partner revenue-sharing from 5% to 10%, quote improvement from 2% to 4% (revenue.near.org, 2026-11-11). The rise is broad, with NEAR's own front-end the largest part.
- **Why it grew**: NEAR@3.33 (NEAR Foundation, announced 2026-06-15) rewards users who keep a confidential balance on near.com and swap confidentially. Drop 1, 333,333 NEAR, was triggered when confidential TVL reached $70M (mid-September) and converts to NEAR once NEAR holds $3.33 for three days, which happened around 2026-09-21 (about **$1.39M** at that price). Later rounds require more activity, which is consistent with TVL still growing after the snapshot. This is timing, not proof: near.com also launched new products over the same months, and there is no control group.
- **Cost against revenue**: confidential volume from the launch to October ≈ $3.75B, i.e. **$2.8M–$4.1M** of revenue at 7.4–11.0 bps. Drop 1 alone cost **a third to a half** of it, paid in NEAR that enters circulation, against about 1M NEAR captured by the revenue wallets in September and October.
- **Did it pay for itself?** At the May–Aug take rate, Sep–Oct volume would have produced $2.09M; NEAR captured $3.96M. The $1.87M uplift is about 1.35x Drop 1's cost. In NEAR terms: the uplift bought about 479k NEAR while Drop 1 released 333k NEAR into circulation, a net 146k NEAR, or 0.01% of supply (log 25, 32). This credits the whole uplift to the incentive and counts only Drop 1 as its cost, so it is the favourable reading. Even so, the incentive moved revenue a lot and net supply hardly at all.
- **If the incentive ends** and the take rate falls back to its May–Aug level, the Monte Carlo puts the 2027 offset at a median 10% of issuance, half the base case; if it winds down over six months instead, 11% (log 26).
- **H4.1 is rejected**: confidential TVL did not leave after the snapshot. It was $71M on 2026-09-16, $155M thirty days later, peaked at $187M on 2026-09-27, and was $138M on 2026-11-12 (NEAR's revenue dashboard): still about twice the snapshot level, but 26% below the peak.

#### Since November: the first out-of-sample test fails

- **The fit overshoots.** For the week of 2026-11-02, the levels fit predicted $901k of revenue and the fit on changes $475k; NEAR captured **$355k** (log 30, 32). Part of the miss is the label change below; part is a real fall.
- **The fall is in three sources.** The take on all Intents volume was 3.9 bps in the week of 2 November (5.5 in October) while gross fees stayed at 16 bps: NEAR kept 25% of fees instead of 35%. DefiLlama's holders revenue gives 3.8 bps. NEAR's own monthly series stays about the same multiple of the wallets, so it implies about 4.5 bps against 6.3 in October: the same fall of about 30%.
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

1Click swaps, 2026-10-14 to 2026-11-12, the last 30 days collected (512k swaps; 2.7M collected in all; log 11, 18, 34, 36):

| Integrator | Volume | App fees | NEAR's revenue |
| --- | --- | --- | --- |
| SwapKit | 38.8% | 74.7% | 0.0% |
| No integrator (NEAR's front-end, direct users) | 16.5% | 4.8% | 39.2% |
| Trust Wallet | 2.5% | 1.1% | 13.4% |
| LI.FI | 12.1% | 1.3% | 8.1% |
| Arbie | 1.4% | 0.6% | 7.3% |
| Anonymous referral `e1a72603…` | 0.4% | 1.2% | 7.2% |

- Integrators keep about 92% of the 1Click fee pool; NEAR keeps the rest.
- **ZEC** is 18.6% of 1Click volume over 76 days but about half of NEAR's 1Click revenue in the last two weeks. (log 13)
- **Users do not stay.** 3–5% of the addresses active in a given week come back in the same week three months later; at most 9–19% are seen again at any time over 2.5 months. These are lower bounds (a returning user with a new address counts as new). (log 14)
- **The volume is broad, not wash-traded** (`oneclick_quality.json`, log 36). 235k sending addresses (86% of swaps carry one); 78% swapped once. The top 10 send 19% of volume and the top 100 34% (HHI 93). 140 addresses with 100 swaps or more, likely bots, market makers and integrator hot wallets, send 18% of volume and 14% of NEAR's revenue. Round trips, where an address swaps A into B and B back into A within 24 hours, are 2.9% of volume and 1.3% of NEAR's revenue, 79% of them through one integrator (LI.FI). Self-trading does not inflate the revenue. An independent entry (Toll Road) finds about 1% round trips outside market makers on a 1.2% sample of `intents.near`; the full 1Click record agrees.
- Reading: NEAR's 1Click revenue rests on unattributed users, a few direct deals and one asset. Distribution partners own the flow, and could route it elsewhere.

Coverage limit: 1Click is about 28% of Intents volume, and confidential swaps were not visible in the Explorer API over the period collected. These results describe 1Click, not all of Intents.

### 4. It does not offset issuance

- Net issuance measured from archival-RPC total supply: **2.43% a year**, 2.4–2.7M NEAR a month. (log 5)
- NEAR captured, Feb–Oct 2026: 3.53M NEAR vs 23.9M issued = **14.8%**. Monthly: 7% to 25%. NEAR's own dashboard gives 16.3% over the same months: it counts 1.5% more emissions and, as noted above, more revenue than reaches the wallets. Same order of magnitude. (log 5, 27, 29)
- **Issuance cut (HSP-029).** House of Stake's vote closed on 2026-11-02 with 99.97% of veNEAR cast in favour (36 voters, 62% turnout, read on-chain from `vote.dao`). It lowers maximum issuance from 2.5% to 1.6% a year over 24 months. Status on 2026-11-12: Timelock, ending 2026-11-16; then a 90-day grace period and a protocol upgrade validators must adopt, so the ramp cannot start before 2027-02-14. Fully phased in, it lifts break-even from 41x to 64x annual captured revenue. It narrows the gap by about a third. (log 31)
- Buybacks are reflexive: NEAR captured per month stayed in a 0.2–0.6M range with no upward trend while the price rose more than 4x from February to October. More dollars did not buy more NEAR.
- The invariant that matters, independent of volume: NEAR is net deflationary when **market cap / annual captured revenue < 1 / issuance rate ≈ 41x**. Today: 205x. (log 6)
- The often-quoted "about $177M of daily volume makes NEAR deflationary" assumes 100% of fees buy NEAR. With the share that is actually captured, the threshold is about $639M a day at today's price and take (4.9 bps). (log 6, 17)

### 5. End-2027

Monte Carlo, 10,000 paths, volume and price drawn jointly in 30-day blocks from history (log 17, `make montecarlo`):

| Scenario | Share of 2027 issuance offset, median (p10–p90) | P(2027 net deflationary) |
| --- | --- | --- |
| Base: last 365 days, take at 4.9 bps (last 30 days), no price drift | 18% (5–75%) | 7% |
| Base + approved issuance cut (HSP-029, from 2027-02-14) | 20% (6–81%) | 7% |
| Take falls back to May–Aug (2.6 bps) | 10% (3–40%) | 2% |
| Incentive winds down over 6 months | 11% (3–43%) | 2% |
| Wind-down + issuance cut | 12% (4–46%) | 3% |
| Only the buyback wallet counts as retired | 11% (3–45%) | 3% |
| Take doubles again (9.8 bps) | 37% (11–151%) | 17% |
| Last 180 days (volume ~4x by Dec 2027) | 50% (13–206%) | 26% |

Break-even at today's price: about $639M/day at 4.9 bps, $392M/day at 8 bps, $209M/day at 15 bps. The dashboard recomputes these daily.

What the simulation assumes, and what that does to the result:

- **The take rate is fixed** at its last-30-day value in each scenario (or follows the stated ramp). It is a policy choice, not a random variable, which is why it is varied by scenario.
- **Volume and price are redrawn from the past**, together, in 30-day blocks. A regime that has not happened yet (a second product, a collapse) is outside the fan.
- **Issuance** is the measured rate applied to today's supply; the HSP-029 scenarios scale it by the approved schedule from the earliest start the chain allows (2027-02-14).
- **Track record.** In a walk-forward test the engine was too optimistic in 2026 (log 21), so the percentages above are more likely too high than too low.

### 6. Against peers and competitors

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **20x** market cap / annualised holders revenue (12 peers with material holders revenue, interquartile 6–27x). NEAR trades at **208x**. At the peer median, NEAR Intents' revenue would support about $453M of market cap, against $4.6B (about $0.33 a NEAR, against $3.42): about 90% of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 58–79% each month from May to October 2026, while THORChain fell from 84% to 4–31%. November to date reverses it (NEAR 35%, THORChain 53%): DefiLlama shows THORChain volume above $180M a day from 4 November. That is eight days of data and may be a reporting artefact; it is flagged, not concluded. NEAR led its category on volume for six months; it has not yet turned that share into enough captured revenue.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Nov 2026): NEAR's volatility is about **103% a year** against 44% for BTC; its worst drawdown was **-88%** (Dec 2024 to Feb 2026), with 705 days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds 2.43% of supply a year; buybacks at the last 30 days' pace remove 0.4%. Supply still grows about **2.1% a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers (45% of supply) earn about 5.4% gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, 2026-10-14 to 2026-11-12): swaps whose volatile leg is BTC bring 37% of NEAR's revenue, ETH 14%, ZEC 14%. Stablecoin-to-stablecoin swaps are 31% of volume but 11% of revenue, at 1.3 bps.
- **What changed in November** (1Click, 16–29 Oct against 1–10 Nov; log 34): NEAR's take fell from 4.6 to 2.9 bps while volume rose ($32M to $38M a day). Most of the gap is one flow: Trust Wallet routed $27M of swaps (99% ZEC) at 20 bps between 23 and 28 October, 26% of NEAR's 1Click revenue in the second half of October, then stopped. Without Trust Wallet the take went from 3.7 to 2.9 bps. ZEC fell from 28% to 11% of volume and from 48% to 10% of NEAR's revenue. What held: NEAR's revenue from swaps without an integrator, its own front-end and direct users ($5.2k then $5.4k a day), now 49% of NEAR's 1Click revenue. The fall in late-October pricing was one integrator's burst, not a broad repricing; the part NEAR controls did not fall.

### 8. The track's own hypothesis: does usage lead the price?

The track suggests testing whether cross-chain volume through NEAR Intents is a better signal of real usage than the token price. Weekly data, 98 complete weeks, NEAR's price taken net of BTC (beta 1.45) so that a market-wide move does not count as a NEAR signal (log 33, `make leadlag`):

- **Usage does not lead the price, and the price does not lead usage.** Intents volume, L1 transactions and L1 active accounts, lags of one to four weeks, both directions: 0 of 24 correlations are significant after Holm's correction. The strongest before correction is r = +0.15, p = 0.15 before correction (L1 transactions, 1-week lag).
- **The two kinds of usage have parted ways.** Over the last 30 days against the same window a year earlier, Intents volume is +48% while L1 transactions are -85% and L1 active accounts -76%. Counting transactions says NEAR is shrinking; counting settled volume says it is growing.
- **What tracks NEAR's revenue.** Weekly changes in captured revenue since March correlate 0.45 with Intents volume, 0.52 with L1 transactions, -0.03 with active accounts and 0.11 with the BTC-adjusted price (36 weeks).
- **Reading.** Week to week, NEAR's revenue moves with both Intents volume and L1 transactions (the two move together within a week), but over a year they part ways and only Intents volume grew with revenue. Neither says anything about next month's price. That fits the valuation finding: the market does not price NEAR on this revenue.

### 9. Public claims, checked

33 statements made in public about NEAR's revenue, buybacks, issuance and usage, by NEAR, analysts, treasury companies and the press, each tested on the committed snapshots at the claim's own date where it has one (rendered by `make docs` from the same outputs; `public_claims()` in `src/figures.py`). 18 survive, 6 are close (within about 10%, or within definitions), 9 do not hold as stated. The pattern: volume and usage figures quoted in public are accurate; claims about value reaching holders (deflation, NEAR staked or permanently removed, buyback totals on NEAR's own series, price reflexivity) are the ones that fail. NEAR's own fee schedule fails in the same place: the 20 bps that 1Click is meant to keep on integrator swaps is paid on a small part of that volume; custom deals are the norm.

| Claim | Source | What the data says | Verdict |
| --- | --- | --- | --- |
| "NEAR Intents has already directed revenue to over 1M in $NEAR buyback" | [Evolving NEAR Tokenomics, near.org, 2026-02-24](https://www.near.org/blog/evolving-near-tokenomics) | 1.05M NEAR ($1.73M) had reached the revenue wallets before 24 February | **Survives** |
| Acquired NEAR is "staked, locked, or otherwise removed from liquid circulation" | Evolving NEAR Tokenomics, near.org, 2026-02-24 | the three revenue wallets hold 4.29M NEAR, 0 of it staked or locked (NEAR RPC `view_account`, 2026-11-13); none is burned | **Not shown** |
| 1Click with an API key and no app fee: 20 bps, 1 bp on stablecoin and same-asset routes | [NEAR Intents docs, fees](https://docs.near-intents.org/resources/fees) | swaps without an integrator, last 30 days: 69% of cross-asset volume pays NEAR's wallets 20 bps or more, 79% of same-asset volume pays 1 bp | **Survives for most volume** |
| 1Click with app fees: a 50/50 split, at least 20 bps to 1Click (custom deals exist) | NEAR Intents docs, fees | swaps with an integrator, last 30 days: 13% of cross-asset volume pays NEAR 20 bps or more, 73% pays it nothing; average 3.5 bps | **The exception is the rule** |
| "About $177M of daily volume makes NEAR deflationary" | community DefiLlama Pro dashboard, widely quoted in 2026 (log 6) | assumes all gross fees buy NEAR; with the captured share, break-even is $639M/day at 4.9 bps | **Inflated** |
| "NEAR captures a growing share of fees" | revenue.near.org, read 2026-11-11 | 19% of gross fees all-time, 33% over the last 30 days; take 2.2 → 5.5 bps Aug to Oct, 3.9 in the week of 2 Nov | **Survives, but turned down in November** |
| "...feeding buybacks that permanently remove NEAR from circulation" | revenue.near.org, read 2026-11-11 | 47% of the NEAR captured sits in a DAO treasury with no on-chain commitment not to sell; nothing is burned; supply grows 2.1% a year net | **Not shown** |
| Revenue as NEAR reports it | revenue.near.org monthly revenue series | 21% above the NEAR its own three revenue wallets receive (Mar–Oct), while the wallet totals agree within 0.16% | **Unverified (gap unexplained)** |
| Share of emissions offset, as NEAR reports it | revenue.near.org, read 2026-11-11 | 16.3% on NEAR's count, 14.8% rebuilt from the wallets and archival supply, Feb–Oct | **Survives (definitions differ)** |
| "Buybacks are still real": about $1.9M of Intents-funded purchases over 30 days | Sal Ternullo (SVRN) on Bankless, via [Stocktwits, 2026-10-06](https://stocktwits.com/news-articles/markets/cryptocurrency/near-treasury-firm-ceo-says-buybacks-are-still-real-but-issuance-runs-six-times-higher/cZDteDIRBl3) | $1.86M reached the three revenue wallets over the 30 days to 6 Oct | **Survives** |
| Issuance runs about $13M over the same 30 days, "more than six times" buybacks | Sal Ternullo (SVRN) on Bankless, via Stocktwits, 2026-10-06 | 2.65M NEAR issued, $10.05M at daily prices: 5.4× the revenue captured | **Overstated (direction right)** |
| Bought NEAR is not burned; it sits in a "permanent capital vehicle" | Sal Ternullo (SVRN) on Bankless, via Stocktwits, 2026-10-06 | nothing is burned; 47% of captured NEAR is in the front-end fund's DAO treasury, the rest in the buyback wallet; no lock on either | **Survives** |
| At 1.6% issuance NEAR still issues about $8M a month; buybacks cover under a quarter | Sal Ternullo (SVRN) on Bankless, via Stocktwits, 2026-10-06 | $5.98M a month at today's price on today's supply; the last 30 days of captured revenue ($1.79M) would cover 30% | **Close (price-dependent)** |
| Staking yield falls from about 5.4% to about 3.5% under HSP-029 | Sal Ternullo (SVRN) on Bankless, via Stocktwits, 2026-10-06 | staker reward 5.4% today; scaled by 1.6/2.5, 3.5% | **Survives** |
| "HSP-029 avoids 11.8M NEAR of issuance over two years" | HSP-029 text on vote.dao; Unchained, 2026-11-03 | a linear ramp from 2.5% to 1.6% on today's supply avoids 11.8M NEAR over two years; it cannot start before 2027-02-14 | **Survives** |
| HSP-029 passed the House of Stake vote (closed 2026-11-02) | vote.dao proposal 29; The Defiant | 99.97% of veNEAR cast in favour; in timelock until 2026-11-16 | **Survives** |
| Cumulative fees above $52M; more than $8M captured for buybacks | Nansen NEAR Q3 2026, via [Altcoin Buzz, 2026-10-28](https://www.altcoinbuzz.io/near-intents-fees-buybacks-52-million) | fees $57.38M to 28 Oct (DefiLlama); captured $7.21M by then on the wallets, crossing $8M on 2026-11-12 | **Fees survive; $8M not on the wallets** |
| $6.68M of NEAR bought back as of 19 October | DefiLlama holders revenue, via Altcoin Buzz (2026-10-28) | $6.74M on DefiLlama, $6.65M rebuilt from the wallets | **Survives** |
| Lifetime fee capture about 16.4% (as of 6 October) | Nansen NEAR Q3 2026, via Altcoin Buzz | 19.1% of fees since the fee switch, 10.7% of all fees since launch | **Close (definitions)** |
| Fee capture about 28.4% over the last 30 days (6 October) | Nansen NEAR Q3 2026, via Altcoin Buzz | 24.6% rebuilt, 25.4% on DefiLlama | **Close, a little high** |
| About $2.7M of NEAR bought back from Intents revenue so far in Q4 | [AMBCrypto, 2026-11-12](https://ambcrypto.com/near-intents-fuels-2-7m-in-q4-buybacks-as-revenue-surges/), from BSC News | $2.75M reached the three revenue wallets from 1 October to 11 November, but only $1.85M the buyback multisig itself (the rest sits in the front-end fund) | **Survives, on all three wallets** |
| $8.68M of fees since 1 October, of which NEAR Intents kept $2.82M | AMBCrypto, 2026-11-12, from BSC News | $8.78M of gross fees on DefiLlama to 11 November; $2.75M reached NEAR's wallets | **Survives** |
| $3.07M of buybacks in Q3, per DefiLlama | AMBCrypto, 2026-11-12, from BSC News | DefiLlama's holders revenue is $3.07M; the wallets received $2.96M, of which $2.07M into the buyback multisig | **Close (DefiLlama's definition)** |
| Q3 2026 Intents volume about $10.4B | Nansen NEAR Q3 2026, via [Altcoin Buzz, 2026-11-02](https://www.altcoinbuzz.io/near-protocol-q3-2026-on-chain-activity-intents) | $9.79B on DefiLlama | **Close** |
| Q3: about 68M transactions, 739k a day, 79.3k daily active accounts, a peak of 1.21M on 27 September | Nansen NEAR Q3 2026, via Altcoin Buzz, 2026-11-02 | NearBlocks: 68.0M, 739k a day, 79.3k active, peak 1.22M on 27 Sep | **Survives** |
| Confidential Intents TVL about $160M at end-September, up 463% on the quarter | Nansen NEAR Q3 2026, via Altcoin Buzz, 2026-11-02 | Dune: $160.9M on 30 Sep, $28.6M on 30 Jun (+463%) | **Survives** |
| Intents volume above $32B | Ternullo on Bankless, 2026-10-06 | $32.66B cumulative on DefiLlama to 6 Oct | **Survives** |
| Over $20B of cumulative volume (3 June); about $32M of fees, a 0.16% take | [Crypto Briefing via KuCoin, 2026-06-03](https://www.kucoin.com/news/flash/near-intents-surpasses-20b-in-all-time-transaction-volume) | $20.16B and $34.58M of gross fees on DefiLlama; NEAR itself kept 3.1 bps of volume in the month to 3 June | **Survives (gross fees, not NEAR's take)** |
| Over $18B of cumulative volume, about $5B of it since the end of February | [Bankless, 2026-05-15](https://www.bankless.com/read/nears-intents-and-ai-bets-fuel-revival), citing Dune | $18.71B to 15 May, $4.80B since 1 March (DefiLlama) | **Survives** |
| NEAR Intents is the largest cross-chain swap venue | near.org and Intents team framing | 58%–79% of cross-chain swap volume each month May–Oct (DefiLlama); 38% in November to date, behind THORChain | **Survives to October; not in November** |
| Staking ratio holds at about 46% | Bitwise Q3 2026 staking report, via Crypto Briefing | 45.0% of total supply staked (validators, NEAR RPC) | **Close** |
| Intents volume spikes coincide with NEAR rallies; the Intents flywheel reprices NEAR | Crypto Briefing (2026-06-03); Bankless, "NEAR's Intents and AI bets fuel revival" | 0 of 24 weekly lead-lag tests significant after Holm, NEAR net of BTC (REPORT section 8) | **Not shown** |
| Usage on NEAR is growing | recurring ecosystem framing | Intents volume +48% year on year over the last 30 days; L1 transactions -85% | **Intents yes, L1 no** |

### 10. The two questions NEAR did not answer, and what the data says

Both were asked on three channels (Discord support ticket, near.com support, the NearBuilders Telegram) without an answer from the team by the deadline. The data narrows each to one testable hypothesis (`make open-questions`, `open_questions.json`, log 42).

**H-A. Confidential swaps pay NEAR about 7.6 bps, and it lands in the buyback multisig.** Run per wallet instead of on total revenue, the weekly fit splits cleanly (13 weeks, Aug–Oct):
- the **buyback multisig** follows confidential volume (correlation 0.97, against 0.19 with public volume): **7.6 bps** on confidential volume (bootstrap 90% interval 7.0–8.8, leaving out any one week 7.4–8.1, 5.3 on week-to-week changes) and 0.7 bps on public volume;
- the **front-end fund** adds 3.4 bps in levels but 0.3 on week-to-week changes: a shared trend, not a fee on confidential swaps.

So the 11 bps of the total-revenue fit was 7.6 bps of confidential fee plus a front-end trend, and the confidential rate sits where NEAR's Dune fee table puts it (7.4 bps). *What would confirm it:* NEAR publishing the confidential rate, or a confidential swap's fee transfer to `buybacks.multisignature.near` read on chain. *What would refute it:* a published rate outside 5–9 bps.

**H-B. Most of the gap between NEAR's revenue series and its wallets is quote-improvement revenue that does not reach the three wallets.** NEAR's dashboard splits what it captures into front-end fees, B2B partner fees and quote improvement (its half of execution better than quoted), for four windows. Its revenue series is that capture times gross fees (they agree to the dollar over all time). Against what the three wallets received over the same windows:

| Window | Reported over wallets | Without quote improvement |
| --- | --- | --- |
| last 7 days | +6% | +-5.6% |
| last 30 days | +9% | -2.9% |
| year to date | +18% | +4.5% |
| all time | +20% | +8.2% |

Quote improvement is 11% of NEAR's reported revenue ($1.18M this year). Taking it out brings the series within a few percent of the wallets on every window longer than a week; what remains is timing (sweeps lag fees by days) and, all time, the 2025 USDC period. *Reading:* about a tenth of the revenue NEAR reports never reaches the wallets that buy NEAR; the offset that matters for supply is the wallet-based 14.8%, not 16.3%. *What would confirm it:* the account that receives the protocol's quote-improvement share, or NEAR stating that its revenue series counts it. *What would refute it:* quote-improvement fees arriving in one of the three wallets.

*Followed on-chain* (NEAR's BigQuery dataset, queries in [`sql/revenue_pipeline.sql`](sql/revenue_pipeline.sql), log 49). Every NEAR the buyback multisig and the front-end fund received from `intents.near` since August arrived through a `native_withdraw` intent: 1.10M and 0.49M NEAR, within 0.5% of the wallet histories this audit rebuilds. About half of the buyback inflow comes from two accounts inside `intents.near` that collect fees in some 170 tokens and convert them to NEAR (751 and 320 withdrawals); the rest, and almost all of the front-end fund's, comes from about 2,350 accounts that each withdrew once. On 13 November the three collecting accounts held about $14k of unconverted fees, under 1% of a month's revenue, so fees waiting to be converted do not explain the gap. Tracing the swaps further shows why NEAR's half of quote improvement cannot be found on the public chain. The account through which 1Click swaps settle (`51e8f94d…`) held about $136M of tokens inside `intents.near` on 13 November, the size of NEAR's confidential TVL ($137.9M on 12 November): it is the confidential pool's account, the bridge to the private shard. Its transfers go to solvers and users, never to fee recipients, so the fee arithmetic of these swaps (the confidential fee, and very likely the protocol's half of quote improvement) happens inside the private shard, and only NEAR that is converted and withdrawn to the three wallets becomes visible. The other recurring recipients were a market maker and the protocol fee collector (`7066024d…`, $0.4k). H-B remains the best explanation, not a proof; NEAR naming the account would settle it.

## Bull case and bear case

**Bull.** Confidential swaps are a product NEAR monetises better than public swaps (about 5.5–11 bps against 1–3), and they reached 41% of volume. If a part of that use outlives the airdrop, the take rate stays well above its old level. The take rate is a lever NEAR can still pull: it doubled in two months and the sensitivity table shows that 8–15 bps with 2–4x today's volume reaches break-even. A single deal with the largest integrator, which now pays NEAR almost nothing, would add more revenue than any volume growth. The revenue is clean, reconciles to the chain and is not being sold.

**Bear.** The rise came mostly from confidential swaps whose growth coincides with an airdrop (Drop 1 cost about three quarters of the revenue uplift over its two best months), with each parked dollar swapped every 2–3 days. On 1Click, it came from pricing on flows NEAR controls (users without integrator, ZEC), the flows most exposed to competition. Integrators own the users, users do not stay, and half the 1Click revenue rides on one asset. If the take falls back to its May–Aug level, buybacks offset a tenth of issuance. Nearly half of what is called "buyback" sits in a treasury with no commitment not to sell.

## What would change our mind

Kill criteria were registered before the analysis and are monitored live on the dashboard. They are tripwires on the quality of the revenue: each one, if it holds for 30 consecutive days, would make the picture worse than this report describes. What would change the conclusion in NEAR's favour is listed under the catalysts below.

| Criterion | Status, data to 2026-11-12 |
| --- | --- |
| 30-day revenue below 50% of its trailing 180-day average | Not triggered: 159% of the average |
| Buyback inflows stop for more than 14 days while fees continue | Not triggered: inflow yesterday |
| Top integrator above 60% of fees | **Triggered on 1Click** (SwapKit, 65–75% of app fees, all year), though SwapKit brings NEAR under 0.1% of its 1Click revenue. The criterion did not say whose fees; we report it as written. All-Intents measure pending. |
| *Added after the fact, reported separately:* confidential TVL back below its level on the NEAR@3.33 snapshot day ($71M) | Not triggered: $138M, but 26% below the peak |

The third result is a lesson as much as a finding: a kill criterion should measure the quantity the thesis depends on, NEAR's captured revenue, not a proxy.

## Dated predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv) (sha256 committed and checked by a test; Bitcoin timestamp in `PREDICTIONS.csv.ots`). P1 and P2 resolve on 2026-11-15, before judging starts; P3 on 2026-11-17; the rest by April 2027. `make predictions` resolves them from the data; results in [`predictions/RESULTS.md`](predictions/RESULTS.md).

## Catalysts to watch

- Whether the take rate holds above 5 bps through Q4: the first full week of November (3.9 bps) says it may not (prediction P1 resolves on 2026-11-15).
- HSP-029 leaving its timelock on 2026-11-16 (prediction P3), then the validator upgrade that starts the ramp.
- A revenue-sharing deal with SwapKit or other large integrators.
- An on-chain commitment (or a sale) by the front-end fund.
- ZEC flows: their share of NEAR's revenue, and whether Trust Wallet's deal lasts.
- Confidential TVL and NEAR's take once NEAR@3.33 rounds stop (further drops are "tba", per NEAR's moderators): the test of whether the take-rate jump is durable.

## Conviction and limits

- **High** on "real" and on "too small to offset issuance today": both follow from on-chain data and an identity.
- **Medium-low** on durability: the September jump is partly explained (confidential swaps account for a fifth to five sixths of it depending on the method, log 24, 32), and that channel grew under an incentive whose causal role is plausible but unproven. The fee NEAR earns on confidential swaps is estimated (about 5–11 bps), not published, and early November fell below every version of the fit.
- **Low** on end-2027 paths: the bootstrap can only replay the past, and the take rate is a policy choice.
- A walk-forward check of the simulation engine (log 21) shows it **overestimated** buyback capacity in 2026: realised outcomes fell below the 10th percentile in a third of 90-day forecasts. If anything, the 18% base case is too generous, which makes "net inflationary through 2027" a conservative conclusion.

Questions sent to the NEAR team (Discord ticket 2026-11-04, near.com support, then the NearBuilders Telegram on 2026-11-13; the support assistants pointed to the fee schedule, which publishes no confidential rate, and had no rule for the revenue series; no answer from the team by the submission deadline): the fee on confidential intents and who receives it, further NEAR@3.33 drops (answer: "tba"), and whether the front-end fund's NEAR is ever sold. One more is open since 2026-11-11: why NEAR's revenue series is about 21% above what the three wallets receive. Confidential TVL now has a public source (revenue.near.org).

## Reproduce

```bash
pip install -r requirements.txt
make check-clean   # every offline step on the committed snapshots, the tests, and a comparison of every output with the committed one
make verify        # renders README/REPORT/FAQ from the outputs and re-checks the 15 findings
make refresh       # optional, with network: fresh snapshots, then everything again
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
