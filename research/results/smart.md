# Smart bots · period test

Run 2026-09-29 04:59 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 6 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **adaptive** · smart | -3% · -0.53 · -16% | +13% · 1.04 · -17% | -1% · -0.02 · -19% | +27% · 1.19 · -15% | +15% · 0.85 · -11% | -9% · -0.73 · -15% | +19% · 0.90 · -25% | +6% · 0.57 · -19% | +14% · 0.76 · -25% | +8% · 0.59 · -25% |
| adaptive · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| adaptive · no_regime | -18% · -1.31 · -40% | +14% · 0.94 · -18% | +7% · 0.58 · -19% | +6% · 0.37 · -25% | +17% · 1.05 · -9% | -17% · -1.21 · -19% | +2% · 0.22 · -14% | +11% · 0.77 · -19% | +1% · 0.14 · -27% | +4% · 0.34 · -40% |
| adaptive · no_score | -2% · -0.35 · -14% | +13% · 1.02 · -17% | -1% · -0.02 · -19% | +27% · 1.19 · -15% | +15% · 0.84 · -11% | -9% · -0.75 · -15% | +24% · 1.01 · -24% | +6% · 0.56 · -19% | +17% · 0.83 · -24% | +9% · 0.63 · -24% |
| adaptive · no_selfcheck | -5% · -0.78 · -16% | +14% · 1.14 · -14% | +5% · 0.53 · -17% | +19% · 0.94 · -15% | +22% · 1.15 · -11% | -11% · -1.27 · -12% | +14% · 0.87 · -20% | +10% · 0.84 · -17% | +11% · 0.72 · -21% | +9% · 0.69 · -21% |
| adaptive · score_m10 | -2% · -0.36 · -14% | +13% · 1.02 · -17% | -1% · -0.02 · -19% | +27% · 1.19 · -15% | +15% · 0.84 · -11% | -9% · -0.74 · -15% | +19% · 0.91 · -25% | +6% · 0.56 · -19% | +14% · 0.76 · -25% | +8% · 0.59 · -25% |
| adaptive · score_p10 | -4% · -0.62 · -15% | +13% · 1.08 · -16% | -1% · -0.02 · -19% | +27% · 1.19 · -15% | +15% · 0.85 · -11% | -9% · -0.71 · -15% | +19% · 0.90 · -25% | +6% · 0.58 · -19% | +14% · 0.76 · -25% | +8% · 0.60 · -25% |
| adaptive · first_choice | -9% · -0.98 · -20% | +10% · 1.04 · -12% | +7% · 0.64 · -14% | +17% · 0.82 · -16% | +5% · 0.35 · -13% | -13% · -1.71 · -14% | +2% · 0.20 · -19% | +9% · 0.82 · -14% | +2% · 0.19 · -22% | +4% · 0.41 · -22% |
| adaptive · risk_1 | -3% · -0.51 · -15% | +13% · 1.05 · -16% | -1% · -0.02 · -19% | +20% · 0.96 · -14% | +21% · 1.14 · -11% | -10% · -1.19 · -12% | +18% · 0.92 · -21% | +6% · 0.57 · -19% | +13% · 0.77 · -21% | +8% · 0.59 · -21% |
| |  | | | | | | | | | |
| **trend** · smart | -2% · -0.12 · -14% | +13% · 1.01 · -17% | +5% · 0.50 · -19% | +3% · 0.37 · -7% | +24% · 1.40 · -11% | -14% · -1.34 · -16% | +0% · 0.06 · -18% | +9% · 0.77 · -19% | +1% · 0.16 · -20% | +5% · 0.49 · -22% |
| trend · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| trend · no_regime | -11% · -0.62 · -42% | +16% · 1.04 · -15% | +3% · 0.29 · -17% | -3% · -0.11 · -20% | +31% · 1.36 · -15% | -15% · -0.96 · -19% | +6% · 0.48 · -17% | +9% · 0.69 · -17% | +5% · 0.35 · -22% | +5% · 0.41 · -42% |
| trend · no_score | -1% · -0.11 · -14% | +13% · 1.01 · -17% | +5% · 0.50 · -19% | +3% · 0.37 · -7% | +24% · 1.40 · -11% | -14% · -1.34 · -16% | +1% · 0.12 · -18% | +9% · 0.77 · -19% | +2% · 0.19 · -20% | +5% · 0.50 · -21% |
| trend · no_selfcheck | -1% · -0.07 · -15% | +11% · 0.81 · -16% | +6% · 0.57 · -15% | +4% · 0.33 · -12% | +32% · 1.57 · -11% | -15% · -1.41 · -16% | +10% · 0.68 · -16% | +9% · 0.70 · -16% | +8% · 0.54 · -20% | +7% · 0.57 · -20% |
| trend · score_m10 | -2% · -0.11 · -14% | +13% · 1.01 · -17% | +5% · 0.50 · -19% | +3% · 0.37 · -7% | +24% · 1.40 · -11% | -14% · -1.34 · -16% | +0% · 0.06 · -18% | +9% · 0.77 · -19% | +1% · 0.16 · -20% | +5% · 0.49 · -22% |
| trend · score_p10 | -2% · -0.12 · -14% | +13% · 1.01 · -17% | +5% · 0.50 · -19% | +3% · 0.37 · -7% | +24% · 1.40 · -11% | -14% · -1.33 · -16% | +0% · 0.06 · -18% | +9% · 0.77 · -19% | +1% · 0.16 · -20% | +5% · 0.49 · -22% |
| trend · first_choice | -7% · -0.76 · -21% | +15% · 1.17 · -14% | +8% · 0.68 · -15% | +8% · 0.55 · -14% | +10% · 0.65 · -12% | -14% · -1.52 · -16% | +7% · 0.53 · -15% | +12% · 0.92 · -15% | +4% · 0.32 · -21% | +7% · 0.56 · -21% |
| trend · risk_1 | -1% · -0.05 · -13% | +14% · 1.04 · -17% | +5% · 0.47 · -19% | +3% · 0.40 · -7% | +21% · 1.32 · -10% | -14% · -1.35 · -16% | +1% · 0.15 · -16% | +9% · 0.77 · -19% | +1% · 0.17 · -20% | +5% · 0.49 · -21% |
| |  | | | | | | | | | |
| **breakout** · smart | -5% · -0.78 · -15% | +9% · 0.92 · -12% | +1% · 0.19 · -17% | +29% · 1.23 · -14% | +36% · 1.89 · -10% | -14% · -1.46 · -16% | +19% · 1.05 · -21% | +5% · 0.53 · -17% | +17% · 0.96 · -21% | +8% · 0.66 · -21% |
| breakout · plain | -33% · -0.79 · -72% | +22% · 0.96 · -29% | +17% · 0.84 · -30% | +92% · 1.72 · -48% | +9% · 0.41 · -34% | -21% · -0.64 · -29% | +76% · 1.69 · -38% | +19% · 0.90 · -30% | +48% · 1.24 · -48% | +21% · 0.78 · -72% |
| breakout · no_regime | -14% · -0.88 · -38% | +8% · 0.67 · -22% | +6% · 0.53 · -19% | +11% · 0.59 · -25% | +36% · 1.95 · -9% | -18% · -1.13 · -23% | +18% · 1.00 · -20% | +7% · 0.60 · -22% | +13% · 0.76 · -26% | +7% · 0.50 · -38% |
| breakout · no_score | -5% · -0.77 · -15% | +9% · 0.92 · -12% | +2% · 0.19 · -17% | +29% · 1.23 · -14% | +37% · 1.90 · -10% | -14% · -1.46 · -17% | +19% · 1.05 · -21% | +5% · 0.53 · -17% | +17% · 0.96 · -21% | +8% · 0.66 · -21% |
| breakout · no_selfcheck | -6% · -0.94 · -15% | +9% · 0.92 · -13% | +4% · 0.43 · -16% | +9% · 0.51 · -17% | +28% · 1.56 · -10% | -15% · -1.46 · -17% | +28% · 1.42 · -21% | +7% · 0.65 · -16% | +17% · 0.99 · -21% | +9% · 0.71 · -21% |
| breakout · score_m10 | -5% · -0.77 · -15% | +9% · 0.92 · -12% | +1% · 0.19 · -17% | +29% · 1.23 · -14% | +37% · 1.89 · -10% | -14% · -1.46 · -16% | +19% · 1.05 · -21% | +5% · 0.53 · -17% | +17% · 0.96 · -21% | +8% · 0.66 · -21% |
| breakout · score_p10 | -5% · -0.81 · -15% | +9% · 0.94 · -12% | +1% · 0.17 · -17% | +29% · 1.23 · -14% | +36% · 1.88 · -10% | -14% · -1.46 · -16% | +19% · 1.05 · -21% | +5% · 0.53 · -17% | +17% · 0.96 · -21% | +8% · 0.65 · -21% |
| breakout · first_choice | -7% · -0.95 · -17% | +7% · 0.73 · -14% | +2% · 0.24 · -16% | -9% · -0.80 · -14% | +25% · 1.72 · -8% | -13% · -1.09 · -17% | +8% · 0.59 · -17% | +5% · 0.47 · -16% | +4% · 0.35 · -18% | +3% · 0.32 · -24% |
| breakout · risk_1 | -5% · -0.87 · -15% | +9% · 0.94 · -12% | +2% · 0.19 · -17% | +30% · 1.26 · -14% | +36% · 1.86 · -10% | -14% · -1.48 · -16% | +20% · 1.13 · -19% | +5% · 0.54 · -17% | +17% · 1.00 · -19% | +8% · 0.68 · -19% |
| |  | | | | | | | | | |
| **momentum** · smart | -5% · -0.39 · -18% | +13% · 0.89 · -29% | +12% · 0.88 · -20% | -1% · 0.02 · -25% | +23% · 1.32 · -8% | -17% · -2.11 · -18% | +5% · 0.41 · -19% | +12% · 0.88 · -29% | +3% · 0.25 · -25% | +7% · 0.53 · -29% |
| momentum · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| momentum · no_regime | -18% · -0.90 · -44% | +12% · 0.80 · -27% | +18% · 1.25 · -22% | +8% · 0.44 · -27% | +28% · 1.32 · -12% | -15% · -0.96 · -21% | +18% · 0.85 · -30% | +15% · 1.01 · -27% | +12% · 0.64 · -30% | +10% · 0.62 · -44% |
| momentum · no_score | -5% · -0.36 · -18% | +13% · 0.90 · -29% | +12% · 0.88 · -20% | -1% · 0.02 · -25% | +23% · 1.32 · -8% | -17% · -2.11 · -18% | +5% · 0.41 · -19% | +12% · 0.89 · -29% | +3% · 0.25 · -25% | +7% · 0.54 · -29% |
| momentum · no_selfcheck | -6% · -0.60 · -20% | +15% · 1.11 · -23% | +11% · 0.82 · -20% | -1% · 0.02 · -25% | +23% · 1.32 · -8% | -17% · -2.11 · -18% | +4% · 0.32 · -18% | +13% · 0.97 · -23% | +2% · 0.20 · -25% | +7% · 0.55 · -25% |
| momentum · score_m10 | -5% · -0.39 · -18% | +13% · 0.89 · -29% | +12% · 0.88 · -20% | -1% · 0.02 · -25% | +23% · 1.32 · -8% | -17% · -2.11 · -18% | +5% · 0.41 · -19% | +12% · 0.88 · -29% | +3% · 0.25 · -25% | +7% · 0.53 · -29% |
| momentum · score_p10 | -5% · -0.39 · -18% | +13% · 0.89 · -29% | +12% · 0.90 · -20% | -2% · -0.02 · -26% | +23% · 1.38 · -8% | -17% · -2.13 · -18% | +5% · 0.41 · -19% | +12% · 0.89 · -29% | +3% · 0.25 · -26% | +7% · 0.54 · -29% |
| momentum · first_choice | -6% · -0.55 · -19% | +12% · 0.86 · -29% | +13% · 0.97 · -19% | -5% · -0.27 · -23% | +23% · 1.32 · -8% | -16% · -1.08 · -18% | -2% · -0.08 · -25% | +13% · 0.91 · -29% | -1% · -0.03 · -29% | +5% · 0.44 · -29% |
| momentum · risk_1 | -5% · -0.44 · -18% | +13% · 0.91 · -29% | +12% · 0.89 · -20% | -2% · -0.04 · -25% | +23% · 1.41 · -8% | -17% · -2.12 · -18% | +6% · 0.48 · -18% | +12% · 0.90 · -29% | +3% · 0.28 · -25% | +7% · 0.56 · -29% |
| |  | | | | | | | | | |
| **pullback** · smart | -5% · -0.65 · -21% | +8% · 0.70 · -11% | +4% · 0.43 · -17% | +14% · 0.81 · -14% | +28% · 1.49 · -11% | -15% · -1.55 · -15% | +16% · 0.91 · -18% | +6% · 0.56 · -17% | +12% · 0.73 · -22% | +7% · 0.56 · -22% |
| pullback · plain | -28% · -0.63 · -67% | +23% · 1.03 · -23% | +16% · 0.85 · -32% | +35% · 0.99 · -45% | +34% · 1.06 · -21% | -30% · -1.11 · -36% | +85% · 1.81 · -37% | +20% · 0.94 · -32% | +46% · 1.23 · -45% | +22% · 0.81 · -67% |
| pullback · no_regime | -15% · -0.86 · -37% | +11% · 0.80 · -16% | +11% · 0.85 · -16% | -4% · -0.09 · -23% | +31% · 1.79 · -10% | -15% · -1.29 · -19% | +11% · 0.79 · -17% | +11% · 0.82 · -16% | +6% · 0.49 · -24% | +7% · 0.50 · -37% |
| pullback · no_score | -5% · -0.64 · -21% | +8% · 0.70 · -11% | +4% · 0.43 · -17% | +14% · 0.81 · -14% | +28% · 1.49 · -11% | -15% · -1.54 · -15% | +16% · 0.90 · -18% | +6% · 0.56 · -17% | +12% · 0.73 · -22% | +7% · 0.56 · -22% |
| pullback · no_selfcheck | -6% · -0.76 · -21% | +8% · 0.78 · -13% | +7% · 0.62 · -13% | +15% · 0.85 · -14% | +28% · 1.49 · -11% | -15% · -1.45 · -16% | +20% · 1.10 · -17% | +8% · 0.70 · -13% | +14% · 0.84 · -20% | +8% · 0.66 · -21% |
| pullback · score_m10 | -5% · -0.65 · -21% | +8% · 0.70 · -11% | +4% · 0.43 · -17% | +14% · 0.81 · -14% | +28% · 1.49 · -11% | -15% · -1.54 · -15% | +16% · 0.91 · -18% | +6% · 0.56 · -17% | +12% · 0.73 · -22% | +7% · 0.56 · -22% |
| pullback · score_p10 | -5% · -0.65 · -21% | +8% · 0.70 · -11% | +4% · 0.43 · -17% | +14% · 0.81 · -14% | +28% · 1.49 · -11% | -14% · -1.53 · -15% | +16% · 0.90 · -18% | +6% · 0.56 · -17% | +12% · 0.73 · -22% | +7% · 0.56 · -22% |
| pullback · first_choice | -6% · -0.74 · -20% | +8% · 0.73 · -11% | +5% · 0.49 · -16% | +21% · 1.14 · -13% | +36% · 1.90 · -11% | -14% · -1.27 · -16% | +5% · 0.48 · -12% | +6% · 0.60 · -16% | +8% · 0.64 · -19% | +6% · 0.53 · -20% |
| pullback · risk_1 | -5% · -0.65 · -21% | +8% · 0.70 · -11% | +4% · 0.43 · -17% | +14% · 0.81 · -14% | +28% · 1.49 · -11% | -15% · -1.55 · -15% | +16% · 0.91 · -18% | +6% · 0.56 · -17% | +12% · 0.73 · -22% | +7% · 0.56 · -22% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.42 · -19% | +13% · 0.92 · -19% | +15% · 0.81 · -34% | +11% · 0.64 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.13 · -20% | +21% · 0.72 · -38% | +34% · 2.15 · -6% | -11% · -0.37 · -21% | +27% · 1.36 · -23% | +18% · 1.16 · -21% | +18% · 0.86 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| adaptive · smart | +6% | 0.57 | -19% | 71% | +14% | 0.76 | -25% | 80% |
| adaptive · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| adaptive · no_regime | +11% | 0.77 | -19% | 94% | +1% | 0.14 | -27% | 65% |
| adaptive · no_score | +6% | 0.56 | -19% | 72% | +17% | 0.83 | -24% | 80% |
| adaptive · no_selfcheck | +10% | 0.84 | -17% | 76% | +11% | 0.72 | -21% | 71% |
| adaptive · score_m10 | +6% | 0.56 | -19% | 72% | +14% | 0.76 | -25% | 80% |
| adaptive · score_p10 | +6% | 0.58 | -19% | 71% | +14% | 0.76 | -25% | 80% |
| adaptive · first_choice | +9% | 0.82 | -14% | 74% | +2% | 0.19 | -22% | 63% |
| adaptive · risk_1 | +6% | 0.57 | -19% | 71% | +13% | 0.77 | -21% | 74% |
| trend · smart | +9% | 0.77 | -19% | 80% | +1% | 0.16 | -20% | 60% |
| trend · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| trend · no_regime | +9% | 0.69 | -17% | 95% | +5% | 0.35 | -22% | 80% |
| trend · no_score | +9% | 0.77 | -19% | 80% | +2% | 0.19 | -20% | 61% |
| trend · no_selfcheck | +9% | 0.70 | -16% | 84% | +8% | 0.54 | -20% | 74% |
| trend · score_m10 | +9% | 0.77 | -19% | 80% | +1% | 0.16 | -20% | 60% |
| trend · score_p10 | +9% | 0.77 | -19% | 80% | +1% | 0.16 | -20% | 60% |
| trend · first_choice | +12% | 0.92 | -15% | 82% | +4% | 0.32 | -21% | 73% |
| trend · risk_1 | +9% | 0.77 | -19% | 80% | +1% | 0.17 | -20% | 66% |
| breakout · smart | +5% | 0.53 | -17% | 70% | +17% | 0.96 | -21% | 77% |
| breakout · plain | +19% | 0.90 | -30% | 99% | +48% | 1.24 | -48% | 97% |
| breakout · no_regime | +7% | 0.60 | -22% | 86% | +13% | 0.76 | -26% | 76% |
| breakout · no_score | +5% | 0.53 | -17% | 70% | +17% | 0.96 | -21% | 77% |
| breakout · no_selfcheck | +7% | 0.65 | -16% | 72% | +17% | 0.99 | -21% | 78% |
| breakout · score_m10 | +5% | 0.53 | -17% | 70% | +17% | 0.96 | -21% | 77% |
| breakout · score_p10 | +5% | 0.53 | -17% | 70% | +17% | 0.96 | -21% | 77% |
| breakout · first_choice | +5% | 0.47 | -16% | 71% | +4% | 0.35 | -18% | 71% |
| breakout · risk_1 | +5% | 0.54 | -17% | 70% | +17% | 1.00 | -19% | 77% |
| momentum · smart | +12% | 0.88 | -29% | 75% | +3% | 0.25 | -25% | 62% |
| momentum · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| momentum · no_regime | +15% | 1.01 | -27% | 87% | +12% | 0.64 | -30% | 86% |
| momentum · no_score | +12% | 0.89 | -29% | 76% | +3% | 0.25 | -25% | 62% |
| momentum · no_selfcheck | +13% | 0.97 | -23% | 74% | +2% | 0.20 | -25% | 62% |
| momentum · score_m10 | +12% | 0.88 | -29% | 75% | +3% | 0.25 | -25% | 62% |
| momentum · score_p10 | +12% | 0.89 | -29% | 75% | +3% | 0.25 | -26% | 62% |
| momentum · first_choice | +13% | 0.91 | -29% | 77% | -1% | -0.03 | -29% | 61% |
| momentum · risk_1 | +12% | 0.90 | -29% | 75% | +3% | 0.28 | -25% | 62% |
| pullback · smart | +6% | 0.56 | -17% | 75% | +12% | 0.73 | -22% | 73% |
| pullback · plain | +20% | 0.94 | -32% | 99% | +46% | 1.23 | -45% | 98% |
| pullback · no_regime | +11% | 0.82 | -16% | 96% | +6% | 0.49 | -24% | 77% |
| pullback · no_score | +6% | 0.56 | -17% | 75% | +12% | 0.73 | -22% | 73% |
| pullback · no_selfcheck | +8% | 0.70 | -13% | 77% | +14% | 0.84 | -20% | 77% |
| pullback · score_m10 | +6% | 0.56 | -17% | 75% | +12% | 0.73 | -22% | 73% |
| pullback · score_p10 | +6% | 0.56 | -17% | 75% | +12% | 0.73 | -22% | 73% |
| pullback · first_choice | +6% | 0.60 | -16% | 76% | +8% | 0.64 | -19% | 77% |
| pullback · risk_1 | +6% | 0.56 | -17% | 75% | +12% | 0.73 | -22% | 73% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.86 / 0.81 | -38% / -34% | | | | | |

## Inside each smart bot

### Adaptive All-Weather

Closed trades 1527 · exits {'Signal': 1201, 'Stop Loss': 326} · sessions blocked {'pause': 0, 'streak': 67, 'day': 2, 'regime': 273} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +7%/yr Sharpe 0.46, neutral 1164 days +16%/yr Sharpe 1.11, bear 607 days -1%/yr Sharpe -0.08, stress 277 days +6%/yr Sharpe 0.75

By strategy: Bollinger Breakout 86 trades -18,635 win 40%, Breakout Strategy 147 trades +80,178 win 39%, Donchian Breakout (Turtle) 126 trades +3,760 win 38%, EMA Crossover 11 trades +1,794 win 36%, Golden Cross (50/200) 5 trades +7,278 win 20%, MACD Crossover 91 trades +513 win 40%, MFI Money Flow (Volume) 1 trades +552 win 100%, Machine Learning Signal Combination 23 trades +4,494 win 39%, Mean Reversion 8 trades -3,234 win 50%, Momentum Strategy 80 trades -4,465 win 38%, Moving Average Crossover 4 trades +6,558 win 75%, Multi-Factor Strategy 42 trades +1,106 win 24%, OBV Trend (Volume) 81 trades -3,613 win 32%, Portfolio-Level Strategy 36 trades +80,263 win 31%, Regime-Based Strategy 31 trades -4,536 win 32%, Relative Strength Strategy 232 trades +85,297 win 41%, SMA Crossover 17 trades +25,708 win 53%, Statistical Arbitrage 6 trades +957 win 67%, Trend Following 41 trades +2,204 win 41%, VWAP Mean Reversion 12 trades +4,186 win 83%, VWAP Reclaim / Pullback 41 trades -1,364 win 34%, VWMA Crossover (Volume) 35 trades +841 win 34%, Volatility Breakout 160 trades +2,671 win 36%, Volume Breakout 211 trades +23,938 win 38%

### Trend Rider

Closed trades 2020 · exits {'Signal': 1727, 'Stop Loss': 293} · sessions blocked {'pause': 0, 'streak': 77, 'day': 1, 'regime': 276} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +6%/yr Sharpe 0.51, neutral 1164 days +14%/yr Sharpe 1.11, bear 607 days -10%/yr Sharpe -1.10, stress 277 days +8%/yr Sharpe 0.78

By strategy: Bollinger Breakout 13 trades -3,867 win 46%, Breakout Strategy 16 trades +14,916 win 38%, Donchian Breakout (Turtle) 14 trades -6,045 win 36%, EMA Crossover 34 trades +1,716 win 32%, Golden Cross (50/200) 35 trades -3,702 win 20%, MACD Crossover 537 trades -35,387 win 38%, MFI Money Flow (Volume) 1 trades +645 win 100%, Machine Learning Signal Combination 94 trades +22,032 win 33%, Mean Reversion 7 trades +1,784 win 100%, Momentum Strategy 27 trades -1,152 win 33%, Moving Average Crossover 15 trades -119 win 33%, Multi-Factor Strategy 19 trades -562 win 32%, OBV Trend (Volume) 406 trades +24,868 win 36%, Portfolio-Level Strategy 12 trades +3,739 win 33%, Regime-Based Strategy 101 trades +1,372 win 47%, Relative Strength Strategy 87 trades +24,486 win 38%, SMA Crossover 80 trades +40,909 win 35%, Statistical Arbitrage 4 trades +1,266 win 75%, Trend Following 279 trades +54,388 win 42%, VWAP Mean Reversion 9 trades +2,218 win 78%, VWAP Reclaim / Pullback 15 trades +3,524 win 40%, VWMA Crossover (Volume) 184 trades +9,831 win 30%, Volatility Breakout 10 trades +15,360 win 50%, Volume Breakout 21 trades +8,826 win 57%

### Breakout Hunter

Closed trades 2285 · exits {'Signal': 1383, 'Stop Loss': 517, 'Time Stop': 385} · sessions blocked {'pause': 0, 'streak': 45, 'day': 7, 'regime': 262} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +11%/yr Sharpe 0.75, neutral 1164 days +14%/yr Sharpe 1.10, bear 607 days -14%/yr Sharpe -1.72, stress 277 days -1%/yr Sharpe -0.08

By strategy: Bollinger Breakout 233 trades -20,087 win 42%, Breakout Strategy 293 trades +202,647 win 49%, Donchian Breakout (Turtle) 292 trades -11,461 win 37%, EMA Crossover 1 trades -647 win 0%, Golden Cross (50/200) 1 trades -356 win 0%, MACD Crossover 13 trades +2,373 win 46%, MFI Money Flow (Volume) 2 trades +543 win 50%, Machine Learning Signal Combination 8 trades -837 win 38%, Mean Reversion 31 trades +3,523 win 71%, Momentum Strategy 47 trades +6,288 win 43%, Moving Average Crossover 1 trades +164 win 100%, Multi-Factor Strategy 30 trades -1,938 win 43%, OBV Trend (Volume) 19 trades -3,465 win 26%, Portfolio-Level Strategy 14 trades +8,301 win 64%, RSI Mean Reversion 3 trades +510 win 67%, Regime-Based Strategy 37 trades +2,338 win 54%, Relative Strength Strategy 175 trades -15,249 win 43%, SMA Crossover 7 trades +1,145 win 57%, Statistical Arbitrage 19 trades +3,052 win 63%, Trend Following 9 trades +985 win 44%, VWAP Mean Reversion 22 trades +2,142 win 68%, VWAP Reclaim / Pullback 22 trades -2,606 win 23%, VWMA Crossover (Volume) 11 trades +514 win 64%, Volatility Breakout 506 trades +10,711 win 40%, Volume Breakout 489 trades +127,688 win 49%

### Momentum Leaders

Closed trades 1018 · exits {'Signal': 666, 'Stop Loss': 352} · sessions blocked {'pause': 0, 'streak': 25, 'day': 5, 'regime': 272} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +11%/yr Sharpe 0.72, neutral 1164 days +18%/yr Sharpe 1.14, bear 607 days -9%/yr Sharpe -0.67, stress 277 days -9%/yr Sharpe -0.63

By strategy: Bollinger Breakout 1 trades -980 win 0%, Breakout Strategy 4 trades -8,070 win 0%, Donchian Breakout (Turtle) 2 trades -841 win 0%, MACD Crossover 1 trades +654 win 100%, Mean Reversion 3 trades +1,356 win 100%, Momentum Strategy 148 trades +31,769 win 39%, Multi-Factor Strategy 113 trades -23,123 win 33%, OBV Trend (Volume) 1 trades -414 win 0%, Portfolio-Level Strategy 71 trades +10,781 win 32%, Regime-Based Strategy 2 trades +18 win 50%, Relative Strength Strategy 655 trades +325,766 win 42%, SMA Crossover 1 trades +577 win 100%, Trend Following 2 trades +3,291 win 50%, VWAP Mean Reversion 2 trades +1,804 win 50%, VWAP Reclaim / Pullback 3 trades -592 win 0%, Volatility Breakout 4 trades +334 win 50%, Volume Breakout 5 trades +1,454 win 60%

### Pullback Buyer

Closed trades 2567 · exits {'Signal': 1325, 'Time Stop': 733, 'Stop Loss': 509} · sessions blocked {'pause': 0, 'streak': 110, 'day': 3, 'regime': 265} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +9%/yr Sharpe 0.60, neutral 1164 days +13%/yr Sharpe 0.97, bear 607 days -4%/yr Sharpe -0.40, stress 277 days +1%/yr Sharpe 0.12

By strategy: Bollinger Breakout 63 trades -8,401 win 33%, Breakout Strategy 160 trades +108,921 win 18%, Donchian Breakout (Turtle) 142 trades -8,838 win 31%, EMA Crossover 2 trades +3,161 win 100%, Golden Cross (50/200) 10 trades -2,109 win 10%, MACD Crossover 64 trades -5,357 win 34%, MFI Money Flow (Volume) 14 trades +1,838 win 21%, Machine Learning Signal Combination 11 trades +12,684 win 82%, Mean Reversion 87 trades +3,004 win 66%, Momentum Strategy 50 trades +7,562 win 34%, Moving Average Crossover 1 trades -25 win 0%, Multi-Factor Strategy 53 trades -8,906 win 11%, OBV Trend (Volume) 48 trades -2,293 win 40%, Pairs Trading 5 trades +814 win 20%, Portfolio-Level Strategy 28 trades +6,711 win 36%, RSI Mean Reversion 3 trades -650 win 33%, Regime-Based Strategy 5 trades +225 win 60%, Relative Strength Strategy 271 trades +80,777 win 33%, SMA Crossover 10 trades +23,153 win 50%, Statistical Arbitrage 63 trades +6,937 win 65%, Trend Following 35 trades -4,340 win 20%, VWAP Mean Reversion 79 trades +13,653 win 71%, VWAP Reclaim / Pullback 1104 trades +42,818 win 32%, VWMA Crossover (Volume) 1 trades -452 win 0%, Volatility Breakout 114 trades +370 win 38%, Volume Breakout 144 trades +9,031 win 35%

