# Smart bots · period test

Run 2026-10-11 08:53 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 15 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **strong** · smart | -14% · -0.87 · -34% | +15% · 1.15 · -19% | +10% · 0.80 · -18% | +4% · 0.27 · -19% | +17% · 0.97 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +13% · 0.97 · -19% | +6% · 0.41 · -30% | +7% · 0.53 · -34% |
| strong · plain | -24% · -0.56 · -68% | +23% · 1.03 · -24% | +16% · 0.88 · -34% | +30% · 0.93 · -38% | +16% · 0.66 · -23% | -21% · -0.64 · -28% | +61% · 1.26 · -51% | +19% · 0.96 · -34% | +34% · 0.93 · -51% | +19% · 0.71 · -68% |
| strong · no_regime | -20% · -0.88 · -51% | +20% · 1.20 · -20% | +15% · 1.05 · -14% | -7% · -0.10 · -32% | +17% · 0.96 · -13% | -23% · -1.38 · -28% | +12% · 0.73 · -17% | +17% · 1.13 · -20% | +3% · 0.27 · -32% | +8% · 0.51 · -51% |
| strong · no_score | -14% · -0.96 · -34% | +14% · 1.13 · -16% | +10% · 0.77 · -18% | +7% · 0.40 · -19% | +17% · 0.96 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +12% · 0.94 · -18% | +6% · 0.43 · -30% | +7% · 0.51 · -34% |
| strong · no_selfcheck | -14% · -0.86 · -34% | +16% · 1.17 · -18% | +10% · 0.80 · -18% | +4% · 0.27 · -19% | +17% · 0.97 · -13% | -23% · -1.35 · -27% | +14% · 0.84 · -17% | +13% · 0.98 · -18% | +6% · 0.42 · -30% | +8% · 0.54 · -34% |
| strong · score_m10 | -16% · -0.88 · -40% | +19% · 1.16 · -20% | +10% · 0.77 · -18% | +8% · 0.44 · -19% | +19% · 1.05 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +14% · 0.97 · -20% | +7% · 0.45 · -30% | +8% · 0.55 · -40% |
| strong · score_p10 | -6% · -0.24 · -35% | +19% · 1.16 · -20% | +14% · 1.02 · -16% | +7% · 0.41 · -19% | +19% · 1.05 · -13% | -23% · -1.36 · -28% | +14% · 0.84 · -17% | +16% · 1.09 · -20% | +7% · 0.46 · -30% | +10% · 0.68 · -35% |
| strong · first_combo | -13% · -0.88 · -33% | +13% · 1.05 · -17% | +9% · 0.72 · -17% | +2% · 0.18 · -16% | +19% · 1.05 · -13% | -24% · -1.42 · -28% | +12% · 0.78 · -17% | +11% · 0.88 · -17% | +5% · 0.37 · -31% | +6% · 0.47 · -33% |
| strong · risk_moderate | -1% · -0.13 · -13% | +14% · 1.02 · -20% | +5% · 0.48 · -20% | +0% · 0.10 · -15% | +12% · 0.87 · -11% | -16% · -1.59 · -17% | +8% · 0.57 · -17% | +9% · 0.78 · -20% | +3% · 0.30 · -20% | +6% · 0.52 · -22% |
| strong · risk_conservative | -1% · -0.11 · -9% | +12% · 0.97 · -13% | +4% · 0.48 · -19% | +1% · 0.17 · -7% | +4% · 0.50 · -6% | -6% · -1.31 · -7% | +5% · 0.46 · -16% | +8% · 0.76 · -19% | +2% · 0.29 · -16% | +5% · 0.54 · -19% |
| strong · combo_back | +5% · 0.34 · -17% | +10% · 0.69 · -19% | +12% · 0.90 · -18% | +18% · 1.06 · -18% | +14% · 0.77 · -13% | -10% · -0.57 · -19% | +20% · 1.17 · -22% | +11% · 0.79 · -23% | +14% · 0.82 · -24% | +11% · 0.74 · -24% |
| strong · pos5 | -17% · -0.88 · -44% | +15% · 0.91 · -27% | +10% · 0.67 · -16% | +10% · 0.50 · -17% | +13% · 0.71 · -14% | -28% · -1.50 · -33% | +24% · 1.19 · -19% | +13% · 0.80 · -27% | +10% · 0.58 · -33% | +8% · 0.53 · -44% |
| strong · pos7 | -16% · -0.83 · -41% | +16% · 0.96 · -24% | +12% · 0.83 · -17% | +5% · 0.31 · -16% | +10% · 0.64 · -14% | -28% · -1.61 · -31% | +13% · 0.78 · -17% | +14% · 0.89 · -24% | +4% · 0.29 · -32% | +7% · 0.47 · -41% |
| |  | | | | | | | | | |
| **adaptive** · smart | -11% · -0.68 · -33% | +12% · 0.91 · -13% | +9% · 0.71 · -17% | +17% · 0.85 · -15% | +17% · 0.97 · -11% | -22% · -1.27 · -25% | +18% · 0.95 · -16% | +11% · 0.80 · -17% | +10% · 0.60 · -29% | +8% · 0.56 · -33% |
| adaptive · plain | -22% · -0.37 · -65% | +27% · 1.13 · -25% | +15% · 0.73 · -34% | +110% · 1.97 · -42% | +7% · 0.37 · -25% | -12% · -0.28 · -26% | +63% · 1.44 · -40% | +20% · 0.94 · -34% | +46% · 1.19 · -42% | +23% · 0.83 · -65% |
| adaptive · no_regime | -15% · -0.61 · -43% | +18% · 1.11 · -19% | +8% · 0.66 · -20% | +20% · 0.81 · -27% | +10% · 0.62 · -15% | -21% · -1.30 · -24% | +13% · 0.77 · -18% | +13% · 0.90 · -20% | +7% · 0.46 · -32% | +8% · 0.52 · -43% |
| adaptive · no_score | -10% · -0.62 · -32% | +11% · 0.86 · -15% | +9% · 0.71 · -17% | +17% · 0.85 · -15% | +17% · 0.97 · -11% | -22% · -1.27 · -25% | +18% · 0.95 · -16% | +10% · 0.78 · -17% | +10% · 0.60 · -29% | +8% · 0.56 · -32% |
| adaptive · no_selfcheck | -11% · -0.68 · -33% | +11% · 0.89 · -14% | +9% · 0.71 · -17% | +17% · 0.85 · -15% | +17% · 0.97 · -11% | -22% · -1.27 · -25% | +18% · 0.95 · -16% | +10% · 0.79 · -17% | +10% · 0.60 · -29% | +8% · 0.56 · -33% |
| adaptive · score_m10 | -10% · -0.63 · -32% | +12% · 0.89 · -14% | +9% · 0.71 · -17% | +17% · 0.85 · -15% | +17% · 0.97 · -11% | -22% · -1.27 · -25% | +18% · 0.95 · -16% | +10% · 0.80 · -17% | +10% · 0.60 · -29% | +8% · 0.56 · -32% |
| adaptive · score_p10 | -9% · -0.60 · -34% | +14% · 0.96 · -18% | +8% · 0.65 · -20% | +17% · 0.85 · -15% | +17% · 0.97 · -11% | -22% · -1.27 · -25% | +18% · 0.95 · -16% | +11% · 0.81 · -20% | +10% · 0.60 · -29% | +8% · 0.58 · -34% |
| adaptive · first_combo | -6% · -0.32 · -31% | +15% · 1.05 · -18% | +5% · 0.47 · -18% | +18% · 0.85 · -14% | +15% · 0.70 · -16% | -17% · -0.85 · -23% | +27% · 1.34 · -17% | +10% · 0.78 · -20% | +16% · 0.83 · -27% | +11% · 0.68 · -31% |
| adaptive · risk_moderate | -3% · -0.43 · -14% | +9% · 0.77 · -15% | +4% · 0.42 · -16% | +23% · 1.05 · -15% | +3% · 0.28 · -13% | -10% · -0.92 · -14% | +23% · 1.09 · -18% | +7% · 0.59 · -16% | +14% · 0.76 · -21% | +8% · 0.61 · -21% |
| adaptive · risk_conservative | -1% · -0.31 · -8% | +4% · 0.41 · -11% | +3% · 0.38 · -13% | +20% · 1.22 · -11% | -1% · 0.00 · -14% | -5% · -1.10 · -5% | +2% · 0.22 · -16% | +3% · 0.40 · -13% | +3% · 0.29 · -17% | +3% · 0.32 · -17% |
| adaptive · pos5 | -3% · -0.06 · -28% | +15% · 0.84 · -26% | +5% · 0.42 · -19% | +25% · 1.06 · -14% | +37% · 1.59 · -10% | -28% · -1.57 · -31% | +20% · 1.02 · -16% | +10% · 0.65 · -26% | +13% · 0.70 · -37% | +10% · 0.60 · -37% |
| adaptive · pos7 | -4% · -0.20 · -31% | +14% · 0.85 · -20% | +9% · 0.64 · -19% | +19% · 0.88 · -14% | +9% · 0.60 · -12% | -22% · -1.13 · -26% | +31% · 1.30 · -17% | +11% · 0.75 · -20% | +16% · 0.78 · -30% | +11% · 0.67 · -31% |
| |  | | | | | | | | | |
| **trend** · smart | -9% · -0.53 · -31% | +10% · 0.73 · -17% | +9% · 0.69 · -16% | +20% · 0.96 · -17% | +5% · 0.36 · -12% | -22% · -1.23 · -24% | +9% · 0.62 · -16% | +10% · 0.71 · -17% | +4% · 0.32 · -31% | +6% · 0.43 · -31% |
| trend · plain | -22% · -0.37 · -65% | +27% · 1.13 · -25% | +15% · 0.73 · -34% | +110% · 1.97 · -42% | +7% · 0.37 · -25% | -12% · -0.28 · -26% | +63% · 1.44 · -40% | +20% · 0.94 · -34% | +46% · 1.19 · -42% | +23% · 0.83 · -65% |
| trend · no_regime | -15% · -0.66 · -46% | +15% · 0.88 · -21% | +11% · 0.79 · -18% | +22% · 0.84 · -27% | +14% · 0.85 · -9% | -20% · -1.16 · -23% | +19% · 0.98 · -16% | +13% · 0.84 · -21% | +11% · 0.62 · -31% | +9% · 0.56 · -46% |
| trend · no_score | -10% · -0.65 · -33% | +11% · 0.78 · -17% | +9% · 0.69 · -16% | +20% · 0.96 · -17% | +5% · 0.36 · -12% | -22% · -1.23 · -24% | +9% · 0.62 · -16% | +10% · 0.74 · -17% | +4% · 0.32 · -31% | +6% · 0.43 · -33% |
| trend · no_selfcheck | -9% · -0.53 · -31% | +10% · 0.73 · -17% | +9% · 0.69 · -16% | +20% · 0.96 · -17% | +5% · 0.36 · -12% | -22% · -1.23 · -24% | +9% · 0.62 · -16% | +10% · 0.71 · -17% | +4% · 0.32 · -31% | +6% · 0.43 · -31% |
| trend · score_m10 | -10% · -0.65 · -33% | +11% · 0.78 · -17% | +9% · 0.69 · -16% | +20% · 0.96 · -17% | +5% · 0.36 · -12% | -22% · -1.23 · -24% | +9% · 0.62 · -16% | +10% · 0.74 · -17% | +4% · 0.32 · -31% | +6% · 0.43 · -33% |
| trend · score_p10 | -10% · -0.63 · -31% | +9% · 0.72 · -16% | +9% · 0.65 · -19% | +16% · 0.80 · -17% | +6% · 0.40 · -12% | -22% · -1.23 · -24% | +9% · 0.63 · -16% | +9% · 0.69 · -19% | +4% · 0.30 · -31% | +5% · 0.40 · -31% |
| trend · first_combo | -8% · -0.52 · -32% | +16% · 1.09 · -17% | +13% · 0.93 · -21% | +14% · 0.68 · -14% | +21% · 1.05 · -10% | -26% · -1.43 · -27% | +19% · 1.05 · -18% | +15% · 1.01 · -24% | +10% · 0.60 · -30% | +10% · 0.68 · -32% |
| trend · risk_moderate | -6% · -0.96 · -19% | +13% · 0.98 · -14% | +4% · 0.37 · -15% | +30% · 1.38 · -16% | +12% · 0.70 · -10% | -14% · -1.31 · -15% | +12% · 0.73 · -18% | +8% · 0.68 · -15% | +9% · 0.60 · -20% | +7% · 0.56 · -20% |
| trend · risk_conservative | -2% · -0.51 · -8% | +7% · 0.71 · -11% | +4% · 0.44 · -16% | +6% · 0.58 · -7% | +4% · 0.37 · -11% | -12% · -2.48 · -12% | +13% · 0.94 · -13% | +6% · 0.58 · -16% | +7% · 0.55 · -16% | +5% · 0.51 · -16% |
| trend · pos5 | -10% · -0.55 · -34% | +13% · 0.82 · -23% | +2% · 0.23 · -27% | +14% · 0.70 · -15% | +17% · 0.87 · -13% | -26% · -1.47 · -30% | +29% · 1.34 · -17% | +8% · 0.54 · -27% | +14% · 0.74 · -36% | +8% · 0.52 · -36% |
| trend · pos7 | -11% · -0.68 · -34% | +13% · 0.87 · -21% | +6% · 0.45 · -23% | +22% · 0.94 · -17% | +12% · 0.73 · -12% | -25% · -1.41 · -27% | +25% · 1.25 · -16% | +9% · 0.67 · -23% | +13% · 0.72 · -34% | +9% · 0.56 · -34% |
| |  | | | | | | | | | |
| **momentum** · smart | -12% · -0.72 · -39% | +12% · 0.76 · -18% | +8% · 0.62 · -21% | +21% · 0.94 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +23% · 1.09 · -21% | +10% · 0.69 · -25% | +14% · 0.74 · -28% | +9% · 0.57 · -39% |
| momentum · plain | -22% · -0.37 · -65% | +27% · 1.13 · -25% | +15% · 0.73 · -34% | +110% · 1.97 · -42% | +7% · 0.37 · -25% | -12% · -0.28 · -26% | +63% · 1.44 · -40% | +20% · 0.94 · -34% | +46% · 1.19 · -42% | +23% · 0.83 · -65% |
| momentum · no_regime | -23% · -1.01 · -54% | +19% · 1.15 · -21% | +12% · 0.85 · -22% | +4% · 0.30 · -27% | +17% · 0.85 · -13% | -25% · -1.41 · -26% | +14% · 0.75 · -19% | +15% · 1.01 · -26% | +6% · 0.36 · -28% | +7% · 0.46 · -54% |
| momentum · no_score | -14% · -0.81 · -37% | +11% · 0.71 · -22% | +8% · 0.62 · -21% | +21% · 0.94 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +23% · 1.09 · -21% | +10% · 0.67 · -23% | +14% · 0.74 · -28% | +9% · 0.55 · -37% |
| momentum · no_selfcheck | -15% · -1.02 · -36% | +9% · 0.77 · -14% | +8% · 0.62 · -21% | +21% · 0.94 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +23% · 1.09 · -21% | +9% · 0.69 · -23% | +14% · 0.74 · -28% | +8% · 0.54 · -36% |
| momentum · score_m10 | -14% · -0.81 · -37% | +11% · 0.71 · -22% | +8% · 0.62 · -21% | +21% · 0.94 · -21% | +22% · 1.10 · -15% | -21% · -1.03 · -26% | +23% · 1.09 · -21% | +10% · 0.67 · -23% | +14% · 0.74 · -28% | +9% · 0.55 · -37% |
| momentum · score_p10 | -13% · -0.72 · -38% | +14% · 0.88 · -21% | +12% · 0.86 · -17% | +27% · 1.20 · -20% | +21% · 1.02 · -15% | -25% · -1.42 · -26% | +21% · 1.01 · -19% | +13% · 0.87 · -23% | +13% · 0.70 · -28% | +10% · 0.64 · -38% |
| momentum · first_combo | -11% · -0.71 · -36% | +13% · 0.94 · -19% | +15% · 1.07 · -16% | +15% · 0.74 · -17% | +27% · 1.29 · -11% | -23% · -1.26 · -25% | +18% · 0.96 · -20% | +14% · 1.00 · -19% | +12% · 0.64 · -28% | +10% · 0.67 · -36% |
| momentum · risk_moderate | -3% · -0.39 · -15% | +14% · 1.05 · -14% | +7% · 0.59 · -19% | +34% · 1.48 · -16% | +11% · 0.56 · -24% | -8% · -1.42 · -9% | +8% · 0.55 · -18% | +10% · 0.83 · -19% | +9% · 0.60 · -29% | +9% · 0.66 · -29% |
| momentum · risk_conservative | -2% · -0.35 · -10% | +4% · 0.42 · -12% | +2% · 0.31 · -13% | +25% · 1.58 · -7% | +34% · 1.32 · -16% | -8% · -1.04 · -10% | +8% · 0.67 · -20% | +3% · 0.37 · -13% | +11% · 0.79 · -20% | +5% · 0.52 · -20% |
| momentum · pos5 | -10% · -0.52 · -31% | +8% · 0.59 · -17% | +7% · 0.50 · -22% | +19% · 0.85 · -16% | +20% · 0.93 · -17% | -25% · -1.15 · -28% | +37% · 1.35 · -17% | +8% · 0.54 · -25% | +20% · 0.85 · -30% | +10% · 0.58 · -31% |
| momentum · pos7 | -10% · -0.45 · -40% | +15% · 0.87 · -17% | +8% · 0.55 · -22% | +10% · 0.55 · -18% | +14% · 0.74 · -19% | -22% · -1.13 · -25% | +23% · 1.06 · -26% | +11% · 0.72 · -22% | +11% · 0.60 · -31% | +9% · 0.54 · -40% |
| |  | | | | | | | | | |
| **pullback** · smart | -16% · -1.02 · -40% | +10% · 0.69 · -27% | +12% · 0.88 · -19% | +21% · 0.98 · -16% | +19% · 1.06 · -9% | -22% · -1.39 · -25% | +4% · 0.34 · -20% | +11% · 0.78 · -27% | +4% · 0.30 · -30% | +5% · 0.41 · -40% |
| pullback · plain | -27% · -0.60 · -65% | +17% · 0.83 · -22% | +18% · 0.98 · -32% | +26% · 0.81 · -46% | +16% · 0.64 · -26% | -31% · -1.13 · -36% | +92% · 1.93 · -36% | +17% · 0.89 · -32% | +45% · 1.22 · -46% | +21% · 0.79 · -65% |
| pullback · no_regime | -22% · -1.07 · -52% | +16% · 0.97 · -24% | +13% · 0.94 · -19% | +40% · 1.30 · -26% | +27% · 1.42 · -9% | -22% · -1.38 · -25% | +22% · 1.01 · -16% | +14% · 0.96 · -24% | +17% · 0.82 · -28% | +11% · 0.65 · -52% |
| pullback · no_score | -13% · -0.94 · -33% | +10% · 0.88 · -17% | +11% · 0.86 · -19% | +21% · 0.98 · -16% | +19% · 1.06 · -9% | -22% · -1.39 · -25% | +4% · 0.34 · -20% | +11% · 0.87 · -19% | +4% · 0.30 · -30% | +6% · 0.44 · -33% |
| pullback · no_selfcheck | -12% · -0.79 · -35% | +15% · 1.03 · -19% | +12% · 0.89 · -19% | +21% · 0.98 · -16% | +19% · 1.06 · -9% | -22% · -1.39 · -25% | +4% · 0.34 · -20% | +13% · 0.96 · -19% | +4% · 0.30 · -30% | +7% · 0.52 · -35% |
| pullback · score_m10 | -13% · -0.95 · -33% | +10% · 0.88 · -17% | +11% · 0.86 · -19% | +21% · 0.98 · -16% | +19% · 1.06 · -9% | -22% · -1.39 · -25% | +4% · 0.34 · -20% | +11% · 0.87 · -19% | +4% · 0.30 · -30% | +6% · 0.44 · -33% |
| pullback · score_p10 | -10% · -0.58 · -37% | +9% · 0.62 · -31% | +12% · 0.89 · -19% | +21% · 0.98 · -16% | +19% · 1.06 · -9% | -22% · -1.39 · -25% | +4% · 0.34 · -20% | +10% · 0.75 · -31% | +4% · 0.30 · -30% | +6% · 0.44 · -37% |
| pullback · first_combo | -11% · -0.74 · -33% | +10% · 0.78 · -19% | +7% · 0.60 · -20% | +26% · 1.12 · -17% | +25% · 1.32 · -11% | -25% · -1.54 · -28% | +18% · 1.01 · -14% | +9% · 0.69 · -20% | +12% · 0.71 · -28% | +8% · 0.56 · -33% |
| pullback · risk_moderate | -5% · -0.81 · -17% | +10% · 0.84 · -15% | +4% · 0.39 · -18% | +5% · 0.38 · -12% | +15% · 0.87 · -13% | -18% · -2.15 · -18% | +21% · 1.12 · -16% | +7% · 0.61 · -18% | +10% · 0.68 · -22% | +7% · 0.57 · -22% |
| pullback · risk_conservative | +2% · 0.42 · -6% | +5% · 0.54 · -14% | +2% · 0.24 · -15% | +4% · 0.43 · -9% | +24% · 1.21 · -10% | -8% · -1.34 · -8% | +9% · 0.68 · -15% | +3% · 0.40 · -15% | +8% · 0.59 · -15% | +5% · 0.49 · -15% |
| pullback · pos5 | -13% · -0.75 · -40% | +24% · 1.25 · -21% | +6% · 0.46 · -15% | +9% · 0.51 · -15% | +8% · 0.50 · -13% | -33% · -2.22 · -35% | +23% · 0.91 · -26% | +15% · 0.89 · -21% | +8% · 0.45 · -40% | +9% · 0.55 · -40% |
| pullback · pos7 | -15% · -1.03 · -40% | +22% · 1.21 · -17% | +14% · 0.94 · -16% | +15% · 0.77 · -14% | +12% · 0.73 · -11% | -30% · -2.00 · -32% | +9% · 0.60 · -21% | +18% · 1.08 · -17% | +3% · 0.26 · -39% | +9% · 0.58 · -40% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +23% · 1.44 · -19% | +13% · 0.92 · -19% | +15% · 0.82 · -34% | +11% · 0.65 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.14 · -20% | +21% · 0.72 · -38% | +34% · 2.16 · -6% | -10% · -0.37 · -20% | +27% · 1.39 · -23% | +18% · 1.16 · -21% | +18% · 0.88 · -38% | +15% · 0.78 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| strong · smart | +13% | 0.97 | -19% | 88% | +6% | 0.41 | -30% | 88% |
| strong · plain | +19% | 0.96 | -34% | 99% | +34% | 0.93 | -51% | 97% |
| strong · no_regime | +17% | 1.13 | -20% | 99% | +3% | 0.27 | -32% | 90% |
| strong · no_score | +12% | 0.94 | -18% | 86% | +6% | 0.43 | -30% | 89% |
| strong · no_selfcheck | +13% | 0.98 | -18% | 88% | +6% | 0.42 | -30% | 89% |
| strong · score_m10 | +14% | 0.97 | -20% | 96% | +7% | 0.45 | -30% | 89% |
| strong · score_p10 | +16% | 1.09 | -20% | 96% | +7% | 0.46 | -30% | 89% |
| strong · first_combo | +11% | 0.88 | -17% | 85% | +5% | 0.37 | -31% | 86% |
| strong · risk_moderate | +9% | 0.78 | -20% | 76% | +3% | 0.30 | -20% | 70% |
| strong · risk_conservative | +8% | 0.76 | -19% | 66% | +2% | 0.29 | -16% | 41% |
| strong · combo_back | +11% | 0.79 | -23% | 63% | +14% | 0.82 | -24% | 71% |
| strong · pos5 | +13% | 0.80 | -27% | 95% | +10% | 0.58 | -33% | 87% |
| strong · pos7 | +14% | 0.89 | -24% | 97% | +4% | 0.29 | -32% | 86% |
| adaptive · smart | +11% | 0.80 | -17% | 89% | +10% | 0.60 | -29% | 90% |
| adaptive · plain | +20% | 0.94 | -34% | 99% | +46% | 1.19 | -42% | 98% |
| adaptive · no_regime | +13% | 0.90 | -20% | 99% | +7% | 0.46 | -32% | 87% |
| adaptive · no_score | +10% | 0.78 | -17% | 90% | +10% | 0.60 | -29% | 90% |
| adaptive · no_selfcheck | +10% | 0.79 | -17% | 89% | +10% | 0.60 | -29% | 90% |
| adaptive · score_m10 | +10% | 0.80 | -17% | 90% | +10% | 0.60 | -29% | 90% |
| adaptive · score_p10 | +11% | 0.81 | -20% | 93% | +10% | 0.60 | -29% | 90% |
| adaptive · first_combo | +10% | 0.78 | -20% | 95% | +16% | 0.83 | -27% | 94% |
| adaptive · risk_moderate | +7% | 0.59 | -16% | 78% | +14% | 0.76 | -21% | 73% |
| adaptive · risk_conservative | +3% | 0.40 | -13% | 58% | +3% | 0.29 | -17% | 48% |
| adaptive · pos5 | +10% | 0.65 | -26% | 96% | +13% | 0.70 | -37% | 78% |
| adaptive · pos7 | +11% | 0.75 | -20% | 97% | +16% | 0.78 | -30% | 92% |
| trend · smart | +10% | 0.71 | -17% | 93% | +4% | 0.32 | -31% | 82% |
| trend · plain | +20% | 0.94 | -34% | 99% | +46% | 1.19 | -42% | 98% |
| trend · no_regime | +13% | 0.84 | -21% | 99% | +11% | 0.62 | -31% | 84% |
| trend · no_score | +10% | 0.74 | -17% | 93% | +4% | 0.32 | -31% | 82% |
| trend · no_selfcheck | +10% | 0.71 | -17% | 93% | +4% | 0.32 | -31% | 82% |
| trend · score_m10 | +10% | 0.74 | -17% | 93% | +4% | 0.32 | -31% | 82% |
| trend · score_p10 | +9% | 0.69 | -19% | 90% | +4% | 0.30 | -31% | 83% |
| trend · first_combo | +15% | 1.01 | -24% | 93% | +10% | 0.60 | -30% | 88% |
| trend · risk_moderate | +8% | 0.68 | -15% | 82% | +9% | 0.60 | -20% | 75% |
| trend · risk_conservative | +6% | 0.58 | -16% | 59% | +7% | 0.55 | -16% | 55% |
| trend · pos5 | +8% | 0.54 | -27% | 91% | +14% | 0.74 | -36% | 84% |
| trend · pos7 | +9% | 0.67 | -23% | 91% | +13% | 0.72 | -34% | 85% |
| momentum · smart | +10% | 0.69 | -25% | 98% | +14% | 0.74 | -28% | 94% |
| momentum · plain | +20% | 0.94 | -34% | 99% | +46% | 1.19 | -42% | 98% |
| momentum · no_regime | +15% | 1.01 | -26% | 99% | +6% | 0.36 | -28% | 94% |
| momentum · no_score | +10% | 0.67 | -23% | 97% | +14% | 0.74 | -28% | 94% |
| momentum · no_selfcheck | +9% | 0.69 | -23% | 84% | +14% | 0.74 | -28% | 94% |
| momentum · score_m10 | +10% | 0.67 | -23% | 97% | +14% | 0.74 | -28% | 94% |
| momentum · score_p10 | +13% | 0.87 | -23% | 98% | +13% | 0.70 | -28% | 92% |
| momentum · first_combo | +14% | 1.00 | -19% | 91% | +12% | 0.64 | -28% | 94% |
| momentum · risk_moderate | +10% | 0.83 | -19% | 80% | +9% | 0.60 | -29% | 59% |
| momentum · risk_conservative | +3% | 0.37 | -13% | 51% | +11% | 0.79 | -20% | 54% |
| momentum · pos5 | +8% | 0.54 | -25% | 91% | +20% | 0.85 | -30% | 91% |
| momentum · pos7 | +11% | 0.72 | -22% | 98% | +11% | 0.60 | -31% | 90% |
| pullback · smart | +11% | 0.78 | -27% | 94% | +4% | 0.30 | -30% | 83% |
| pullback · plain | +17% | 0.89 | -32% | 99% | +45% | 1.22 | -46% | 98% |
| pullback · no_regime | +14% | 0.96 | -24% | 99% | +17% | 0.82 | -28% | 96% |
| pullback · no_score | +11% | 0.87 | -19% | 86% | +4% | 0.30 | -30% | 83% |
| pullback · no_selfcheck | +13% | 0.96 | -19% | 93% | +4% | 0.30 | -30% | 83% |
| pullback · score_m10 | +11% | 0.87 | -19% | 85% | +4% | 0.30 | -30% | 83% |
| pullback · score_p10 | +10% | 0.75 | -31% | 93% | +4% | 0.30 | -30% | 83% |
| pullback · first_combo | +9% | 0.69 | -20% | 90% | +12% | 0.71 | -28% | 91% |
| pullback · risk_moderate | +7% | 0.61 | -18% | 77% | +10% | 0.68 | -22% | 71% |
| pullback · risk_conservative | +3% | 0.40 | -15% | 54% | +8% | 0.59 | -15% | 57% |
| pullback · pos5 | +15% | 0.89 | -21% | 97% | +8% | 0.45 | -40% | 85% |
| pullback · pos7 | +18% | 1.08 | -17% | 96% | +3% | 0.26 | -39% | 72% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.88 / 0.82 | -38% / -34% | | | | | |

## Inside each smart bot

### Strong Stocks on Sale

Sectors (first day, sector): []

Closed trades 2188 · exits {'Signal': 1780, 'Stop Loss': 408} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1176, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2914 days +8%/yr Sharpe 0.56, neutral 1175 days +24%/yr Sharpe 1.47, bear 606 days -19%/yr Sharpe -0.98, stress 278 days +9%/yr Sharpe 0.80

By strategy: Donchian Breakout (Turtle) 1708 trades +244,613 win 40%, Mean Reversion & Multi-Factor Strategy & Regime-Based Strategy & Portfolio-Level Strategy (4/4) 80 trades +1,320 win 57%, Momentum Strategy & VWAP Mean Reversion & Multi-Factor Strategy (3/3) 45 trades +12,828 win 67%, VWAP Mean Reversion & Multi-Factor Strategy & Momentum Strategy & Portfolio-Level Strategy (4/4) 42 trades +3,494 win 60%, VWAP Mean Reversion & RSI Mean Reversion & Relative Strength Strategy & Portfolio-Level Strategy (3/4) 211 trades +33,945 win 62%, VWAP Mean Reversion & Statistical Arbitrage & Multi-Factor Strategy & Relative Strength Strategy (3/4) 102 trades +2,973 win 61%

### Adaptive All-Weather

Sectors (first day, sector): []

Closed trades 1740 · exits {'Signal': 1380, 'Stop Loss': 360} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1176, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2914 days +7%/yr Sharpe 0.45, neutral 1175 days +22%/yr Sharpe 1.34, bear 606 days -9%/yr Sharpe -0.47, stress 278 days +11%/yr Sharpe 0.85

By strategy: Bollinger Breakout 82 trades -5,344 win 38%, Breakout Strategy 119 trades +32,929 win 30%, Donchian Breakout (Turtle) 132 trades +26,781 win 44%, EMA Crossover 19 trades -4,517 win 37%, Golden Cross (50/200) 9 trades +7,224 win 11%, MACD Crossover 89 trades +1,505 win 36%, MFI Money Flow (Volume) 3 trades +6,549 win 67%, Machine Learning Signal Combination 23 trades +845 win 26%, Mean Reversion 26 trades +7,588 win 96%, Momentum Strategy 74 trades +29,257 win 31%, Moving Average Crossover 10 trades +9,802 win 50%, Multi-Factor Strategy 43 trades -4,217 win 28%, OBV Trend (Volume) 104 trades +2,530 win 45%, Pairs Trading 1 trades +466 win 100%, Portfolio-Level Strategy 57 trades +52,462 win 35%, Regime-Based Strategy 68 trades +3,458 win 47%, Relative Strength Strategy 256 trades +110,164 win 46%, SMA Crossover 25 trades -3,882 win 36%, Statistical Arbitrage 5 trades +1,904 win 80%, Trend Following 57 trades -1,050 win 37%, VWAP Mean Reversion 30 trades +9,969 win 80%, VWAP Reclaim / Pullback 50 trades +4,985 win 30%, VWMA Crossover (Volume) 42 trades -2,389 win 31%, Volatility Breakout 198 trades -14,973 win 37%, Volume Breakout 218 trades +18,380 win 39%

### Trend Rider

Sectors (first day, sector): []

Closed trades 1712 · exits {'Signal': 1335, 'Stop Loss': 377} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2914, 'neutral': 1176, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2914 days +5%/yr Sharpe 0.34, neutral 1175 days +20%/yr Sharpe 1.22, bear 606 days -13%/yr Sharpe -0.67, stress 278 days +9%/yr Sharpe 0.66

By strategy: Bollinger Breakout 79 trades -3,497 win 42%, Breakout Strategy 125 trades +59,494 win 35%, Donchian Breakout (Turtle) 141 trades +41,600 win 45%, EMA Crossover 13 trades -1,000 win 31%, Golden Cross (50/200) 8 trades +8,331 win 12%, MACD Crossover 94 trades -2,437 win 34%, MFI Money Flow (Volume) 2 trades +2,674 win 100%, Machine Learning Signal Combination 26 trades -249 win 31%, Mean Reversion 25 trades +4,720 win 84%, Momentum Strategy 71 trades +14,431 win 39%, Moving Average Crossover 4 trades -1,147 win 50%, Multi-Factor Strategy 43 trades -1,654 win 26%, OBV Trend (Volume) 84 trades -3,588 win 39%, Pairs Trading 1 trades +3,073 win 100%, Portfolio-Level Strategy 64 trades +24,107 win 36%, Regime-Based Strategy 66 trades -950 win 44%, Relative Strength Strategy 266 trades +17,184 win 44%, SMA Crossover 21 trades +4,343 win 57%, Statistical Arbitrage 7 trades +1,910 win 86%, Trend Following 60 trades +2,411 win 42%, VWAP Mean Reversion 27 trades +5,593 win 74%, VWAP Reclaim / Pullback 46 trades -3,643 win 26%, VWMA Crossover (Volume) 34 trades -5,311 win 29%, Volatility Breakout 195 trades -20,235 win 37%, Volume Breakout 210 trades +10,727 win 43%

### Momentum Leaders

Sectors (first day, sector): []

Closed trades 1797 · exits {'Signal': 1409, 'Stop Loss': 388} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2914, 'neutral': 1176, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2914 days +9%/yr Sharpe 0.52, neutral 1175 days +24%/yr Sharpe 1.30, bear 606 days -10%/yr Sharpe -0.48, stress 278 days +11%/yr Sharpe 0.75

By strategy: Bollinger Breakout 83 trades -8,215 win 45%, Breakout Strategy 151 trades +52,770 win 34%, Donchian Breakout (Turtle) 159 trades +109,411 win 46%, EMA Crossover 17 trades +3,788 win 29%, Golden Cross (50/200) 5 trades +24,465 win 40%, MACD Crossover 89 trades -10,431 win 26%, MFI Money Flow (Volume) 2 trades +1,663 win 50%, Machine Learning Signal Combination 31 trades -3,041 win 29%, Mean Reversion 28 trades +8,690 win 89%, Momentum Strategy 62 trades -77 win 26%, Moving Average Crossover 5 trades -51 win 20%, Multi-Factor Strategy 39 trades -4,116 win 31%, OBV Trend (Volume) 100 trades +9,082 win 40%, Portfolio-Level Strategy 50 trades +93,884 win 32%, Regime-Based Strategy 73 trades +3,795 win 49%, Relative Strength Strategy 275 trades +139,307 win 47%, SMA Crossover 27 trades -4,584 win 37%, Statistical Arbitrage 11 trades -4,976 win 45%, Trend Following 65 trades +8,638 win 48%, VWAP Mean Reversion 29 trades +7,779 win 83%, VWAP Reclaim / Pullback 56 trades -2,528 win 27%, VWMA Crossover (Volume) 42 trades -5,440 win 29%, Volatility Breakout 192 trades +15,382 win 38%, Volume Breakout 206 trades -39,134 win 35%

### Pullback Buyer

Sectors (first day, sector): []

Closed trades 3029 · exits {'Signal': 1583, 'Time Stop': 857, 'Stop Loss': 589} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2914, 'neutral': 1176, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2914 days +7%/yr Sharpe 0.43, neutral 1175 days +19%/yr Sharpe 1.12, bear 606 days -15%/yr Sharpe -0.81, stress 278 days +1%/yr Sharpe 0.06

By strategy: Bollinger Breakout 131 trades -10,062 win 33%, Breakout Strategy 251 trades +64,855 win 28%, Donchian Breakout (Turtle) 267 trades +25,929 win 36%, EMA Crossover 24 trades +4,720 win 38%, Golden Cross (50/200) 19 trades +9,820 win 16%, MACD Crossover 162 trades -6,720 win 33%, MFI Money Flow (Volume) 1 trades +855 win 100%, Machine Learning Signal Combination 45 trades -3,880 win 16%, Mean Reversion 56 trades +1,289 win 66%, Momentum Strategy 124 trades +16,813 win 27%, Moving Average Crossover 9 trades +4,030 win 44%, Multi-Factor Strategy 85 trades -4,684 win 24%, OBV Trend (Volume) 165 trades -6,907 win 34%, Portfolio-Level Strategy 92 trades +9,809 win 21%, RSI Mean Reversion 1 trades -105 win 0%, Regime-Based Strategy 111 trades -7,613 win 43%, Relative Strength Strategy 551 trades +59,164 win 33%, SMA Crossover 34 trades +554 win 29%, Statistical Arbitrage 17 trades +949 win 59%, Trend Following 86 trades +7,168 win 35%, VWAP Mean Reversion 55 trades +12,449 win 69%, VWAP Reclaim / Pullback 72 trades -1,338 win 22%, VWMA Crossover (Volume) 60 trades +3,835 win 37%, Volatility Breakout 298 trades -4,110 win 37%, Volume Breakout 313 trades -17,021 win 30%

