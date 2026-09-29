# Smart bots · how the final settings were chosen

Four rounds of the test (research/smart.py, commits 49e7fa8 → 2b26cb0). Every variant below is one bot with different brain settings.
Rule, fixed before looking: per bot, the highest Sharpe on 2010-2019 (in-sample); a variant within 0.05 of it with a max drop at least 5 points smaller wins instead.
The variants that remove a part of the brain (plain, no_regime, no_score, no_selfcheck) could not be picked. 2020-now was only looked at after the pick.

Picked: adaptive = hold_stress · trend = lite · breakout = light_notrail · momentum = lite_score60 · pullback = neutral_full

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| adaptive · smart | +8% | 0.89 | -15% | 53% | -0% | 0.03 | -11% | 34% |
| adaptive · plain | +23% | 1.10 | -27% | 99% | +28% | 0.92 | -39% | 98% |
| adaptive · no_regime | +8% | 0.80 | -15% | 70% | +1% | 0.12 | -13% | 62% |
| adaptive · no_score | +8% | 0.91 | -15% | 54% | -0% | 0.02 | -13% | 37% |
| adaptive · no_selfcheck | +10% | 0.96 | -14% | 63% | -0% | -0.02 | -10% | 32% |
| adaptive · score_m10 | +8% | 0.90 | -15% | 54% | -0% | 0.02 | -11% | 35% |
| adaptive · score_p10 | +7% | 0.87 | -15% | 51% | +2% | 0.31 | -13% | 46% |
| adaptive · atr_m | +6% | 0.74 | -14% | 52% | -1% | -0.03 | -14% | 37% |
| adaptive · atr_p | +8% | 0.90 | -14% | 56% | -0% | -0.05 | -10% | 30% |
| adaptive · size_full | +8% | 0.88 | -16% | 57% | +0% | 0.05 | -12% | 38% |
| adaptive · hold_stress | +9% | 0.95 | -16% | 59% | +0% | 0.05 | -12% | 37% |
| adaptive · no_trail | +7% | 0.66 | -16% | 63% | +0% | 0.06 | -18% | 40% |
| adaptive · trail_wide | +8% | 0.80 | -17% | 62% | +2% | 0.30 | -16% | 45% |
| adaptive · neutral_full | +10% | 0.94 | -15% | 69% | +1% | 0.16 | -14% | 47% |
| adaptive · stress_strict | +9% | 0.95 | -16% | 59% | +2% | 0.28 | -14% | 52% |
| adaptive · light | +10% | 0.83 | -18% | 76% | -0% | 0.06 | -27% | 65% |
| adaptive · light_notrail | +12% | 0.92 | -22% | 82% | +3% | 0.27 | -25% | 77% |
| adaptive · lite | +8% | 0.69 | -21% | 74% | +6% | 0.50 | -19% | 67% |
| adaptive · lite_bear_exit | +7% | 0.61 | -21% | 71% | +9% | 0.69 | -22% | 60% |
| adaptive · lite_trail | +10% | 0.90 | -14% | 75% | +1% | 0.17 | -18% | 54% |
| adaptive · lite_score60 | +7% | 0.65 | -21% | 73% | +6% | 0.50 | -19% | 67% |
| adaptive · lite_nocap | +7% | 0.64 | -23% | 73% | +11% | 0.74 | -19% | 64% |
| adaptive · lite_novol | +9% | 0.75 | -18% | 75% | +7% | 0.56 | -22% | 61% |
| adaptive · lite_bigrisk | +8% | 0.69 | -21% | 74% | +6% | 0.50 | -19% | 67% |
| adaptive · lite_free | +7% | 0.63 | -22% | 75% | +11% | 0.74 | -19% | 65% |
| trend · smart | +5% | 0.64 | -12% | 52% | +1% | 0.18 | -12% | 35% |
| trend · plain | +22% | 1.21 | -27% | 99% | +32% | 1.08 | -36% | 98% |
| trend · no_regime | +9% | 1.03 | -12% | 68% | +5% | 0.50 | -12% | 61% |
| trend · no_score | +6% | 0.66 | -14% | 60% | +3% | 0.36 | -17% | 47% |
| trend · no_selfcheck | +4% | 0.53 | -14% | 51% | +3% | 0.41 | -13% | 40% |
| trend · score_m10 | +5% | 0.67 | -14% | 54% | +3% | 0.38 | -15% | 43% |
| trend · score_p10 | +4% | 0.59 | -14% | 48% | +2% | 0.28 | -11% | 34% |
| trend · atr_m | +5% | 0.66 | -12% | 54% | +1% | 0.23 | -15% | 40% |
| trend · atr_p | +5% | 0.66 | -13% | 51% | +4% | 0.54 | -12% | 42% |
| trend · size_full | +7% | 0.72 | -14% | 66% | -0% | -0.02 | -15% | 39% |
| trend · hold_stress | +5% | 0.62 | -13% | 52% | +3% | 0.40 | -12% | 42% |
| trend · no_trail | +6% | 0.69 | -12% | 55% | +9% | 0.93 | -12% | 46% |
| trend · trail_wide | +6% | 0.69 | -14% | 53% | +4% | 0.53 | -12% | 46% |
| trend · neutral_full | +5% | 0.64 | -12% | 52% | +1% | 0.18 | -12% | 35% |
| trend · stress_strict | +5% | 0.64 | -13% | 52% | +2% | 0.29 | -12% | 42% |
| trend · light | +7% | 0.71 | -15% | 65% | +2% | 0.23 | -15% | 46% |
| trend · light_notrail | +8% | 0.76 | -14% | 70% | +9% | 0.82 | -14% | 52% |
| trend · lite | +12% | 1.01 | -14% | 84% | +9% | 0.71 | -19% | 65% |
| trend · lite_bear_exit | +9% | 0.82 | -15% | 76% | +3% | 0.31 | -25% | 54% |
| trend · lite_trail | +10% | 0.96 | -15% | 75% | +4% | 0.40 | -21% | 57% |
| trend · lite_score60 | +12% | 1.01 | -13% | 81% | +9% | 0.70 | -18% | 73% |
| trend · lite_nocap | +12% | 1.00 | -15% | 83% | +5% | 0.49 | -19% | 58% |
| trend · lite_novol | +10% | 0.85 | -14% | 83% | +7% | 0.56 | -18% | 72% |
| trend · lite_bigrisk | +12% | 1.01 | -14% | 84% | +9% | 0.72 | -19% | 65% |
| trend · lite_free | +12% | 0.99 | -16% | 85% | +6% | 0.52 | -20% | 61% |
| breakout · smart | +3% | 0.42 | -15% | 46% | +4% | 0.58 | -10% | 37% |
| breakout · plain | +12% | 0.74 | -27% | 98% | +22% | 0.81 | -34% | 97% |
| breakout · no_regime | +3% | 0.43 | -16% | 60% | +5% | 0.55 | -13% | 53% |
| breakout · no_score | +3% | 0.47 | -15% | 48% | +4% | 0.54 | -11% | 39% |
| breakout · no_selfcheck | +2% | 0.33 | -18% | 47% | +4% | 0.59 | -8% | 35% |
| breakout · score_m10 | +3% | 0.48 | -17% | 46% | +4% | 0.55 | -10% | 36% |
| breakout · score_p10 | +4% | 0.52 | -15% | 50% | +2% | 0.31 | -9% | 28% |
| breakout · atr_m | +2% | 0.27 | -15% | 40% | +1% | 0.22 | -12% | 31% |
| breakout · atr_p | +3% | 0.41 | -14% | 44% | +3% | 0.45 | -9% | 31% |
| breakout · size_full | +3% | 0.46 | -17% | 51% | +5% | 0.64 | -11% | 43% |
| breakout · hold_stress | +3% | 0.42 | -15% | 46% | +4% | 0.59 | -10% | 37% |
| breakout · no_trail | +3% | 0.34 | -16% | 53% | +2% | 0.24 | -11% | 36% |
| breakout · trail_wide | +3% | 0.43 | -18% | 48% | +2% | 0.35 | -13% | 35% |
| breakout · neutral_full | +3% | 0.37 | -17% | 54% | +4% | 0.55 | -10% | 41% |
| breakout · stress_strict | +2% | 0.30 | -15% | 42% | +4% | 0.59 | -10% | 38% |
| breakout · light | +3% | 0.32 | -20% | 63% | +7% | 0.65 | -15% | 57% |
| breakout · light_notrail | +7% | 0.64 | -15% | 71% | +6% | 0.55 | -15% | 54% |
| breakout · lite | +4% | 0.41 | -20% | 61% | +8% | 0.58 | -16% | 64% |
| breakout · lite_bear_exit | +0% | 0.05 | -23% | 50% | +7% | 0.67 | -14% | 54% |
| breakout · lite_trail | +5% | 0.50 | -21% | 66% | +3% | 0.36 | -14% | 44% |
| breakout · lite_score60 | +3% | 0.38 | -21% | 54% | +6% | 0.49 | -17% | 63% |
| breakout · lite_nocap | +4% | 0.43 | -18% | 62% | +9% | 0.61 | -19% | 66% |
| breakout · lite_novol | +5% | 0.51 | -17% | 67% | +9% | 0.65 | -19% | 66% |
| breakout · lite_bigrisk | +4% | 0.41 | -20% | 61% | +8% | 0.58 | -16% | 64% |
| breakout · lite_free | +4% | 0.43 | -18% | 62% | +10% | 0.64 | -19% | 67% |
| momentum · smart | +5% | 0.57 | -16% | 57% | -0% | -0.02 | -16% | 33% |
| momentum · plain | +17% | 0.86 | -33% | 99% | +42% | 1.21 | -37% | 99% |
| momentum · no_regime | +5% | 0.49 | -15% | 65% | +3% | 0.31 | -21% | 61% |
| momentum · no_score | +5% | 0.50 | -16% | 59% | -0% | -0.00 | -18% | 39% |
| momentum · no_selfcheck | +3% | 0.36 | -16% | 53% | +2% | 0.29 | -13% | 41% |
| momentum · score_m10 | +4% | 0.49 | -16% | 55% | -0% | -0.02 | -16% | 35% |
| momentum · score_p10 | +4% | 0.49 | -16% | 53% | +0% | 0.08 | -16% | 36% |
| momentum · atr_m | +4% | 0.47 | -15% | 58% | +2% | 0.22 | -18% | 37% |
| momentum · atr_p | +6% | 0.61 | -16% | 57% | +1% | 0.16 | -16% | 38% |
| momentum · size_full | +6% | 0.57 | -17% | 62% | +0% | 0.07 | -18% | 42% |
| momentum · hold_stress | +4% | 0.43 | -19% | 56% | +1% | 0.17 | -17% | 37% |
| momentum · no_trail | +9% | 0.78 | -14% | 60% | +6% | 0.61 | -18% | 46% |
| momentum · trail_wide | +9% | 0.81 | -14% | 61% | +4% | 0.44 | -19% | 47% |
| momentum · neutral_full | +6% | 0.64 | -16% | 61% | -1% | -0.04 | -17% | 43% |
| momentum · stress_strict | +4% | 0.45 | -16% | 54% | +1% | 0.14 | -17% | 38% |
| momentum · light | +7% | 0.60 | -23% | 72% | +4% | 0.40 | -21% | 65% |
| momentum · light_notrail | +11% | 0.88 | -20% | 68% | +6% | 0.46 | -30% | 69% |
| momentum · lite | +13% | 0.94 | -19% | 81% | +9% | 0.59 | -23% | 65% |
| momentum · lite_bear_exit | +12% | 0.87 | -19% | 75% | +2% | 0.24 | -20% | 62% |
| momentum · lite_trail | +4% | 0.48 | -19% | 62% | +3% | 0.30 | -20% | 65% |
| momentum · lite_score60 | +13% | 0.94 | -19% | 81% | +9% | 0.59 | -23% | 64% |
| momentum · lite_nocap | +10% | 0.81 | -20% | 71% | +1% | 0.14 | -23% | 58% |
| momentum · lite_novol | +14% | 0.91 | -31% | 83% | +10% | 0.64 | -24% | 67% |
| momentum · lite_bigrisk | +13% | 0.94 | -19% | 81% | +9% | 0.59 | -23% | 65% |
| momentum · lite_free | +10% | 0.82 | -19% | 72% | +1% | 0.16 | -23% | 60% |
| pullback · smart | +5% | 0.62 | -13% | 56% | +5% | 0.67 | -17% | 44% |
| pullback · plain | +17% | 0.93 | -26% | 98% | +8% | 0.42 | -50% | 98% |
| pullback · no_regime | +10% | 0.88 | -13% | 82% | +4% | 0.47 | -17% | 56% |
| pullback · no_score | +4% | 0.51 | -14% | 57% | +5% | 0.57 | -17% | 47% |
| pullback · no_selfcheck | +5% | 0.65 | -14% | 56% | +4% | 0.52 | -18% | 41% |
| pullback · score_m10 | +4% | 0.53 | -13% | 56% | +5% | 0.57 | -17% | 45% |
| pullback · score_p10 | +4% | 0.55 | -13% | 58% | +4% | 0.58 | -16% | 40% |
| pullback · atr_m | +4% | 0.48 | -13% | 61% | +2% | 0.27 | -18% | 39% |
| pullback · atr_p | +4% | 0.55 | -12% | 59% | +5% | 0.65 | -15% | 44% |
| pullback · size_full | +5% | 0.59 | -15% | 60% | +7% | 0.72 | -18% | 51% |
| pullback · hold_stress | +5% | 0.59 | -13% | 57% | +4% | 0.52 | -16% | 45% |
| pullback · no_trail | +5% | 0.62 | -13% | 56% | +5% | 0.67 | -17% | 44% |
| pullback · trail_wide | +5% | 0.62 | -13% | 56% | +5% | 0.67 | -17% | 44% |
| pullback · neutral_full | +8% | 0.81 | -14% | 69% | +4% | 0.42 | -18% | 49% |
| pullback · stress_strict | +5% | 0.61 | -13% | 56% | +5% | 0.60 | -17% | 45% |
| pullback · light | +8% | 0.76 | -17% | 74% | +6% | 0.58 | -21% | 62% |
| pullback · light_notrail | +8% | 0.76 | -17% | 74% | +6% | 0.58 | -21% | 62% |
| pullback · lite | +6% | 0.64 | -17% | 72% | +2% | 0.24 | -23% | 53% |
| pullback · lite_bear_exit | +6% | 0.65 | -15% | 75% | +7% | 0.61 | -23% | 61% |
| pullback · lite_trail | +8% | 0.80 | -16% | 74% | +2% | 0.25 | -24% | 53% |
| pullback · lite_score60 | +7% | 0.73 | -16% | 73% | +3% | 0.34 | -25% | 55% |
| pullback · lite_nocap | +6% | 0.64 | -16% | 77% | +6% | 0.56 | -22% | 60% |
| pullback · lite_novol | +7% | 0.71 | -17% | 75% | +5% | 0.52 | -22% | 56% |
| pullback · lite_bigrisk | +6% | 0.64 | -17% | 72% | +2% | 0.24 | -23% | 53% |
| pullback · lite_free | +6% | 0.63 | -16% | 78% | +4% | 0.40 | -23% | 62% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.86 / 0.81 | -38% / -34% | | | | | |

