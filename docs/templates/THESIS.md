# THESIS

*The one-page form the track asks for: the claim, the evidence for it, the evidence against it, what would change our mind, and what could not be computed. Data to {{data_to}}; every figure is rendered from `data/processed/` by `make docs`. The full argument is in [`REPORT.md`](REPORT.md).*

## The claim

NEAR Intents' protocol revenue is real and has grown, but in its current form it does not support NEAR's value through supply: buybacks offset about a sixth of issuance, the recent jump was partly bought with an incentive and is already easing, and the market prices NEAR on something other than this revenue. Holding NEAR is a bet on Intents growing several times over at a higher take, not on scarcity.

## Evidence for

- **It is real.** Rebuilt from the chain, revenue matches DefiLlama within {{rev_gap}} ({{rev_rebuilt}} since the 2026-02-23 fee switch) and NEAR's own dashboard within {{wallets_gap}} on the NEAR its three revenue wallets received. ({{rev_rebuilt_exact}} vs {{rev_llama_exact}}; `make revenue`, `make official`)
- **It is too small for the supply story.** Feb–Oct 2026: {{captured_feb_oct}} NEAR captured against {{issued_feb_oct}} issued, {{offset_rebuilt}} ({{offset_official}} on NEAR's own count). Supply still grows {{net_growth}} a year net. (`make supply`)
- **The gap is structural.** Supply stops growing only when market cap is below {{breakeven_now}} annual captured revenue ({{breakeven_cut}} after the approved HSP-029 cut); it is {{near_captured_mult}}. Break-even needs about {{be_vol_now}} of daily volume at today's take, against about {{volume0}}. (`make montecarlo`)
- **2027 does not change it in the base case.** Median {{mc_base}} of 2027 issuance offset ({{mc_base_band}}), {{mc_base_p}} chance of a deflationary 2027; {{mc_cut}} with the issuance cut. The engine was too optimistic in its 2026 backtest. (`make montecarlo backtest`)
- **The jump was partly bought.** NEAR's take went from {{take_aug}} to {{take_oct}} bps between August and October; confidential swaps, which grew under the NEAR@3.33 airdrop, explain {{jump_fd}} to {{jump_levels}} of it. Drop 1 cost {{drop1_usd}}, {{drop1_over_uplift}} of the revenue uplift. (`make confidential`)
- **It is easing.** The fit missed its first unseen week ({{oos_actual}} vs {{oos_pred_fd}}–{{oos_pred}}); the take was {{take_last_week}} bps in the week of 2 November on three sources; confidential TVL is {{tvl_from_peak}} below its peak. (`make confidential official`)
- **NEAR does not own the customer.** On 1Click, integrators keep about {{oc_integrators_keep}} of the fee pool; SwapKit takes {{sk_fees}} of app fees and sends NEAR {{sk_near}} of its revenue. (`make swaps` outputs, to {{oc_to}})
- **The market agrees it is priced on something else.** Peers whose holders share revenue trade at a median {{peers_median}} holders revenue; NEAR at {{near_holders_mult}}. Usage does not lead the price: {{ll_sig}} of {{ll_tests}} lead-lag tests significant after Holm. (`make comps leadlag`)

## Evidence against

- **The take rate is a lever.** It more than doubled in two months; at 8–15 bps with 2–4× today's volume, buybacks would cover issuance (sensitivity table in `make montecarlo`).
- **Confidential swaps do pay NEAR more**, in every method ({{premium_range}} bps against {{public_range}}). If a part of that use outlives the airdrop, the take stays well above its May–Aug level ({{take_mayaug}} bps).
- **The part NEAR controls held up in November.** On 1Click, NEAR's revenue from swaps without an integrator was {{noref_day_oct}} a day in late October and {{noref_day_nov}} in early November; the fall came from one integrator's burst ending (Trust Wallet). 
- **NEAR's own front-end is growing its share.** NEAR's dashboard shows capture by front-end fees rising from {{cap_fe_all}} of gross fees all-time to {{cap_fe_d30}} over the last 30 days: the flows NEAR controls are the ones that grew.
- **NEAR's own revenue series is higher.** It runs {{series_over_wallets}} above the wallets; if that revenue is real and retired, the offset is {{offset_official}} rather than {{offset_rebuilt}}. It does not change the order of magnitude.
- **Issuance is being cut.** HSP-029 passed with {{hsp_for}} of veNEAR cast; fully phased in, it lowers the break-even multiple's bar from {{breakeven_now}} to {{breakeven_cut}}.
- **Intents volume is growing** ({{yoy_vol}} over the last 30 days against a year earlier) while L1 activity falls ({{yoy_txns}} transactions): the part of NEAR that earns is the part that grows.

## What would change our mind

- **Toward the bull case:** the take holding above 5 bps through Q4 after the incentive (prediction P1 says it will not in early November; P5 says it stays above the May–Aug level); a revenue-sharing deal with SwapKit or another large integrator; an on-chain commitment by the front-end fund not to sell; daily volume several times higher at a stable take.
- **Toward a worse picture** (the pre-registered kill criteria, live on the dashboard): 30-day revenue below half its 180-day average (now {{kill1}}); buyback inflows stopping for 14 days while fees continue; one integrator above 60% of fees (triggered on 1Click, where SwapKit brings NEAR 1% of its revenue).
- **Dated predictions** frozen on 2026-11-11 (`predictions/`), two resolving before judging.

## What could not be computed, and why

- **The fee on confidential swaps.** Not published; estimated at {{premium_range}} bps by three methods. Asked to NEAR (Discord ticket, then near.com support); no answer yet.
- **Where NEAR's extra {{series_over_wallets}} of reported revenue goes.** Not visible in the three wallets NEAR lists, nor waiting in the fee collector. Asked to NEAR.
- **Confidential swaps by integrator or asset.** The Explorer API shows only 1Click (public) swaps; Dune's asset tables could not be read consistently (log 26).
- **The NEAR BigQuery dataset** suggested by the track was not used: it needs a billed Google Cloud project. NearBlocks' daily charts and the archival RPC cover the same L1 activity and supply questions without one.
- **Whether NEAR@3.33 caused the growth.** The timing fits; there is no control group, and near.com shipped other products over the same months.
