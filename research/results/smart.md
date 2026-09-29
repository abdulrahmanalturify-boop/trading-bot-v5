# Smart bots · period test

Run 2026-09-29 05:26 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 8 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **adaptive** · smart | -2% · -0.18 · -12% | +11% · 0.92 · -15% | +3% · 0.30 · -18% | +19% · 0.99 · -12% | +18% · 1.07 · -8% | -8% · -0.61 · -13% | +17% · 0.87 · -19% | +7% · 0.62 · -18% | +13% · 0.74 · -19% | +8% · 0.61 · -19% |
| adaptive · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| adaptive · no_regime | -18% · -1.31 · -40% | +14% · 0.94 · -18% | +7% · 0.58 · -19% | +6% · 0.37 · -25% | +17% · 1.05 · -9% | -17% · -1.21 · -19% | +2% · 0.22 · -14% | +11% · 0.77 · -19% | +1% · 0.14 · -27% | +4% · 0.34 · -40% |
| adaptive · no_score | -2% · -0.19 · -12% | +12% · 0.92 · -15% | +3% · 0.30 · -18% | +19% · 0.99 · -12% | +18% · 1.05 · -8% | -8% · -0.63 · -13% | +17% · 0.86 · -19% | +7% · 0.62 · -18% | +13% · 0.73 · -19% | +8% · 0.61 · -19% |
| adaptive · no_selfcheck | -2% · -0.18 · -12% | +11% · 0.92 · -15% | +4% · 0.40 · -15% | +21% · 1.06 · -13% | +18% · 1.07 · -8% | -8% · -0.59 · -15% | +19% · 0.93 · -14% | +8% · 0.67 · -15% | +14% · 0.79 · -21% | +9% · 0.66 · -21% |
| adaptive · score_m10 | -2% · -0.19 · -12% | +11% · 0.92 · -15% | +3% · 0.30 · -18% | +19% · 0.99 · -12% | +18% · 1.06 · -8% | -8% · -0.62 · -13% | +17% · 0.87 · -19% | +7% · 0.62 · -18% | +13% · 0.74 · -19% | +8% · 0.62 · -19% |
| adaptive · score_p10 | -2% · -0.24 · -12% | +12% · 0.96 · -15% | +3% · 0.30 · -18% | +18% · 0.99 · -12% | +18% · 1.07 · -8% | -8% · -0.60 · -13% | +17% · 0.87 · -19% | +7% · 0.64 · -18% | +13% · 0.74 · -19% | +8% · 0.62 · -19% |
| adaptive · first_choice | -5% · -0.54 · -18% | +15% · 1.14 · -15% | +6% · 0.60 · -18% | +18% · 0.92 · -11% | +4% · 0.34 · -13% | -12% · -1.39 · -14% | -0% · 0.02 · -18% | +10% · 0.89 · -20% | +1% · 0.14 · -22% | +5% · 0.49 · -22% |
| adaptive · risk_1 | -2% · -0.20 · -11% | +11% · 0.93 · -15% | +3% · 0.30 · -18% | +19% · 1.02 · -12% | +20% · 1.15 · -8% | -7% · -0.48 · -13% | +15% · 0.82 · -19% | +7% · 0.63 · -18% | +12% · 0.73 · -19% | +8% · 0.61 · -19% |
| |  | | | | | | | | | |
| **trend** · smart | -4% · -0.67 · -18% | +15% · 1.15 · -17% | +7% · 0.60 · -17% | +21% · 1.04 · -16% | +23% · 1.32 · -10% | -17% · -1.62 · -17% | +20% · 1.05 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.75 · -19% |
| trend · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| trend · no_regime | -14% · -0.80 · -40% | +10% · 0.70 · -21% | +7% · 0.58 · -19% | +17% · 0.74 · -23% | +13% · 0.84 · -11% | -19% · -1.30 · -22% | +24% · 1.18 · -17% | +9% · 0.65 · -21% | +13% · 0.73 · -25% | +8% · 0.52 · -40% |
| trend · no_score | -4% · -0.66 · -19% | +15% · 1.15 · -17% | +7% · 0.60 · -17% | +21% · 1.03 · -16% | +23% · 1.30 · -10% | -17% · -1.61 · -17% | +20% · 1.05 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.75 · -19% |
| trend · no_selfcheck | -4% · -0.64 · -16% | +16% · 1.17 · -15% | +7% · 0.60 · -17% | +25% · 1.20 · -16% | +16% · 0.94 · -10% | -15% · -1.36 · -17% | +20% · 1.05 · -16% | +11% · 0.89 · -17% | +14% · 0.79 · -21% | +11% · 0.76 · -21% |
| trend · score_m10 | -4% · -0.67 · -18% | +15% · 1.15 · -17% | +7% · 0.60 · -17% | +21% · 1.04 · -16% | +23% · 1.31 · -10% | -17% · -1.61 · -17% | +20% · 1.05 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.75 · -19% |
| trend · score_p10 | -4% · -0.67 · -18% | +15% · 1.15 · -17% | +7% · 0.60 · -17% | +21% · 1.04 · -16% | +23% · 1.32 · -10% | -17% · -1.62 · -17% | +20% · 1.05 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.75 · -19% |
| trend · first_choice | -4% · -0.42 · -17% | +12% · 0.99 · -15% | +6% · 0.55 · -13% | +11% · 0.61 · -17% | +15% · 0.86 · -13% | -9% · -1.08 · -14% | +7% · 0.55 · -19% | +9% · 0.77 · -16% | +6% · 0.46 · -20% | +7% · 0.56 · -20% |
| trend · risk_1 | -4% · -0.65 · -17% | +15% · 1.15 · -16% | +7% · 0.60 · -17% | +20% · 1.05 · -16% | +23% · 1.29 · -10% | -17% · -1.64 · -17% | +20% · 1.06 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.76 · -19% |
| |  | | | | | | | | | |
| **breakout** · smart | -4% · -0.58 · -15% | +8% · 0.75 · -12% | +2% · 0.24 · -20% | +22% · 1.09 · -14% | +17% · 1.00 · -11% | -14% · -1.28 · -17% | +11% · 0.74 · -19% | +5% · 0.50 · -20% | +9% · 0.61 · -22% | +5% · 0.49 · -22% |
| breakout · plain | -33% · -0.79 · -72% | +22% · 0.96 · -29% | +17% · 0.84 · -30% | +92% · 1.72 · -48% | +9% · 0.41 · -34% | -21% · -0.64 · -29% | +76% · 1.69 · -38% | +19% · 0.90 · -30% | +48% · 1.24 · -48% | +21% · 0.78 · -72% |
| breakout · no_regime | -11% · -0.65 · -36% | +7% · 0.54 · -20% | +8% · 0.65 · -19% | +13% · 0.75 · -23% | +25% · 1.29 · -9% | -12% · -0.67 · -21% | +21% · 1.11 · -20% | +8% · 0.59 · -20% | +14% · 0.81 · -23% | +8% · 0.55 · -36% |
| breakout · no_score | -4% · -0.58 · -15% | +7% · 0.73 · -12% | +2% · 0.23 · -20% | +22% · 1.08 · -14% | +17% · 1.01 · -11% | -14% · -1.27 · -17% | +11% · 0.75 · -19% | +5% · 0.49 · -20% | +9% · 0.61 · -22% | +5% · 0.48 · -22% |
| breakout · no_selfcheck | -4% · -0.57 · -15% | +8% · 0.78 · -11% | -1% · -0.04 · -20% | +6% · 0.53 · -11% | +15% · 0.94 · -10% | -14% · -1.25 · -17% | +18% · 1.04 · -19% | +4% · 0.40 · -20% | +10% · 0.69 · -19% | +5% · 0.47 · -20% |
| breakout · score_m10 | -4% · -0.58 · -15% | +7% · 0.73 · -12% | +2% · 0.23 · -20% | +22% · 1.08 · -14% | +17% · 1.00 · -11% | -14% · -1.28 · -17% | +11% · 0.74 · -19% | +5% · 0.49 · -20% | +9% · 0.61 · -22% | +5% · 0.48 · -22% |
| breakout · score_p10 | -4% · -0.60 · -15% | +7% · 0.73 · -12% | -1% · -0.03 · -20% | +6% · 0.47 · -11% | +15% · 0.93 · -10% | -14% · -1.28 · -17% | +11% · 0.75 · -19% | +3% · 0.38 · -20% | +6% · 0.49 · -22% | +4% · 0.36 · -22% |
| breakout · first_choice | -5% · -0.53 · -15% | +8% · 0.80 · -15% | -1% · -0.02 · -19% | +1% · 0.11 · -12% | +21% · 1.23 · -9% | -9% · -0.61 · -18% | +9% · 0.63 · -18% | +4% · 0.40 · -19% | +6% · 0.48 · -20% | +4% · 0.37 · -21% |
| breakout · risk_1 | -4% · -0.56 · -15% | +7% · 0.72 · -12% | +2% · 0.24 · -20% | +23% · 1.11 · -14% | +17% · 1.00 · -11% | -14% · -1.28 · -17% | +14% · 0.85 · -18% | +5% · 0.49 · -20% | +10% · 0.68 · -22% | +6% · 0.51 · -22% |
| |  | | | | | | | | | |
| **momentum** · smart | -2% · -0.35 · -13% | +10% · 0.76 · -15% | +7% · 0.63 · -17% | +40% · 1.74 · -13% | +29% · 1.12 · -17% | -13% · -1.56 · -14% | +23% · 1.06 · -23% | +9% · 0.69 · -17% | +20% · 0.97 · -23% | +11% · 0.75 · -23% |
| momentum · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| momentum · no_regime | -17% · -0.97 · -39% | +14% · 0.92 · -21% | +10% · 0.82 · -22% | +25% · 0.98 · -24% | +30% · 1.47 · -10% | -20% · -1.22 · -21% | +9% · 0.57 · -19% | +12% · 0.87 · -22% | +8% · 0.52 · -25% | +7% · 0.52 · -39% |
| momentum · no_score | -2% · -0.35 · -14% | +10% · 0.77 · -15% | +7% · 0.63 · -17% | +40% · 1.73 · -13% | +29% · 1.11 · -17% | -13% · -1.55 · -14% | +24% · 1.07 · -23% | +9% · 0.70 · -17% | +20% · 0.97 · -23% | +11% · 0.76 · -23% |
| momentum · no_selfcheck | -3% · -0.50 · -14% | +13% · 0.96 · -15% | +6% · 0.55 · -18% | +22% · 1.05 · -13% | +28% · 1.48 · -8% | -14% · -1.19 · -15% | +30% · 1.22 · -21% | +10% · 0.77 · -18% | +20% · 0.99 · -21% | +12% · 0.79 · -21% |
| momentum · score_m10 | -2% · -0.35 · -13% | +10% · 0.76 · -15% | +7% · 0.63 · -17% | +40% · 1.73 · -13% | +29% · 1.12 · -17% | -13% · -1.56 · -14% | +24% · 1.07 · -23% | +9% · 0.70 · -17% | +20% · 0.97 · -23% | +11% · 0.75 · -23% |
| momentum · score_p10 | -2% · -0.36 · -13% | +10% · 0.76 · -15% | +7% · 0.62 · -17% | +40% · 1.74 · -13% | +29% · 1.12 · -17% | -13% · -1.58 · -14% | +23% · 1.06 · -23% | +8% · 0.69 · -17% | +20% · 0.97 · -23% | +11% · 0.75 · -23% |
| momentum · first_choice | -2% · -0.32 · -14% | +12% · 0.98 · -14% | +6% · 0.55 · -16% | +13% · 0.70 · -18% | +22% · 1.05 · -13% | -11% · -0.80 · -15% | +4% · 0.32 · -21% | +9% · 0.76 · -17% | +5% · 0.38 · -21% | +6% · 0.52 · -21% |
| momentum · risk_1 | -2% · -0.28 · -12% | +10% · 0.76 · -15% | +7% · 0.63 · -17% | +22% · 1.08 · -13% | +28% · 1.47 · -8% | -14% · -1.34 · -16% | +22% · 1.04 · -23% | +9% · 0.70 · -17% | +16% · 0.87 · -23% | +10% · 0.71 · -23% |
| |  | | | | | | | | | |
| **pullback** · smart | -3% · -0.47 · -16% | +13% · 1.01 · -15% | +5% · 0.43 · -19% | +19% · 0.99 · -12% | +33% · 1.68 · -11% | -17% · -2.16 · -18% | +7% · 0.56 · -16% | +9% · 0.73 · -19% | +8% · 0.57 · -22% | +7% · 0.59 · -22% |
| pullback · plain | -28% · -0.63 · -67% | +23% · 1.03 · -23% | +16% · 0.85 · -32% | +35% · 0.99 · -45% | +34% · 1.06 · -21% | -30% · -1.11 · -36% | +85% · 1.81 · -37% | +20% · 0.94 · -32% | +46% · 1.23 · -45% | +22% · 0.81 · -67% |
| pullback · no_regime | -14% · -1.02 · -38% | +12% · 0.79 · -26% | +12% · 0.89 · -18% | +16% · 0.81 · -21% | +40% · 2.07 · -9% | -17% · -1.19 · -21% | +16% · 0.89 · -17% | +12% · 0.84 · -26% | +13% · 0.76 · -23% | +10% · 0.64 · -38% |
| pullback · no_score | -4% · -0.49 · -17% | +13% · 1.01 · -16% | +5% · 0.43 · -19% | +19% · 1.00 · -12% | +33% · 1.68 · -11% | -17% · -2.16 · -18% | +7% · 0.56 · -16% | +9% · 0.73 · -19% | +8% · 0.57 · -22% | +7% · 0.59 · -22% |
| pullback · no_selfcheck | -3% · -0.43 · -16% | +13% · 0.99 · -15% | +5% · 0.44 · -17% | +23% · 1.19 · -12% | +34% · 1.77 · -9% | -18% · -2.27 · -18% | +17% · 0.98 · -16% | +9% · 0.72 · -17% | +14% · 0.84 · -21% | +9% · 0.70 · -21% |
| pullback · score_m10 | -3% · -0.47 · -17% | +13% · 1.01 · -15% | +5% · 0.43 · -19% | +19% · 1.00 · -12% | +33% · 1.68 · -11% | -17% · -2.16 · -18% | +7% · 0.56 · -16% | +9% · 0.73 · -19% | +8% · 0.57 · -22% | +7% · 0.59 · -22% |
| pullback · score_p10 | -3% · -0.47 · -16% | +13% · 1.01 · -15% | +5% · 0.43 · -19% | +18% · 0.99 · -12% | +33% · 1.68 · -11% | -17% · -2.17 · -18% | +7% · 0.55 · -16% | +9% · 0.73 · -19% | +8% · 0.56 · -22% | +7% · 0.59 · -22% |
| pullback · first_choice | -4% · -0.54 · -18% | +12% · 0.92 · -16% | +8% · 0.68 · -16% | +12% · 0.63 · -16% | +26% · 1.40 · -10% | -15% · -1.50 · -17% | +1% · 0.14 · -15% | +10% · 0.80 · -16% | +3% · 0.30 · -20% | +6% · 0.51 · -20% |
| pullback · risk_1 | -3% · -0.47 · -16% | +13% · 1.01 · -15% | +5% · 0.43 · -19% | +18% · 0.98 · -12% | +33% · 1.68 · -11% | -17% · -2.16 · -18% | +7% · 0.56 · -16% | +9% · 0.73 · -19% | +8% · 0.56 · -22% | +7% · 0.59 · -22% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.42 · -19% | +13% · 0.92 · -19% | +15% · 0.81 · -34% | +11% · 0.64 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.13 · -20% | +21% · 0.72 · -38% | +34% · 2.15 · -6% | -11% · -0.37 · -21% | +27% · 1.36 · -23% | +18% · 1.16 · -21% | +18% · 0.86 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| adaptive · smart | +7% | 0.62 | -18% | 78% | +13% | 0.74 | -19% | 77% |
| adaptive · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| adaptive · no_regime | +11% | 0.77 | -19% | 94% | +1% | 0.14 | -27% | 65% |
| adaptive · no_score | +7% | 0.62 | -18% | 78% | +13% | 0.73 | -19% | 77% |
| adaptive · no_selfcheck | +8% | 0.67 | -15% | 81% | +14% | 0.79 | -21% | 75% |
| adaptive · score_m10 | +7% | 0.62 | -18% | 78% | +13% | 0.74 | -19% | 77% |
| adaptive · score_p10 | +7% | 0.64 | -18% | 77% | +13% | 0.74 | -19% | 77% |
| adaptive · first_choice | +10% | 0.89 | -20% | 77% | +1% | 0.14 | -22% | 60% |
| adaptive · risk_1 | +7% | 0.63 | -18% | 78% | +12% | 0.73 | -19% | 77% |
| trend · smart | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 78% |
| trend · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| trend · no_regime | +9% | 0.65 | -21% | 93% | +13% | 0.73 | -25% | 82% |
| trend · no_score | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 79% |
| trend · no_selfcheck | +11% | 0.89 | -17% | 83% | +14% | 0.79 | -21% | 78% |
| trend · score_m10 | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 78% |
| trend · score_p10 | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 78% |
| trend · first_choice | +9% | 0.77 | -16% | 83% | +6% | 0.46 | -20% | 73% |
| trend · risk_1 | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 78% |
| breakout · smart | +5% | 0.50 | -20% | 65% | +9% | 0.61 | -22% | 74% |
| breakout · plain | +19% | 0.90 | -30% | 99% | +48% | 1.24 | -48% | 97% |
| breakout · no_regime | +8% | 0.59 | -20% | 90% | +14% | 0.81 | -23% | 79% |
| breakout · no_score | +5% | 0.49 | -20% | 65% | +9% | 0.61 | -22% | 74% |
| breakout · no_selfcheck | +4% | 0.40 | -20% | 62% | +10% | 0.69 | -19% | 73% |
| breakout · score_m10 | +5% | 0.49 | -20% | 65% | +9% | 0.61 | -22% | 74% |
| breakout · score_p10 | +3% | 0.38 | -20% | 62% | +6% | 0.49 | -22% | 70% |
| breakout · first_choice | +4% | 0.40 | -19% | 71% | +6% | 0.48 | -20% | 68% |
| breakout · risk_1 | +5% | 0.49 | -20% | 65% | +10% | 0.68 | -22% | 74% |
| momentum · smart | +9% | 0.69 | -17% | 79% | +20% | 0.97 | -23% | 78% |
| momentum · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| momentum · no_regime | +12% | 0.87 | -22% | 85% | +8% | 0.52 | -25% | 73% |
| momentum · no_score | +9% | 0.70 | -17% | 80% | +20% | 0.97 | -23% | 78% |
| momentum · no_selfcheck | +10% | 0.77 | -18% | 81% | +20% | 0.99 | -21% | 81% |
| momentum · score_m10 | +9% | 0.70 | -17% | 79% | +20% | 0.97 | -23% | 78% |
| momentum · score_p10 | +8% | 0.69 | -17% | 79% | +20% | 0.97 | -23% | 78% |
| momentum · first_choice | +9% | 0.76 | -17% | 78% | +5% | 0.38 | -21% | 74% |
| momentum · risk_1 | +9% | 0.70 | -17% | 79% | +16% | 0.87 | -23% | 81% |
| pullback · smart | +9% | 0.73 | -19% | 79% | +8% | 0.57 | -22% | 65% |
| pullback · plain | +20% | 0.94 | -32% | 99% | +46% | 1.23 | -45% | 98% |
| pullback · no_regime | +12% | 0.84 | -26% | 92% | +13% | 0.76 | -23% | 78% |
| pullback · no_score | +9% | 0.73 | -19% | 79% | +8% | 0.57 | -22% | 65% |
| pullback · no_selfcheck | +9% | 0.72 | -17% | 81% | +14% | 0.84 | -21% | 73% |
| pullback · score_m10 | +9% | 0.73 | -19% | 79% | +8% | 0.57 | -22% | 65% |
| pullback · score_p10 | +9% | 0.73 | -19% | 79% | +8% | 0.56 | -22% | 65% |
| pullback · first_choice | +10% | 0.80 | -16% | 81% | +3% | 0.30 | -20% | 65% |
| pullback · risk_1 | +9% | 0.73 | -19% | 79% | +8% | 0.56 | -22% | 65% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.86 / 0.81 | -38% / -34% | | | | | |

## Inside each smart bot

### Adaptive All-Weather

Closed trades 1593 · exits {'Signal': 1291, 'Stop Loss': 302} · sessions blocked {'pause': 0, 'streak': 50, 'day': 4, 'regime': 273} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +8%/yr Sharpe 0.54, neutral 1164 days +17%/yr Sharpe 1.06, bear 607 days -2%/yr Sharpe -0.14, stress 277 days +5%/yr Sharpe 0.67

By strategy: Bollinger Breakout 99 trades -15,429 win 41%, Breakout Strategy 128 trades +197,517 win 40%, Donchian Breakout (Turtle) 138 trades -6,195 win 36%, EMA Crossover 14 trades +1,707 win 29%, Golden Cross (50/200) 6 trades +8,921 win 17%, MACD Crossover 108 trades -1,225 win 41%, MFI Money Flow (Volume) 1 trades +984 win 100%, Machine Learning Signal Combination 29 trades -2,210 win 38%, Mean Reversion 8 trades +1,537 win 100%, Momentum Strategy 63 trades -8,589 win 41%, Moving Average Crossover 5 trades +3,511 win 60%, Multi-Factor Strategy 38 trades +8,254 win 32%, OBV Trend (Volume) 91 trades +3,420 win 34%, Portfolio-Level Strategy 35 trades +33,389 win 34%, Regime-Based Strategy 36 trades -7,222 win 36%, Relative Strength Strategy 216 trades +65,673 win 43%, SMA Crossover 21 trades +41,698 win 67%, Statistical Arbitrage 3 trades -251 win 33%, Trend Following 53 trades -955 win 43%, VWAP Mean Reversion 13 trades +2,315 win 77%, VWAP Reclaim / Pullback 23 trades -5,593 win 35%, VWMA Crossover (Volume) 40 trades +264 win 32%, Volatility Breakout 208 trades +15,207 win 37%, Volume Breakout 217 trades +5,956 win 41%

### Trend Rider

Closed trades 1552 · exits {'Signal': 1243, 'Stop Loss': 309} · sessions blocked {'pause': 0, 'streak': 49, 'day': 5, 'regime': 274} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +11%/yr Sharpe 0.72, neutral 1164 days +19%/yr Sharpe 1.28, bear 607 days -8%/yr Sharpe -0.71, stress 277 days +9%/yr Sharpe 0.84

By strategy: Bollinger Breakout 95 trades -20,978 win 39%, Breakout Strategy 144 trades +273,004 win 33%, Donchian Breakout (Turtle) 127 trades +52,656 win 43%, EMA Crossover 6 trades +2,536 win 33%, Golden Cross (50/200) 9 trades +8,333 win 33%, MACD Crossover 91 trades +37 win 43%, Machine Learning Signal Combination 25 trades +7,435 win 48%, Mean Reversion 9 trades -929 win 78%, Momentum Strategy 50 trades -2,469 win 36%, Moving Average Crossover 7 trades +5,780 win 43%, Multi-Factor Strategy 41 trades -8,245 win 20%, OBV Trend (Volume) 87 trades -4,040 win 33%, Portfolio-Level Strategy 35 trades +96,942 win 40%, Regime-Based Strategy 41 trades +1,225 win 49%, Relative Strength Strategy 221 trades +34,639 win 41%, SMA Crossover 15 trades +39,302 win 53%, Statistical Arbitrage 4 trades -827 win 50%, Trend Following 49 trades -13,703 win 35%, VWAP Mean Reversion 9 trades +5,137 win 89%, VWAP Reclaim / Pullback 25 trades +9,153 win 36%, VWMA Crossover (Volume) 41 trades +7,542 win 41%, Volatility Breakout 204 trades +33,230 win 36%, Volume Breakout 217 trades +4,549 win 39%

### Breakout Hunter

Closed trades 2213 · exits {'Signal': 1264, 'Stop Loss': 529, 'Time Stop': 420} · sessions blocked {'pause': 0, 'streak': 25, 'day': 4, 'regime': 271} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +7%/yr Sharpe 0.52, neutral 1164 days +13%/yr Sharpe 1.05, bear 607 days -12%/yr Sharpe -1.50, stress 277 days +0%/yr Sharpe 0.07

By strategy: Bollinger Breakout 125 trades -1,757 win 46%, Breakout Strategy 172 trades +61,504 win 48%, Donchian Breakout (Turtle) 156 trades +17,159 win 42%, EMA Crossover 25 trades +1,821 win 52%, Golden Cross (50/200) 7 trades +3,701 win 57%, MACD Crossover 122 trades -585 win 40%, MFI Money Flow (Volume) 3 trades +399 win 33%, Machine Learning Signal Combination 41 trades +1,209 win 44%, Mean Reversion 20 trades +681 win 70%, Momentum Strategy 91 trades -3,794 win 45%, Moving Average Crossover 6 trades +8,137 win 50%, Multi-Factor Strategy 55 trades -650 win 44%, OBV Trend (Volume) 122 trades +8,501 win 42%, Pairs Trading 2 trades +1,544 win 100%, Portfolio-Level Strategy 51 trades +2,760 win 43%, Regime-Based Strategy 75 trades +1,643 win 48%, Relative Strength Strategy 234 trades +12,331 win 39%, SMA Crossover 29 trades +26,069 win 52%, Statistical Arbitrage 25 trades +5,796 win 68%, Trend Following 70 trades +8,101 win 46%, VWAP Mean Reversion 27 trades -3,029 win 59%, VWAP Reclaim / Pullback 41 trades -4,160 win 39%, VWMA Crossover (Volume) 73 trades +4,110 win 33%, Volatility Breakout 281 trades -23,248 win 37%, Volume Breakout 360 trades +19,238 win 42%

### Momentum Leaders

Closed trades 1564 · exits {'Signal': 1255, 'Stop Loss': 309} · sessions blocked {'pause': 0, 'streak': 14, 'day': 7, 'regime': 276} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +11%/yr Sharpe 0.67, neutral 1164 days +19%/yr Sharpe 1.20, bear 607 days -0%/yr Sharpe -0.03, stress 277 days +2%/yr Sharpe 0.26

By strategy: Bollinger Breakout 93 trades -18,362 win 35%, Breakout Strategy 149 trades +358,970 win 42%, Donchian Breakout (Turtle) 143 trades +13,728 win 39%, EMA Crossover 9 trades -1,855 win 11%, Golden Cross (50/200) 8 trades +9,378 win 25%, MACD Crossover 88 trades +12,961 win 43%, MFI Money Flow (Volume) 1 trades -477 win 0%, Machine Learning Signal Combination 24 trades +2,173 win 50%, Mean Reversion 10 trades +1,492 win 80%, Momentum Strategy 43 trades -4,418 win 40%, Moving Average Crossover 8 trades +2,865 win 25%, Multi-Factor Strategy 40 trades -2,341 win 30%, OBV Trend (Volume) 82 trades +16,781 win 40%, Portfolio-Level Strategy 34 trades +111,578 win 41%, Regime-Based Strategy 38 trades -488 win 61%, Relative Strength Strategy 219 trades +24,668 win 41%, SMA Crossover 19 trades +897 win 32%, Statistical Arbitrage 9 trades +3,877 win 56%, Trend Following 49 trades +4,224 win 51%, VWAP Mean Reversion 12 trades +5,222 win 75%, VWAP Reclaim / Pullback 31 trades +4,997 win 39%, VWMA Crossover (Volume) 42 trades -941 win 29%, Volatility Breakout 193 trades +63,000 win 41%, Volume Breakout 220 trades -19,786 win 39%

### Pullback Buyer

Closed trades 2525 · exits {'Signal': 1337, 'Time Stop': 712, 'Stop Loss': 476} · sessions blocked {'pause': 0, 'streak': 77, 'day': 0, 'regime': 270} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +9%/yr Sharpe 0.60, neutral 1164 days +14%/yr Sharpe 1.03, bear 607 days -7%/yr Sharpe -0.90, stress 277 days +5%/yr Sharpe 0.67

By strategy: Bollinger Breakout 140 trades +1,283 win 40%, Breakout Strategy 261 trades +124,755 win 30%, Donchian Breakout (Turtle) 241 trades +1,516 win 34%, EMA Crossover 18 trades +4,445 win 39%, Golden Cross (50/200) 18 trades +23,677 win 22%, MACD Crossover 151 trades -2,047 win 40%, Machine Learning Signal Combination 31 trades -820 win 35%, Mean Reversion 22 trades -2,287 win 55%, Momentum Strategy 80 trades +19,547 win 24%, Moving Average Crossover 6 trades +1,750 win 50%, Multi-Factor Strategy 69 trades -11,843 win 23%, OBV Trend (Volume) 133 trades +4,825 win 37%, Portfolio-Level Strategy 66 trades +15,645 win 21%, Regime-Based Strategy 61 trades -1,727 win 39%, Relative Strength Strategy 399 trades +14,885 win 29%, SMA Crossover 28 trades +32,178 win 39%, Statistical Arbitrage 10 trades -320 win 60%, Trend Following 68 trades +3,465 win 34%, VWAP Mean Reversion 19 trades +1,669 win 63%, VWAP Reclaim / Pullback 42 trades +4,948 win 29%, VWMA Crossover (Volume) 63 trades +4,739 win 30%, Volatility Breakout 291 trades +37,886 win 37%, Volume Breakout 308 trades -7,172 win 35%

