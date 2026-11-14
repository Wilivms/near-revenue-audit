<!-- Generated from docs/templates/THESIS.md by `make docs`; edit the template, not this file. -->
# THESIS

*The one-page form the track asks for: the claim, the evidence for it, the evidence against it, what would change our mind, and what could not be computed. Data to 2026-11-12; every figure is rendered from `data/processed/` by `make docs`. The full argument is in [`REPORT.md`](REPORT.md).*

## The claim

NEAR Intents' protocol revenue is real and has grown, but in its current form it does not support NEAR's value through supply: buybacks offset about a sixth of issuance, the recent jump was partly bought with an incentive and is already easing, and the market prices NEAR on something other than this revenue. Holding NEAR is a bet on Intents growing several times over at a higher take, not on scarcity.

**Verdict.** The fee-capture case does not hold at today's price, and is unlikely to within 12 months (7% chance of a deflationary 2027 in the base case, 26% with 4x the volume): market cap is 205x captured revenue against 41x for supply to stop growing. Constructive only if two of these hold for a quarter: the take stays at 5 bps or more after the airdrop (3.9 now), revenue covers half of issuance (21% now), or bought NEAR is burned or locked by a rule (none today; 47% sits in a fund whose policy one Admin vote can change). A thesis on public data, not personal advice.

## Evidence for

- **It is real.** Three independent indexers agree: NearBlocks, NEAR's BigQuery dataset (to the last digit on the NEAR the wallets received) and NEAR's own dashboard. Rebuilt from the chain, revenue matches DefiLlama within 0.8% ($8.09M since the 2026-02-23 fee switch) and NEAR's own dashboard within 0.16% on the NEAR its three revenue wallets received. ($8,087,549 vs $8,149,355; `make revenue`, `make official`)
- **In one line.** Of every $100 swapped through NEAR Intents (2026-10-14 to 2026-11-12), users pay $0.159 in fees, NEAR's wallets receive $0.049, and the network issues $0.238 of new NEAR: revenue covers 21% of issuance.
- **It is too small for the supply story.** Feb–Oct 2026: 3.53M NEAR captured against 23.9M issued, 14.8% (16.3% on NEAR's own count). Supply still grows 2.1% a year net. (`make supply`)
- **The gap is structural.** Supply stops growing only when market cap is below 41x annual captured revenue (64x after the approved HSP-029 cut); it is 205x (market cap on 2026-11-13 ÷ wallet revenue 2026-10-14 to 2026-11-12, annualised). Break-even needs about $639M of daily volume at today's take, against about $127M. (`make montecarlo`)
- **2027 does not change it in the base case.** Median 18% of 2027 issuance offset (5–75%), 7% chance of a deflationary 2027; 20% with the issuance cut. The engine was too optimistic in its 2026 backtest. (`make montecarlo backtest`)
- **The jump was partly bought.** NEAR's take went from 2.2 to 5.5 bps between August and October; confidential swaps, which grew under the NEAR@3.33 airdrop, explain 22% to 84% of it. Drop 1 cost $1.39M, 74% of the revenue uplift. (`make confidential`)
- **It is easing.** The fit missed its first unseen week ($355k vs $475k–$901k); the take was 3.9 bps in the week of 2 November on three sources; confidential TVL is 26% below its peak. (`make confidential official`)
- **NEAR does not own the customer.** On 1Click, integrators keep about 92% of the fee pool; SwapKit takes 75% of app fees and sends NEAR under 0.1% of its revenue. (`make swaps` outputs, to 2026-11-12)
- **Other flows dwarf the buyback.** US spot NEAR ETFs had taken in a net $80.5M by 5 November, ten times the $8.09M NEAR has captured since the fee switch, and lost a net $5.74M in November to 12 November, against $0.55M captured from 1 to 11 November (SoSoValue, via [ChainCatcher](https://www.chaincatcher.com/en/article/2302233) and [AMBCrypto](https://ambcrypto.com/near-intents-fuels-2-7m-in-q4-buybacks-as-revenue-surges/); outside data, not rebuilt here). Price is set by flows several times larger than revenue.
- **The market agrees it is priced on something else.** Peers whose holders share revenue trade at a median 20x holders revenue; NEAR at 208x on the same definition (DefiLlama holders revenue, last 30 days annualised, so slightly different from the 205x on the wallets); at the peer median its revenue supports about $0.33 a NEAR, against $3.42. Usage counts can mislead: from late October to early November transactions to `intents.near` changed +85% while captured revenue changed -18%, and 99.9% of the increase is the contract signing its own transactions (`make bigquery`). Usage does not lead the price: 0 of 24 lead-lag tests significant after Holm. (`make comps leadlag`)

## Evidence against

- **The take rate is a lever.** It doubled in two months (2.2 to 5.5 bps, month on month); at 8–15 bps with 2–4× today's volume, buybacks would cover issuance (sensitivity table in `make montecarlo`).
- **Confidential swaps do pay NEAR more**, in every method (5.5–11 bps against 1–3). If a part of that use outlives the airdrop, the take stays well above its May–Aug level (2.4 bps).
- **The part NEAR controls held up in November.** On 1Click, NEAR's revenue from swaps without an integrator was $5.2k a day in late October and $5.4k in early November; the fall came from one integrator's burst ending (Trust Wallet). 
- **NEAR's own front-end is growing its share.** NEAR's dashboard shows capture by front-end fees rising from 12% of gross fees all-time to 19% over the last 30 days: the flows NEAR controls are the ones that grew.
- **NEAR's own revenue series is higher.** It runs 21% above the wallets; if that revenue is real and retired, the offset is 16.3% rather than 14.8%. It does not change the order of magnitude.
- **Issuance is being cut.** HSP-029 passed with 99.97% of veNEAR cast; fully phased in, it lowers the break-even multiple's bar from 41x to 64x.
- **It survived a freeze and an exploit, at the large integrators' expense.** 1Click stopped for 3.7 hours on 1 October, about $2,014 of NEAR revenue, and users and NEAR's revenue stayed within their usual range in the two weeks after. But the 25 largest integrators' volume fell −39%, more than at any of 21 placebo dates, and only 3 of the 10 that cut back had returned by November. (`make incident`)
- **The market pays for incentives, not for supply cuts.** Of seven NEAR events tested against a placebo distribution, only the NEAR@3.33 airdrop snapshot moved the price (+26% against Bitcoin in three days); the issuance halving left it flat and HSP-029's approval was followed by −16%. (`make events`)
- **Users pay about 59 bps a swap on 1Click; NEAR keeps 6.4% of it** (43 bps go to integrators, 12 to solvers and networks). (`make swap-cost`)
- **NEAR's revenue grows without more people signing NEAR transactions.** About 52 heavy signers send 79% of transactions; human-scale signers are −69% on a year and lead nothing (0 of 24 tests). (`make signers`)
- **The jump is dated by the data.** The one break in the weekly take falls in the week ending 20 Sep 2026 (90%: 30 Aug 2026 to 27 Sep 2026), the airdrop snapshot's week. (`make deeper`)
- **Buybacks justify 2.0% to 16.2% of the market cap**, and none of the levers tested, even combined (a 20 bps fee, twice the volume, the issuance cut), lifts coverage of issuance above 72%. (`make deeper`)
- **The buyback is a policy, not a mechanism.** Nothing is burned or locked; the multisig needs 2 of 4 keys, and the front-end fund, holding 2.02M NEAR, can change its own policy with one Admin vote and has paid $2.45M in stablecoins to `aurora…` accounts (payments to an operating partner would fit). Multisigs and DAOs are normal; what a holder can count on is the policy, not a rule. (`make control`)
- **The treasury's 30.17M NEAR moved this year was staked, not sold** (9x the NEAR bought back since February): not selling pressure now, a stock its holders control. (`make treasury`)
- **Users do not visibly shop on fees.** Across 32 large 1Click integrators, the fee charged and the volume growth are unrelated (Spearman +0.08); the highest-fee ones grew most. The constraint on NEAR's take is the integrators' choice of router, not the users. (`make elasticity`)
- **The price implies far more revenue than exists.** At 15% and 3% growth it needs 24x today's captured revenue, or 83% a year of growth for five years. (`make implied`)
- **Competition is not compressing the price yet.** In 5 live quote rounds (48 identical swaps asked of 1Click, Relay, Across and LI.FI within the same minute, five corridors, about $1k and $20k), 1Click paid the user the most in 52%, median +0.1 bps from the best alternative, fees included: ahead on native BTC (+8.5 bps), level on L2 stablecoins and EVM swaps, behind on Ethereum to L2 (−1.2 bps) and Solana (+4.5 bps). NEAR's take is inside that price; where 1Click trails, the gap is about the size of that take. (`make quotes`)
- **Intents volume is growing** (+48% over the last 30 days against a year earlier) while L1 activity falls (-85% transactions): the part of NEAR that earns is the part that grows.

## What would change our mind

- **Toward the bull case:** the take holding above 5 bps through Q4 after the incentive (prediction P1 says it will not in early November; P5 says it stays above the May–Aug level); a revenue-sharing deal with SwapKit or another large integrator; an on-chain commitment by the front-end fund not to sell; daily volume several times higher at a stable take.
- **Toward a worse picture** (the pre-registered kill criteria, live on the dashboard): 30-day revenue below half its 180-day average (now 159%); buyback inflows stopping for 14 days while fees continue; one integrator above 60% of fees (triggered on 1Click, where SwapKit brings NEAR under 0.1% of its revenue).
- **Dated predictions** frozen on 2026-11-11 (`predictions/`), two resolving before judging.

## What could not be computed, and why

- **The fee on confidential swaps.** Not published, and not answered on three channels (NEAR Discord support, near.com support, the NearBuilders Telegram). Our hypothesis from the data (REPORT section 10): about **7.6 bps**, landing in the buyback multisig (interval 7.0–8.8; 5.3 on week-to-week changes), in line with NEAR's Dune fee table (7.4).
- **Where NEAR's extra 21% of reported revenue goes.** Not answered either. Our hypothesis (REPORT section 10): mostly **quote-improvement revenue** (11% of what NEAR reports), which does not reach the three wallets; without it the series is within 4.5% of the wallets this year and -2.9% over the last 30 days.
- **Confidential swaps by integrator or asset.** The Explorer API shows only 1Click (public) swaps; Dune's asset tables could not be read consistently (log 26).
- **Whether NEAR@3.33 caused the growth.** The timing fits; there is no control group, and near.com shipped other products over the same months.
