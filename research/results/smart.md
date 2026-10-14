# Smart bots · period test

Run 2026-10-14 16:13 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 10 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **strong** · smart | -15% · -0.98 · -34% | +15% · 1.16 · -18% | +12% · 0.92 · -14% | +7% · 0.39 · -19% | +17% · 0.97 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +14% · 1.04 · -18% | +7% · 0.43 · -30% | +8% · 0.56 · -34% |
| strong · plain | -24% · -0.54 · -68% | +21% · 0.97 · -28% | +19% · 0.97 · -29% | +56% · 1.42 · -38% | +10% · 0.45 · -29% | -22% · -0.67 · -29% | +66% · 1.33 · -52% | +20% · 0.97 · -29% | +39% · 1.02 · -52% | +21% · 0.76 · -68% |
| strong · no_regime | -19% · -0.82 · -51% | +19% · 1.09 · -22% | +16% · 1.13 · -14% | -11% · -0.30 · -33% | +17% · 0.97 · -13% | -23% · -1.29 · -27% | +12% · 0.73 · -17% | +17% · 1.10 · -22% | +3% · 0.24 · -33% | +8% · 0.50 · -51% |
| strong · no_score | -16% · -1.09 · -34% | +16% · 1.29 · -12% | +12% · 0.88 · -16% | +7% · 0.39 · -19% | +17% · 0.96 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +14% · 1.07 · -16% | +7% · 0.43 · -30% | +8% · 0.56 · -34% |
| strong · no_selfcheck | -15% · -0.98 · -34% | +15% · 1.15 · -19% | +12% · 0.92 · -14% | +7% · 0.39 · -19% | +17% · 0.97 · -13% | -22% · -1.25 · -27% | +14% · 0.83 · -17% | +14% · 1.03 · -19% | +7% · 0.44 · -29% | +8% · 0.56 · -34% |
| strong · score_m10 | -12% · -0.60 · -35% | +20% · 1.18 · -21% | +12% · 0.88 · -16% | +7% · 0.41 · -19% | +17% · 0.97 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +16% · 1.04 · -21% | +7% · 0.44 · -30% | +9% · 0.61 · -35% |
| strong · score_p10 | -12% · -0.70 · -35% | +17% · 1.06 · -24% | +12% · 0.92 · -14% | +6% · 0.37 · -19% | +17% · 0.97 · -13% | -24% · -1.35 · -28% | +14% · 0.82 · -17% | +15% · 0.99 · -24% | +6% · 0.41 · -31% | +9% · 0.58 · -35% |
| strong · first_combo | -15% · -1.01 · -34% | +14% · 1.15 · -15% | +10% · 0.78 · -15% | +3% · 0.25 · -16% | +19% · 1.05 · -13% | -24% · -1.36 · -28% | +12% · 0.77 · -17% | +12% · 0.95 · -15% | +5% · 0.38 · -30% | +6% · 0.49 · -34% |
| strong · risk_moderate | -1% · -0.16 · -13% | +14% · 1.01 · -20% | +4% · 0.39 · -21% | +1% · 0.14 · -11% | +13% · 0.98 · -11% | -15% · -1.54 · -17% | +8% · 0.57 · -17% | +9% · 0.74 · -21% | +4% · 0.33 · -20% | +6% · 0.51 · -21% |
| strong · risk_conservative | -1% · -0.11 · -9% | +13% · 1.04 · -13% | +4% · 0.47 · -19% | +2% · 0.31 · -7% | +9% · 0.87 · -8% | -6% · -0.92 · -9% | +8% · 0.65 · -16% | +8% · 0.79 · -19% | +5% · 0.50 · -16% | +6% · 0.62 · -19% |
| strong · combo_back | +5% · 0.33 · -17% | +10% · 0.69 · -19% | +12% · 0.90 · -18% | +18% · 1.06 · -18% | +13% · 0.75 · -13% | -10% · -0.57 · -19% | +19% · 1.12 · -22% | +11% · 0.79 · -23% | +13% · 0.79 · -24% | +11% · 0.73 · -24% |
| strong · pos5 | -19% · -1.01 · -44% | +17% · 0.96 · -27% | +9% · 0.66 · -16% | +13% · 0.65 · -15% | +13% · 0.72 · -14% | -26% · -1.33 · -31% | +24% · 1.16 · -19% | +13% · 0.82 · -27% | +11% · 0.62 · -31% | +9% · 0.54 · -44% |
| strong · pos7 | -17% · -0.90 · -41% | +20% · 1.12 · -25% | +11% · 0.77 · -17% | +3% · 0.24 · -18% | +10% · 0.64 · -14% | -26% · -1.47 · -29% | +17% · 0.93 · -17% | +15% · 0.96 · -25% | +6% · 0.40 · -30% | +8% · 0.54 · -41% |
| |  | | | | | | | | | |
| **adaptive** · smart | -13% · -0.83 · -35% | +12% · 0.94 · -14% | +10% · 0.71 · -16% | +16% · 0.83 · -15% | +16% · 0.96 · -11% | -22% · -1.27 · -25% | +15% · 0.83 · -18% | +11% · 0.82 · -16% | +9% · 0.53 · -29% | +7% · 0.52 · -35% |
| adaptive · plain | -22% · -0.37 · -65% | +24% · 1.05 · -25% | +12% · 0.70 · -35% | +110% · 1.96 · -42% | +10% · 0.45 · -25% | -12% · -0.26 · -29% | +72% · 1.48 · -34% | +18% · 0.89 · -35% | +51% · 1.23 · -42% | +24% · 0.83 · -65% |
| adaptive · no_regime | -12% · -0.46 · -42% | +18% · 1.10 · -19% | +8% · 0.63 · -18% | +22% · 0.87 · -28% | +10% · 0.62 · -15% | -21% · -1.30 · -24% | +11% · 0.71 · -18% | +13% · 0.88 · -19% | +7% · 0.44 · -33% | +8% · 0.52 · -42% |
| adaptive · no_score | -12% · -0.78 · -34% | +12% · 0.91 · -15% | +10% · 0.71 · -16% | +16% · 0.83 · -15% | +16% · 0.96 · -11% | -22% · -1.27 · -25% | +15% · 0.83 · -18% | +11% · 0.81 · -16% | +9% · 0.53 · -29% | +7% · 0.52 · -34% |
| adaptive · no_selfcheck | -13% · -0.83 · -35% | +12% · 0.94 · -14% | +10% · 0.71 · -16% | +16% · 0.83 · -15% | +16% · 0.96 · -11% | -22% · -1.27 · -25% | +15% · 0.83 · -18% | +11% · 0.82 · -16% | +9% · 0.53 · -29% | +7% · 0.52 · -35% |
| adaptive · score_m10 | -12% · -0.79 · -34% | +12% · 0.92 · -14% | +10% · 0.71 · -16% | +16% · 0.83 · -15% | +16% · 0.96 · -11% | -22% · -1.27 · -25% | +15% · 0.83 · -18% | +11% · 0.81 · -16% | +9% · 0.53 · -29% | +7% · 0.52 · -34% |
| adaptive · score_p10 | -9% · -0.45 · -36% | +15% · 0.96 · -19% | +10% · 0.72 · -16% | +16% · 0.83 · -15% | +16% · 0.96 · -11% | -22% · -1.27 · -25% | +15% · 0.83 · -18% | +13% · 0.85 · -19% | +9% · 0.53 · -29% | +9% · 0.58 · -36% |
| adaptive · first_combo | -6% · -0.32 · -31% | +15% · 1.01 · -18% | +7% · 0.59 · -20% | +12% · 0.62 · -14% | +8% · 0.49 · -11% | -17% · -0.82 · -23% | +28% · 1.36 · -17% | +11% · 0.81 · -22% | +15% · 0.79 · -25% | +10% · 0.68 · -31% |
| adaptive · risk_moderate | -3% · -0.42 · -14% | +10% · 0.90 · -14% | +4% · 0.38 · -18% | +19% · 0.92 · -14% | +13% · 0.82 · -9% | -8% · -0.66 · -15% | +11% · 0.77 · -16% | +7% · 0.63 · -18% | +9% · 0.62 · -23% | +7% · 0.57 · -23% |
| adaptive · risk_conservative | -1% · -0.32 · -8% | +3% · 0.32 · -11% | +4% · 0.47 · -15% | +8% · 0.77 · -7% | +8% · 0.57 · -10% | -2% · -0.16 · -7% | +3% · 0.33 · -15% | +4% · 0.40 · -15% | +3% · 0.34 · -15% | +3% · 0.35 · -15% |
| adaptive · pos5 | -3% · -0.12 · -28% | +16% · 0.89 · -27% | +5% · 0.38 · -22% | +26% · 1.08 · -14% | +37% · 1.59 · -10% | -28% · -1.57 · -31% | +6% · 0.50 · -14% | +10% · 0.66 · -27% | +6% · 0.41 · -37% | +7% · 0.50 · -37% |
| adaptive · pos7 | -6% · -0.27 · -30% | +15% · 0.88 · -20% | +9% · 0.64 · -19% | +18% · 0.82 · -16% | +9% · 0.59 · -12% | -22% · -1.13 · -26% | +29% · 1.23 · -18% | +12% · 0.77 · -20% | +14% · 0.73 · -30% | +11% · 0.65 · -30% |
| |  | | | | | | | | | |
| **trend** · smart | -8% · -0.48 · -30% | +11% · 0.79 · -17% | +9% · 0.65 · -19% | +21% · 0.98 · -16% | +5% · 0.36 · -12% | -22% · -1.24 · -24% | +17% · 0.94 · -18% | +10% · 0.72 · -19% | +9% · 0.53 · -32% | +8% · 0.52 · -32% |
| trend · plain | -22% · -0.37 · -65% | +24% · 1.05 · -25% | +12% · 0.70 · -35% | +110% · 1.96 · -42% | +10% · 0.45 · -25% | -12% · -0.26 · -29% | +72% · 1.48 · -34% | +18% · 0.89 · -35% | +51% · 1.23 · -42% | +24% · 0.83 · -65% |
| trend · no_regime | -15% · -0.66 · -46% | +15% · 0.91 · -21% | +12% · 0.86 · -19% | +18% · 0.73 · -25% | +14% · 0.85 · -9% | -21% · -1.17 · -23% | +15% · 0.86 · -18% | +13% · 0.89 · -21% | +9% · 0.52 · -31% | +8% · 0.54 · -46% |
| trend · no_score | -10% · -0.63 · -32% | +11% · 0.79 · -18% | +9% · 0.65 · -19% | +21% · 0.98 · -16% | +5% · 0.36 · -12% | -22% · -1.24 · -24% | +17% · 0.94 · -18% | +10% · 0.72 · -19% | +9% · 0.53 · -32% | +7% · 0.51 · -32% |
| trend · no_selfcheck | -8% · -0.48 · -30% | +11% · 0.79 · -17% | +9% · 0.65 · -19% | +21% · 0.98 · -16% | +5% · 0.36 · -12% | -22% · -1.24 · -24% | +17% · 0.94 · -18% | +10% · 0.72 · -19% | +9% · 0.53 · -32% | +8% · 0.52 · -32% |
| trend · score_m10 | -10% · -0.63 · -32% | +11% · 0.79 · -18% | +9% · 0.65 · -19% | +21% · 0.98 · -16% | +5% · 0.36 · -12% | -22% · -1.24 · -24% | +17% · 0.94 · -18% | +10% · 0.72 · -19% | +9% · 0.53 · -32% | +7% · 0.51 · -32% |
| trend · score_p10 | -10% · -0.61 · -30% | +11% · 0.82 · -17% | +9% · 0.65 · -19% | +16% · 0.82 · -16% | +6% · 0.40 · -12% | -22% · -1.24 · -24% | +17% · 0.94 · -18% | +10% · 0.73 · -19% | +8% · 0.50 · -31% | +7% · 0.50 · -31% |
| trend · first_combo | -8% · -0.52 · -32% | +13% · 0.96 · -17% | +13% · 0.91 · -21% | +17% · 0.82 · -14% | +21% · 1.05 · -11% | -22% · -1.08 · -24% | +16% · 0.88 · -18% | +13% · 0.94 · -24% | +10% · 0.59 · -29% | +10% · 0.64 · -32% |
| trend · risk_moderate | -6% · -0.96 · -19% | +13% · 1.00 · -14% | +5% · 0.47 · -15% | +24% · 1.17 · -15% | +4% · 0.32 · -15% | -14% · -1.70 · -14% | +11% · 0.70 · -18% | +9% · 0.73 · -15% | +7% · 0.50 · -23% | +7% · 0.54 · -23% |
| trend · risk_conservative | -2% · -0.53 · -8% | +7% · 0.71 · -10% | +3% · 0.33 · -16% | +25% · 1.47 · -11% | -3% · -0.22 · -14% | -7% · -2.20 · -7% | +13% · 0.91 · -15% | +5% · 0.53 · -16% | +9% · 0.68 · -19% | +5% · 0.55 · -19% |
| trend · pos5 | -9% · -0.43 · -35% | +15% · 0.83 · -23% | +2% · 0.24 · -27% | +15% · 0.72 · -15% | +17% · 0.87 · -13% | -26% · -1.47 · -30% | +26% · 1.25 · -17% | +9% · 0.56 · -27% | +13% · 0.70 · -36% | +8% · 0.52 · -36% |
| trend · pos7 | -11% · -0.68 · -34% | +15% · 0.98 · -21% | +5% · 0.41 · -24% | +22% · 0.96 · -17% | +12% · 0.73 · -12% | -25% · -1.41 · -27% | +23% · 1.17 · -15% | +10% · 0.70 · -24% | +12% · 0.68 · -34% | +9% · 0.56 · -34% |
| |  | | | | | | | | | |
| **momentum** · smart | -12% · -0.62 · -36% | +11% · 0.73 · -20% | +10% · 0.71 · -21% | +19% · 0.89 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +16% · 0.87 · -21% | +11% · 0.72 · -21% | +10% · 0.59 · -29% | +8% · 0.52 · -36% |
| momentum · plain | -22% · -0.37 · -65% | +24% · 1.05 · -25% | +12% · 0.70 · -35% | +110% · 1.96 · -42% | +10% · 0.45 · -25% | -12% · -0.26 · -29% | +72% · 1.48 · -34% | +18% · 0.89 · -35% | +51% · 1.23 · -42% | +24% · 0.83 · -65% |
| momentum · no_regime | -22% · -0.97 · -53% | +16% · 0.97 · -20% | +11% · 0.78 · -21% | +14% · 0.62 · -25% | +18% · 0.94 · -11% | -24% · -1.39 · -26% | +12% · 0.66 · -19% | +14% · 0.88 · -25% | +6% · 0.39 · -30% | +6% · 0.43 · -53% |
| momentum · no_score | -10% · -0.56 · -35% | +10% · 0.72 · -23% | +10% · 0.73 · -21% | +19% · 0.89 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +16% · 0.87 · -21% | +10% · 0.72 · -23% | +10% · 0.59 · -29% | +8% · 0.54 · -35% |
| momentum · no_selfcheck | -15% · -0.86 · -35% | +8% · 0.69 · -18% | +10% · 0.71 · -21% | +19% · 0.89 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +16% · 0.87 · -21% | +9% · 0.70 · -21% | +10% · 0.59 · -29% | +7% · 0.48 · -35% |
| momentum · score_m10 | -14% · -0.82 · -34% | +8% · 0.71 · -17% | +10% · 0.71 · -21% | +19% · 0.89 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +16% · 0.87 · -21% | +9% · 0.71 · -21% | +10% · 0.59 · -29% | +7% · 0.49 · -34% |
| momentum · score_p10 | -7% · -0.31 · -35% | +13% · 0.81 · -17% | +10% · 0.71 · -21% | +19% · 0.89 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +16% · 0.87 · -21% | +12% · 0.76 · -21% | +10% · 0.59 · -29% | +9% · 0.58 · -35% |
| momentum · first_combo | -11% · -0.71 · -36% | +12% · 0.89 · -19% | +13% · 0.92 · -16% | +19% · 0.87 · -16% | +26% · 1.24 · -11% | -19% · -0.96 · -23% | +18% · 0.94 · -20% | +12% · 0.90 · -20% | +12% · 0.68 · -27% | +10% · 0.64 · -36% |
| momentum · risk_moderate | -3% · -0.34 · -14% | +13% · 0.94 · -16% | +5% · 0.46 · -16% | +31% · 1.42 · -16% | +16% · 0.76 · -21% | -8% · -1.39 · -9% | +9% · 0.58 · -18% | +9% · 0.71 · -16% | +10% · 0.63 · -26% | +8% · 0.61 · -26% |
| momentum · risk_conservative | -2% · -0.32 · -9% | +4% · 0.48 · -12% | +5% · 0.56 · -14% | +29% · 1.62 · -9% | +38% · 1.47 · -15% | -10% · -1.91 · -10% | +2% · 0.25 · -21% | +5% · 0.53 · -14% | +9% · 0.63 · -21% | +6% · 0.53 · -21% |
| momentum · pos5 | -10% · -0.52 · -31% | +8% · 0.57 · -23% | +6% · 0.45 · -23% | +21% · 0.95 · -17% | +5% · 0.35 · -23% | -20% · -0.92 · -26% | +33% · 1.26 · -22% | +7% · 0.51 · -29% | +17% · 0.77 · -32% | +9% · 0.52 · -32% |
| momentum · pos7 | -10% · -0.45 · -40% | +14% · 0.81 · -19% | +7% · 0.51 · -23% | +11% · 0.59 · -16% | +13% · 0.70 · -20% | -23% · -1.24 · -25% | +11% · 0.66 · -20% | +10% · 0.67 · -23% | +5% · 0.35 · -33% | +6% · 0.42 · -40% |
| |  | | | | | | | | | |
| **pullback** · smart | -10% · -0.59 · -35% | +8% · 0.55 · -28% | +11% · 0.84 · -21% | +17% · 0.84 · -17% | +20% · 1.13 · -11% | -24% · -1.57 · -26% | +4% · 0.37 · -20% | +10% · 0.69 · -28% | +3% · 0.27 · -30% | +5% · 0.40 · -35% |
| pullback · plain | -27% · -0.60 · -65% | +20% · 0.90 · -26% | +17% · 0.86 · -30% | +78% · 1.63 · -46% | +19% · 0.66 · -26% | -25% · -0.82 · -31% | +93% · 1.88 · -37% | +18% · 0.88 · -30% | +55% · 1.35 · -46% | +24% · 0.86 · -65% |
| pullback · no_regime | -20% · -0.96 · -50% | +16% · 1.01 · -22% | +13% · 0.94 · -20% | +26% · 0.94 · -27% | +22% · 1.29 · -10% | -23% · -1.51 · -25% | +16% · 0.87 · -15% | +15% · 0.98 · -22% | +11% · 0.62 · -30% | +9% · 0.58 · -50% |
| pullback · no_score | -13% · -0.88 · -32% | +8% · 0.69 · -17% | +12% · 0.87 · -21% | +17% · 0.84 · -17% | +20% · 1.13 · -11% | -24% · -1.57 · -26% | +4% · 0.37 · -20% | +10% · 0.79 · -21% | +3% · 0.27 · -30% | +5% · 0.40 · -32% |
| pullback · no_selfcheck | -11% · -0.73 · -34% | +16% · 1.06 · -20% | +11% · 0.84 · -21% | +17% · 0.84 · -17% | +20% · 1.13 · -11% | -24% · -1.57 · -26% | +4% · 0.37 · -20% | +13% · 0.96 · -21% | +3% · 0.27 · -30% | +7% · 0.52 · -34% |
| pullback · score_m10 | -13% · -0.89 · -32% | +8% · 0.70 · -17% | +12% · 0.87 · -21% | +17% · 0.84 · -17% | +20% · 1.13 · -11% | -24% · -1.57 · -26% | +4% · 0.37 · -20% | +10% · 0.79 · -21% | +3% · 0.27 · -30% | +5% · 0.40 · -32% |
| pullback · score_p10 | -12% · -0.87 · -33% | +6% · 0.59 · -25% | +11% · 0.84 · -21% | +17% · 0.84 · -17% | +20% · 1.13 · -11% | -24% · -1.57 · -26% | +4% · 0.37 · -20% | +9% · 0.73 · -25% | +3% · 0.27 · -30% | +5% · 0.38 · -33% |
| pullback · first_combo | -11% · -0.75 · -33% | +13% · 0.93 · -19% | +8% · 0.66 · -20% | +26% · 1.12 · -17% | +25% · 1.31 · -11% | -25% · -1.56 · -29% | +15% · 0.86 · -14% | +10% · 0.79 · -20% | +11% · 0.63 · -29% | +8% · 0.57 · -33% |
| pullback · risk_moderate | -5% · -0.83 · -17% | +10% · 0.85 · -16% | +9% · 0.70 · -14% | +19% · 0.99 · -12% | +15% · 0.87 · -13% | -17% · -2.13 · -18% | +21% · 1.13 · -16% | +9% · 0.77 · -16% | +13% · 0.78 · -21% | +9% · 0.69 · -21% |
| pullback · risk_conservative | +2% · 0.43 · -6% | +4% · 0.38 · -15% | +3% · 0.39 · -13% | +13% · 0.93 · -10% | +7% · 0.51 · -13% | -6% · -1.20 · -7% | +12% · 0.75 · -15% | +3% · 0.38 · -16% | +8% · 0.59 · -15% | +5% · 0.47 · -16% |
| pullback · pos5 | -19% · -1.15 · -46% | +24% · 1.22 · -21% | +7% · 0.51 · -16% | +9% · 0.51 · -15% | +8% · 0.50 · -13% | -33% · -2.22 · -35% | +20% · 0.83 · -26% | +15% · 0.89 · -21% | +7% · 0.40 · -43% | +8% · 0.49 · -46% |
| pullback · pos7 | -15% · -1.04 · -41% | +22% · 1.23 · -18% | +13% · 0.89 · -18% | +3% · 0.24 · -16% | +9% · 0.60 · -11% | -29% · -1.95 · -31% | +8% · 0.54 · -21% | +18% · 1.07 · -18% | +1% · 0.13 · -39% | +8% · 0.52 · -41% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.42 · -19% | +13% · 0.92 · -19% | +15% · 0.81 · -34% | +11% · 0.64 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.14 · -20% | +21% · 0.72 · -38% | +34% · 2.16 · -6% | -10% · -0.37 · -20% | +26% · 1.33 · -23% | +18% · 1.16 · -21% | +18% · 0.85 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| strong · smart | +14% | 1.04 | -18% | 87% | +7% | 0.43 | -30% | 89% |
| strong · plain | +20% | 0.97 | -29% | 99% | +39% | 1.02 | -52% | 98% |
| strong · no_regime | +17% | 1.10 | -22% | 99% | +3% | 0.24 | -33% | 90% |
| strong · no_score | +14% | 1.07 | -16% | 85% | +7% | 0.43 | -30% | 89% |
| strong · no_selfcheck | +14% | 1.03 | -19% | 87% | +7% | 0.44 | -29% | 89% |
| strong · score_m10 | +16% | 1.04 | -21% | 96% | +7% | 0.44 | -30% | 89% |
| strong · score_p10 | +15% | 0.99 | -24% | 96% | +6% | 0.41 | -31% | 89% |
| strong · first_combo | +12% | 0.95 | -15% | 84% | +5% | 0.38 | -30% | 86% |
| strong · risk_moderate | +9% | 0.74 | -21% | 77% | +4% | 0.33 | -20% | 68% |
| strong · risk_conservative | +8% | 0.79 | -19% | 66% | +5% | 0.50 | -16% | 48% |
| strong · combo_back | +11% | 0.79 | -23% | 63% | +13% | 0.79 | -24% | 71% |
| strong · pos5 | +13% | 0.82 | -27% | 96% | +11% | 0.62 | -31% | 89% |
| strong · pos7 | +15% | 0.96 | -25% | 97% | +6% | 0.40 | -30% | 89% |
| adaptive · smart | +11% | 0.82 | -16% | 89% | +9% | 0.53 | -29% | 90% |
| adaptive · plain | +18% | 0.89 | -35% | 99% | +51% | 1.23 | -42% | 98% |
| adaptive · no_regime | +13% | 0.88 | -19% | 99% | +7% | 0.44 | -33% | 83% |
| adaptive · no_score | +11% | 0.81 | -16% | 89% | +9% | 0.53 | -29% | 90% |
| adaptive · no_selfcheck | +11% | 0.82 | -16% | 89% | +9% | 0.53 | -29% | 90% |
| adaptive · score_m10 | +11% | 0.81 | -16% | 89% | +9% | 0.53 | -29% | 90% |
| adaptive · score_p10 | +13% | 0.85 | -19% | 98% | +9% | 0.53 | -29% | 90% |
| adaptive · first_combo | +11% | 0.81 | -22% | 95% | +15% | 0.79 | -25% | 96% |
| adaptive · risk_moderate | +7% | 0.63 | -18% | 78% | +9% | 0.62 | -23% | 69% |
| adaptive · risk_conservative | +4% | 0.40 | -15% | 59% | +3% | 0.34 | -15% | 58% |
| adaptive · pos5 | +10% | 0.66 | -27% | 96% | +6% | 0.41 | -37% | 74% |
| adaptive · pos7 | +12% | 0.77 | -20% | 97% | +14% | 0.73 | -30% | 92% |
| trend · smart | +10% | 0.72 | -19% | 94% | +9% | 0.53 | -32% | 87% |
| trend · plain | +18% | 0.89 | -35% | 99% | +51% | 1.23 | -42% | 98% |
| trend · no_regime | +13% | 0.89 | -21% | 99% | +9% | 0.52 | -31% | 89% |
| trend · no_score | +10% | 0.72 | -19% | 93% | +9% | 0.53 | -32% | 87% |
| trend · no_selfcheck | +10% | 0.72 | -19% | 94% | +9% | 0.53 | -32% | 87% |
| trend · score_m10 | +10% | 0.72 | -19% | 93% | +9% | 0.53 | -32% | 87% |
| trend · score_p10 | +10% | 0.73 | -19% | 91% | +8% | 0.50 | -31% | 87% |
| trend · first_combo | +13% | 0.94 | -24% | 93% | +10% | 0.59 | -29% | 94% |
| trend · risk_moderate | +9% | 0.73 | -15% | 82% | +7% | 0.50 | -23% | 72% |
| trend · risk_conservative | +5% | 0.53 | -16% | 55% | +9% | 0.68 | -19% | 53% |
| trend · pos5 | +9% | 0.56 | -27% | 96% | +13% | 0.70 | -36% | 84% |
| trend · pos7 | +10% | 0.70 | -24% | 91% | +12% | 0.68 | -34% | 85% |
| momentum · smart | +11% | 0.72 | -21% | 97% | +10% | 0.59 | -29% | 92% |
| momentum · plain | +18% | 0.89 | -35% | 99% | +51% | 1.23 | -42% | 98% |
| momentum · no_regime | +14% | 0.88 | -25% | 99% | +6% | 0.39 | -30% | 87% |
| momentum · no_score | +10% | 0.72 | -23% | 93% | +10% | 0.59 | -29% | 92% |
| momentum · no_selfcheck | +9% | 0.70 | -21% | 85% | +10% | 0.59 | -29% | 92% |
| momentum · score_m10 | +9% | 0.71 | -21% | 84% | +10% | 0.59 | -29% | 92% |
| momentum · score_p10 | +12% | 0.76 | -21% | 98% | +10% | 0.59 | -29% | 92% |
| momentum · first_combo | +12% | 0.90 | -20% | 92% | +12% | 0.68 | -27% | 95% |
| momentum · risk_moderate | +9% | 0.71 | -16% | 82% | +10% | 0.63 | -26% | 59% |
| momentum · risk_conservative | +5% | 0.53 | -14% | 55% | +9% | 0.63 | -21% | 50% |
| momentum · pos5 | +7% | 0.51 | -29% | 91% | +17% | 0.77 | -32% | 86% |
| momentum · pos7 | +10% | 0.67 | -23% | 98% | +5% | 0.35 | -33% | 80% |
| pullback · smart | +10% | 0.69 | -28% | 94% | +3% | 0.27 | -30% | 81% |
| pullback · plain | +18% | 0.88 | -30% | 99% | +55% | 1.35 | -46% | 98% |
| pullback · no_regime | +15% | 0.98 | -22% | 99% | +11% | 0.62 | -30% | 83% |
| pullback · no_score | +10% | 0.79 | -21% | 84% | +3% | 0.27 | -30% | 81% |
| pullback · no_selfcheck | +13% | 0.96 | -21% | 93% | +3% | 0.27 | -30% | 81% |
| pullback · score_m10 | +10% | 0.79 | -21% | 84% | +3% | 0.27 | -30% | 81% |
| pullback · score_p10 | +9% | 0.73 | -25% | 83% | +3% | 0.27 | -30% | 81% |
| pullback · first_combo | +10% | 0.79 | -20% | 92% | +11% | 0.63 | -29% | 90% |
| pullback · risk_moderate | +9% | 0.77 | -16% | 79% | +13% | 0.78 | -21% | 72% |
| pullback · risk_conservative | +3% | 0.38 | -16% | 48% | +8% | 0.59 | -15% | 53% |
| pullback · pos5 | +15% | 0.89 | -21% | 97% | +7% | 0.40 | -43% | 85% |
| pullback · pos7 | +18% | 1.07 | -18% | 97% | +1% | 0.13 | -39% | 72% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.85 / 0.81 | -38% / -34% | | | | | |

## Inside each smart bot

### Strong Stocks on Sale

Sectors (first day, sector): []

Closed trades 2191 · exits {'Signal': 1786, 'Stop Loss': 405} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1179, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2914 days +9%/yr Sharpe 0.62, neutral 1178 days +22%/yr Sharpe 1.37, bear 607 days -16%/yr Sharpe -0.85, stress 277 days +9%/yr Sharpe 0.79

By strategy: Donchian Breakout (Turtle) 1713 trades +266,060 win 40%, Mean Reversion & Multi-Factor Strategy & Regime-Based Strategy & Portfolio-Level Strategy (4/4) 83 trades +2,586 win 60%, Momentum Strategy & VWAP Mean Reversion & Multi-Factor Strategy (3/3) 41 trades +8,267 win 63%, VWAP Mean Reversion & Multi-Factor Strategy & Momentum Strategy & Portfolio-Level Strategy (4/4) 45 trades +3,265 win 58%, VWAP Mean Reversion & RSI Mean Reversion & Relative Strength Strategy & Portfolio-Level Strategy (3/4) 209 trades +43,641 win 63%, VWAP Mean Reversion & Statistical Arbitrage & Multi-Factor Strategy & Relative Strength Strategy (3/4) 100 trades +2,670 win 62%

### Adaptive All-Weather

Sectors (first day, sector): []

Closed trades 1766 · exits {'Signal': 1400, 'Stop Loss': 366} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1179, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2914 days +8%/yr Sharpe 0.49, neutral 1178 days +22%/yr Sharpe 1.35, bear 607 days -12%/yr Sharpe -0.64, stress 277 days +10%/yr Sharpe 0.72

By strategy: Bollinger Breakout 89 trades -6,309 win 40%, Breakout Strategy 115 trades +17,368 win 30%, Donchian Breakout (Turtle) 136 trades +16,741 win 43%, EMA Crossover 21 trades -6,188 win 29%, Golden Cross (50/200) 6 trades +11,716 win 17%, MACD Crossover 88 trades +1,775 win 35%, MFI Money Flow (Volume) 3 trades +6,987 win 67%, Machine Learning Signal Combination 24 trades +2,088 win 25%, Mean Reversion 25 trades +8,101 win 96%, Momentum Strategy 81 trades +39,607 win 35%, Moving Average Crossover 9 trades +15,155 win 67%, Multi-Factor Strategy 42 trades -2,849 win 26%, OBV Trend (Volume) 103 trades +4,982 win 47%, Pairs Trading 1 trades +510 win 100%, Portfolio-Level Strategy 52 trades +34,922 win 33%, Regime-Based Strategy 67 trades -3,039 win 40%, Relative Strength Strategy 261 trades +122,321 win 46%, SMA Crossover 27 trades +16,108 win 37%, Statistical Arbitrage 7 trades +1,144 win 71%, Trend Following 59 trades +4,261 win 42%, VWAP Mean Reversion 32 trades +9,445 win 81%, VWAP Reclaim / Pullback 50 trades +4,725 win 30%, VWMA Crossover (Volume) 44 trades +384 win 36%, Volatility Breakout 204 trades -22,610 win 37%, Volume Breakout 220 trades +16,043 win 39%

### Trend Rider

Sectors (first day, sector): []

Closed trades 1704 · exits {'Signal': 1342, 'Stop Loss': 362} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1179, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2914 days +7%/yr Sharpe 0.42, neutral 1178 days +22%/yr Sharpe 1.27, bear 607 days -11%/yr Sharpe -0.56, stress 277 days +12%/yr Sharpe 0.86

By strategy: Bollinger Breakout 81 trades -1,906 win 43%, Breakout Strategy 120 trades +104,001 win 32%, Donchian Breakout (Turtle) 140 trades +43,219 win 43%, EMA Crossover 12 trades -1,967 win 33%, Golden Cross (50/200) 7 trades +10,215 win 14%, MACD Crossover 96 trades -5,149 win 32%, MFI Money Flow (Volume) 2 trades +2,763 win 100%, Machine Learning Signal Combination 26 trades +1,259 win 35%, Mean Reversion 25 trades +5,749 win 88%, Momentum Strategy 71 trades +18,099 win 39%, Moving Average Crossover 4 trades -1,215 win 50%, Multi-Factor Strategy 44 trades -2,646 win 27%, OBV Trend (Volume) 86 trades -724 win 40%, Pairs Trading 1 trades +3,243 win 100%, Portfolio-Level Strategy 63 trades +41,856 win 35%, Regime-Based Strategy 67 trades -3,835 win 42%, Relative Strength Strategy 269 trades +33,590 win 43%, SMA Crossover 23 trades +1,532 win 52%, Statistical Arbitrage 7 trades +2,346 win 86%, Trend Following 56 trades -629 win 43%, VWAP Mean Reversion 26 trades +7,084 win 77%, VWAP Reclaim / Pullback 43 trades -1,886 win 28%, VWMA Crossover (Volume) 38 trades -2,332 win 32%, Volatility Breakout 189 trades -24,559 win 35%, Volume Breakout 208 trades +30,824 win 45%

### Momentum Leaders

Sectors (first day, sector): []

Closed trades 1739 · exits {'Signal': 1363, 'Stop Loss': 376} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2914, 'neutral': 1179, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2914 days +8%/yr Sharpe 0.47, neutral 1178 days +24%/yr Sharpe 1.32, bear 607 days -11%/yr Sharpe -0.50, stress 277 days +5%/yr Sharpe 0.35

By strategy: Bollinger Breakout 75 trades -14,450 win 44%, Breakout Strategy 140 trades +66,456 win 38%, Donchian Breakout (Turtle) 152 trades +110,705 win 47%, EMA Crossover 16 trades +591 win 25%, Golden Cross (50/200) 5 trades -5,928 win 0%, MACD Crossover 81 trades -5,774 win 31%, MFI Money Flow (Volume) 2 trades +1,669 win 50%, Machine Learning Signal Combination 26 trades -3,643 win 27%, Mean Reversion 25 trades +8,539 win 84%, Momentum Strategy 64 trades +2,366 win 31%, Moving Average Crossover 5 trades +1,306 win 20%, Multi-Factor Strategy 41 trades +3,937 win 39%, OBV Trend (Volume) 100 trades -482 win 34%, Portfolio-Level Strategy 62 trades +52,675 win 35%, Regime-Based Strategy 68 trades +5,043 win 54%, Relative Strength Strategy 278 trades +86,964 win 42%, SMA Crossover 20 trades -7,735 win 35%, Statistical Arbitrage 12 trades -2,972 win 50%, Trend Following 61 trades +8,712 win 46%, VWAP Mean Reversion 28 trades +8,579 win 79%, VWAP Reclaim / Pullback 55 trades +319 win 31%, VWMA Crossover (Volume) 37 trades -9,085 win 24%, Volatility Breakout 178 trades +7,910 win 39%, Volume Breakout 208 trades -5,494 win 40%

### Pullback Buyer

Sectors (first day, sector): []

Closed trades 3022 · exits {'Signal': 1568, 'Time Stop': 869, 'Stop Loss': 585} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2914, 'neutral': 1179, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2914 days +7%/yr Sharpe 0.48, neutral 1178 days +18%/yr Sharpe 1.07, bear 607 days -18%/yr Sharpe -0.97, stress 277 days +0%/yr Sharpe 0.03

By strategy: Bollinger Breakout 136 trades -11,274 win 33%, Breakout Strategy 249 trades +52,252 win 28%, Donchian Breakout (Turtle) 250 trades +17,758 win 32%, EMA Crossover 24 trades +4,740 win 33%, Golden Cross (50/200) 19 trades +8,374 win 16%, MACD Crossover 155 trades -632 win 35%, MFI Money Flow (Volume) 1 trades +938 win 100%, Machine Learning Signal Combination 44 trades -5,225 win 14%, Mean Reversion 57 trades -3 win 65%, Momentum Strategy 125 trades +13,815 win 26%, Moving Average Crossover 5 trades +4,722 win 60%, Multi-Factor Strategy 90 trades -5,921 win 21%, OBV Trend (Volume) 179 trades -1,417 win 37%, Portfolio-Level Strategy 91 trades +8,852 win 21%, RSI Mean Reversion 1 trades -100 win 0%, Regime-Based Strategy 110 trades -8,555 win 42%, Relative Strength Strategy 562 trades +53,339 win 32%, SMA Crossover 39 trades +1,126 win 31%, Statistical Arbitrage 14 trades +1,655 win 64%, Trend Following 84 trades +9,909 win 36%, VWAP Mean Reversion 53 trades +11,989 win 68%, VWAP Reclaim / Pullback 75 trades -603 win 23%, VWMA Crossover (Volume) 61 trades +5,532 win 38%, Volatility Breakout 291 trades -7,280 win 37%, Volume Breakout 307 trades -4,295 win 32%

