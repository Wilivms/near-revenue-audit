<!-- Generated from docs/templates/THESIS.md by `make docs`; edit the template, not this file. -->
# THESIS

*The one-page form the track asks for: the claim, the evidence for it, the evidence against it, what would change our mind, and what could not be computed. Data to 2026-11-12; every figure is rendered from `data/processed/` by `make docs`. The full argument is in [`REPORT.md`](REPORT.md).*

## The claim

NEAR Intents' protocol revenue is real and has grown, but in its current form it does not support NEAR's value through supply: buybacks offset about a sixth of issuance, the recent jump was partly bought with an incentive and is already easing, and the market prices NEAR on something other than this revenue. Holding NEAR is a bet on Intents growing several times over at a higher take, not on scarcity.

## Evidence for

- **It is real.** Three independent indexers agree: NearBlocks, NEAR's BigQuery dataset (to the last digit on the NEAR the wallets received) and NEAR's own dashboard. Rebuilt from the chain, revenue matches DefiLlama within 0.8% ($8.09M since the 2026-02-23 fee switch) and NEAR's own dashboard within 0.16% on the NEAR its three revenue wallets received. ($8,087,549 vs $8,149,355; `make revenue`, `make official`)
- **It is too small for the supply story.** Feb–Oct 2026: 3.53M NEAR captured against 23.9M issued, 14.8% (16.3% on NEAR's own count). Supply still grows 2.1% a year net. (`make supply`)
- **The gap is structural.** Supply stops growing only when market cap is below 41x annual captured revenue (64x after the approved HSP-029 cut); it is 205x (market cap on 2026-11-13 ÷ wallet revenue 2026-10-14 to 2026-11-12, annualised). Break-even needs about $639M of daily volume at today's take, against about $127M. (`make montecarlo`)
- **2027 does not change it in the base case.** Median 18% of 2027 issuance offset (5–75%), 7% chance of a deflationary 2027; 20% with the issuance cut. The engine was too optimistic in its 2026 backtest. (`make montecarlo backtest`)
- **The jump was partly bought.** NEAR's take went from 2.2 to 5.5 bps between August and October; confidential swaps, which grew under the NEAR@3.33 airdrop, explain 22% to 84% of it. Drop 1 cost $1.39M, 74% of the revenue uplift. (`make confidential`)
- **It is easing.** The fit missed its first unseen week ($355k vs $475k–$901k); the take was 3.9 bps in the week of 2 November on three sources; confidential TVL is 26% below its peak. (`make confidential official`)
- **NEAR does not own the customer.** On 1Click, integrators keep about 92% of the fee pool; SwapKit takes 75% of app fees and sends NEAR under 0.1% of its revenue. (`make swaps` outputs, to 2026-11-10)
- **The market agrees it is priced on something else.** Peers whose holders share revenue trade at a median 20x holders revenue; NEAR at 208x on the same definition (DefiLlama holders revenue, last 30 days annualised, so slightly different from the 205x on the wallets); at the peer median its revenue supports about $0.33 a NEAR, against $3.42. Usage does not lead the price: 0 of 24 lead-lag tests significant after Holm. (`make comps leadlag`)

## Evidence against

- **The take rate is a lever.** It more than doubled in two months; at 8–15 bps with 2–4× today's volume, buybacks would cover issuance (sensitivity table in `make montecarlo`).
- **Confidential swaps do pay NEAR more**, in every method (5.5–11 bps against 1–3). If a part of that use outlives the airdrop, the take stays well above its May–Aug level (2.4 bps).
- **The part NEAR controls held up in November.** On 1Click, NEAR's revenue from swaps without an integrator was $5.2k a day in late October and $5.4k in early November; the fall came from one integrator's burst ending (Trust Wallet). 
- **NEAR's own front-end is growing its share.** NEAR's dashboard shows capture by front-end fees rising from 12% of gross fees all-time to 19% over the last 30 days: the flows NEAR controls are the ones that grew.
- **NEAR's own revenue series is higher.** It runs 21% above the wallets; if that revenue is real and retired, the offset is 16.3% rather than 14.8%. It does not change the order of magnitude.
- **Issuance is being cut.** HSP-029 passed with 99.97% of veNEAR cast; fully phased in, it lowers the break-even multiple's bar from 41x to 64x.
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
