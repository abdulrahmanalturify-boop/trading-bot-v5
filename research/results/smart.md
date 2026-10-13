# Smart bots · period test

Run 2026-10-13 08:14 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 13 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **strong** · smart | -15% · -1.00 · -34% | +15% · 1.22 · -15% | +11% · 0.83 · -16% | +4% · 0.30 · -19% | +17% · 0.97 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +13% · 1.01 · -16% | +6% · 0.41 · -30% | +7% · 0.53 · -34% |
| strong · plain | -23% · -0.52 · -68% | +25% · 1.09 · -25% | +21% · 1.06 · -29% | +56% · 1.42 · -38% | +20% · 0.71 · -24% | -21% · -0.66 · -28% | +70% · 1.40 · -47% | +23% · 1.08 · -29% | +43% · 1.09 · -47% | +24% · 0.84 · -68% |
| strong · no_regime | -19% · -0.82 · -51% | +19% · 1.13 · -22% | +15% · 1.07 · -13% | -5% · -0.06 · -32% | +17% · 0.96 · -13% | -23% · -1.38 · -28% | +12% · 0.73 · -17% | +17% · 1.10 · -22% | +4% · 0.28 · -32% | +8% · 0.51 · -51% |
| strong · no_score | -17% · -1.15 · -34% | +15% · 1.30 · -12% | +10% · 0.79 · -16% | +8% · 0.43 · -19% | +17% · 0.96 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +13% · 1.02 · -16% | +7% · 0.43 · -30% | +7% · 0.53 · -34% |
| strong · no_selfcheck | -15% · -1.00 · -34% | +15% · 1.22 · -15% | +11% · 0.83 · -16% | +4% · 0.30 · -19% | +17% · 0.97 · -13% | -23% · -1.35 · -27% | +14% · 0.84 · -17% | +13% · 1.01 · -16% | +6% · 0.42 · -30% | +7% · 0.53 · -34% |
| strong · score_m10 | -12% · -0.64 · -35% | +19% · 1.18 · -22% | +10% · 0.79 · -16% | +9% · 0.47 · -19% | +19% · 1.05 · -13% | -23% · -1.38 · -28% | +14% · 0.83 · -17% | +15% · 1.00 · -22% | +7% · 0.46 · -30% | +9% · 0.59 · -35% |
| strong · score_p10 | -7% · -0.27 · -35% | +18% · 1.09 · -23% | +14% · 1.04 · -14% | +8% · 0.44 · -19% | +19% · 1.05 · -13% | -23% · -1.36 · -28% | +14% · 0.84 · -17% | +16% · 1.06 · -23% | +7% · 0.46 · -30% | +10% · 0.66 · -35% |
| strong · first_combo | -15% · -1.02 · -34% | +15% · 1.24 · -15% | +10% · 0.76 · -17% | +2% · 0.19 · -16% | +19% · 1.05 · -13% | -24% · -1.42 · -28% | +12% · 0.77 · -17% | +12% · 0.98 · -17% | +5% · 0.37 · -31% | +6% · 0.49 · -34% |
| strong · risk_moderate | -2% · -0.17 · -13% | +12% · 0.89 · -18% | +4% · 0.42 · -21% | -1% · 0.02 · -12% | +9% · 0.75 · -11% | -13% · -1.51 · -14% | +7% · 0.54 · -17% | +8% · 0.68 · -21% | +3% · 0.29 · -18% | +5% · 0.47 · -23% |
| strong · risk_conservative | -1% · -0.12 · -9% | +12% · 1.00 · -13% | +4% · 0.49 · -19% | +1% · 0.17 · -7% | +4% · 0.54 · -5% | -6% · -1.31 · -7% | +5% · 0.46 · -16% | +8% · 0.78 · -19% | +2% · 0.30 · -16% | +5% · 0.55 · -19% |
| strong · combo_back | +5% · 0.35 · -17% | +9% · 0.66 · -19% | +12% · 0.91 · -18% | +18% · 1.06 · -18% | +7% · 0.46 · -13% | -10% · -0.55 · -19% | +19% · 1.11 · -22% | +11% · 0.77 · -23% | +12% · 0.74 · -24% | +11% · 0.70 · -24% |
| strong · pos5 | -21% · -1.14 · -44% | +16% · 0.95 · -25% | +10% · 0.70 · -16% | +13% · 0.63 · -17% | +13% · 0.71 · -14% | -28% · -1.50 · -33% | +24% · 1.18 · -19% | +13% · 0.83 · -25% | +11% · 0.60 · -33% | +8% · 0.52 · -46% |
| strong · pos7 | -18% · -0.99 · -41% | +15% · 0.94 · -26% | +11% · 0.75 · -17% | +7% · 0.39 · -16% | +10% · 0.64 · -14% | -28% · -1.61 · -31% | +13% · 0.78 · -17% | +13% · 0.85 · -26% | +4% · 0.31 · -32% | +6% · 0.43 · -41% |
| |  | | | | | | | | | |
| **adaptive** · smart | -10% · -0.63 · -32% | +13% · 0.94 · -15% | +5% · 0.44 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +16% · 0.86 · -18% | +9% · 0.69 · -20% | +8% · 0.50 · -30% | +7% · 0.47 · -32% |
| adaptive · plain | -20% · -0.32 · -64% | +29% · 1.18 · -22% | +17% · 0.90 · -27% | +115% · 2.03 · -42% | +18% · 0.67 · -27% | -23% · -0.70 · -30% | +67% · 1.57 · -34% | +23% · 1.04 · -27% | +47% · 1.24 · -42% | +26% · 0.90 · -64% |
| adaptive · no_regime | -15% · -0.61 · -43% | +17% · 1.03 · -18% | +8% · 0.63 · -20% | +23% · 0.91 · -27% | -0% · 0.06 · -15% | -20% · -1.21 · -25% | +17% · 0.90 · -18% | +12% · 0.84 · -20% | +8% · 0.50 · -30% | +8% · 0.51 · -43% |
| adaptive · no_score | -10% · -0.58 · -32% | +13% · 0.92 · -15% | +5% · 0.44 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +16% · 0.86 · -18% | +9% · 0.68 · -20% | +8% · 0.50 · -30% | +7% · 0.47 · -32% |
| adaptive · no_selfcheck | -10% · -0.63 · -32% | +13% · 0.93 · -16% | +5% · 0.44 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +16% · 0.86 · -18% | +9% · 0.69 · -20% | +8% · 0.50 · -30% | +7% · 0.47 · -32% |
| adaptive · score_m10 | -10% · -0.59 · -32% | +13% · 0.93 · -15% | +5% · 0.44 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +16% · 0.86 · -18% | +9% · 0.69 · -20% | +8% · 0.50 · -30% | +7% · 0.47 · -32% |
| adaptive · score_p10 | -8% · -0.41 · -36% | +14% · 0.89 · -19% | +5% · 0.39 · -20% | +15% · 0.79 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +16% · 0.86 · -18% | +9% · 0.66 · -20% | +8% · 0.49 · -30% | +7% · 0.48 · -36% |
| adaptive · first_combo | -6% · -0.33 · -31% | +15% · 1.02 · -20% | +6% · 0.51 · -19% | +18% · 0.85 · -14% | +13% · 0.65 · -16% | -20% · -1.11 · -25% | +15% · 0.87 · -17% | +11% · 0.78 · -20% | +9% · 0.54 · -30% | +8% · 0.56 · -31% |
| adaptive · risk_moderate | +2% · 0.23 · -13% | +11% · 0.84 · -19% | +4% · 0.36 · -16% | +29% · 1.29 · -13% | +9% · 0.56 · -10% | -11% · -0.94 · -15% | +16% · 0.87 · -18% | +7% · 0.62 · -19% | +12% · 0.69 · -23% | +9% · 0.62 · -23% |
| adaptive · risk_conservative | +0% · 0.04 · -8% | +3% · 0.33 · -13% | +6% · 0.61 · -13% | +15% · 1.00 · -11% | +10% · 0.68 · -11% | -2% · -0.14 · -7% | +4% · 0.37 · -16% | +4% · 0.46 · -14% | +5% · 0.45 · -16% | +4% · 0.44 · -16% |
| adaptive · pos5 | -3% · -0.09 · -28% | +15% · 0.82 · -27% | +5% · 0.41 · -22% | +18% · 0.80 · -15% | +26% · 1.32 · -10% | -24% · -1.32 · -28% | +8% · 0.61 · -16% | +10% · 0.63 · -27% | +6% · 0.40 · -32% | +7% · 0.48 · -32% |
| adaptive · pos7 | -4% · -0.20 · -31% | +13% · 0.77 · -20% | +9% · 0.66 · -19% | +19% · 0.88 · -14% | +9% · 0.60 · -12% | -22% · -1.13 · -26% | +26% · 1.17 · -17% | +11% · 0.72 · -20% | +13% · 0.70 · -30% | +10% · 0.62 · -31% |
| |  | | | | | | | | | |
| **trend** · smart | -9% · -0.53 · -31% | +13% · 0.82 · -30% | +9% · 0.65 · -18% | +14% · 0.72 · -16% | +7% · 0.52 · -14% | -22% · -1.30 · -24% | +17% · 0.97 · -15% | +11% · 0.74 · -30% | +8% · 0.50 · -30% | +8% · 0.52 · -31% |
| trend · plain | -20% · -0.32 · -64% | +29% · 1.18 · -22% | +17% · 0.90 · -27% | +115% · 2.03 · -42% | +18% · 0.67 · -27% | -23% · -0.70 · -30% | +67% · 1.57 · -34% | +23% · 1.04 · -27% | +47% · 1.24 · -42% | +26% · 0.90 · -64% |
| trend · no_regime | -15% · -0.66 · -46% | +18% · 1.04 · -20% | +10% · 0.74 · -19% | +19% · 0.78 · -28% | +10% · 0.63 · -9% | -23% · -1.31 · -25% | +11% · 0.65 · -21% | +14% · 0.90 · -20% | +5% · 0.37 · -30% | +7% · 0.49 · -46% |
| trend · no_score | -10% · -0.65 · -33% | +12% · 0.84 · -18% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +7% · 0.52 · -14% | -22% · -1.30 · -24% | +17% · 0.97 · -15% | +10% · 0.73 · -19% | +8% · 0.50 · -30% | +7% · 0.50 · -33% |
| trend · no_selfcheck | -9% · -0.53 · -31% | +13% · 0.82 · -30% | +9% · 0.65 · -18% | +14% · 0.72 · -16% | +7% · 0.52 · -14% | -22% · -1.30 · -24% | +17% · 0.97 · -15% | +11% · 0.74 · -30% | +8% · 0.50 · -30% | +8% · 0.52 · -31% |
| trend · score_m10 | -10% · -0.65 · -33% | +12% · 0.84 · -18% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +7% · 0.52 · -14% | -22% · -1.30 · -24% | +17% · 0.97 · -15% | +10% · 0.73 · -19% | +8% · 0.50 · -30% | +7% · 0.50 · -33% |
| trend · score_p10 | -10% · -0.67 · -31% | +12% · 0.77 · -31% | +8% · 0.61 · -19% | +11% · 0.62 · -17% | +7% · 0.46 · -12% | -21% · -1.18 · -24% | +15% · 0.91 · -16% | +10% · 0.69 · -31% | +7% · 0.45 · -31% | +6% · 0.46 · -31% |
| trend · first_combo | -8% · -0.52 · -32% | +14% · 0.98 · -18% | +9% · 0.69 · -21% | +17% · 0.80 · -14% | +23% · 1.16 · -9% | -25% · -1.34 · -26% | +14% · 0.83 · -18% | +12% · 0.84 · -24% | +9% · 0.53 · -31% | +8% · 0.57 · -32% |
| trend · risk_moderate | -5% · -0.73 · -16% | +12% · 0.98 · -16% | +3% · 0.29 · -18% | +13% · 0.82 · -15% | +6% · 0.40 · -13% | -15% · -1.38 · -16% | +9% · 0.60 · -20% | +7% · 0.65 · -18% | +5% · 0.36 · -21% | +5% · 0.45 · -21% |
| trend · risk_conservative | -1% · -0.20 · -7% | +5% · 0.52 · -15% | +3% · 0.32 · -14% | +4% · 0.40 · -6% | +7% · 0.57 · -9% | -10% · -2.00 · -10% | +3% · 0.32 · -16% | +4% · 0.43 · -15% | +1% · 0.18 · -16% | +2% · 0.30 · -16% |
| trend · pos5 | -10% · -0.55 · -34% | +15% · 0.92 · -20% | +2% · 0.22 · -27% | +12% · 0.61 · -15% | +17% · 0.87 · -13% | -26% · -1.47 · -30% | +27% · 1.28 · -17% | +9% · 0.59 · -27% | +13% · 0.69 · -36% | +8% · 0.52 · -36% |
| trend · pos7 | -11% · -0.68 · -34% | +12% · 0.83 · -21% | +7% · 0.52 · -23% | +26% · 1.07 · -16% | +14% · 0.79 · -12% | -25% · -1.44 · -27% | +24% · 1.19 · -15% | +10% · 0.68 · -23% | +13% · 0.72 · -34% | +9% · 0.57 · -34% |
| |  | | | | | | | | | |
| **momentum** · smart | -13% · -0.81 · -33% | +9% · 0.70 · -16% | +10% · 0.72 · -19% | +10% · 0.54 · -22% | +27% · 1.33 · -10% | -29% · -1.88 · -29% | +15% · 0.81 · -24% | +9% · 0.71 · -23% | +8% · 0.47 · -30% | +6% · 0.45 · -33% |
| momentum · plain | -20% · -0.32 · -64% | +29% · 1.18 · -22% | +17% · 0.90 · -27% | +115% · 2.03 · -42% | +18% · 0.67 · -27% | -23% · -0.70 · -30% | +67% · 1.57 · -34% | +23% · 1.04 · -27% | +47% · 1.24 · -42% | +26% · 0.90 · -64% |
| momentum · no_regime | -18% · -0.70 · -51% | +18% · 1.06 · -21% | +10% · 0.73 · -26% | +22% · 0.84 · -27% | +15% · 0.80 · -15% | -20% · -1.04 · -25% | +13% · 0.69 · -23% | +14% · 0.90 · -26% | +8% · 0.48 · -28% | +8% · 0.51 · -51% |
| momentum · no_score | -12% · -0.77 · -32% | +8% · 0.68 · -16% | +10% · 0.72 · -19% | +10% · 0.54 · -22% | +27% · 1.33 · -10% | -29% · -1.88 · -29% | +15% · 0.81 · -24% | +9% · 0.70 · -23% | +8% · 0.47 · -30% | +6% · 0.45 · -32% |
| momentum · no_selfcheck | -13% · -0.81 · -33% | +10% · 0.73 · -18% | +10% · 0.72 · -19% | +10% · 0.54 · -22% | +27% · 1.33 · -10% | -29% · -1.88 · -29% | +15% · 0.81 · -24% | +10% · 0.73 · -23% | +8% · 0.47 · -30% | +6% · 0.46 · -33% |
| momentum · score_m10 | -12% · -0.77 · -32% | +8% · 0.68 · -16% | +10% · 0.72 · -19% | +10% · 0.54 · -22% | +27% · 1.33 · -10% | -29% · -1.88 · -29% | +15% · 0.81 · -24% | +9% · 0.70 · -23% | +8% · 0.47 · -30% | +6% · 0.45 · -32% |
| momentum · score_p10 | -11% · -0.70 · -32% | +9% · 0.66 · -21% | +12% · 0.85 · -19% | +10% · 0.54 · -22% | +27% · 1.33 · -10% | -29% · -1.88 · -29% | +15% · 0.81 · -24% | +10% · 0.75 · -23% | +8% · 0.47 · -30% | +7% · 0.49 · -32% |
| momentum · first_combo | -11% · -0.71 · -36% | +9% · 0.70 · -22% | +11% · 0.85 · -18% | +23% · 1.01 · -19% | +28% · 1.36 · -11% | -23% · -1.28 · -25% | +15% · 0.85 · -20% | +10% · 0.78 · -22% | +11% · 0.63 · -29% | +8% · 0.56 · -36% |
| momentum · risk_moderate | -2% · -0.28 · -13% | +9% · 0.74 · -14% | +6% · 0.50 · -18% | +22% · 1.03 · -16% | +28% · 1.45 · -10% | -14% · -1.01 · -15% | +26% · 1.06 · -26% | +7% · 0.62 · -18% | +18% · 0.88 · -26% | +10% · 0.68 · -26% |
| momentum · risk_conservative | +0% · 0.07 · -10% | +5% · 0.48 · -12% | +2% · 0.35 · -14% | +14% · 1.08 · -6% | +33% · 1.33 · -13% | -10% · -1.10 · -12% | +11% · 0.81 · -17% | +4% · 0.42 · -15% | +11% · 0.76 · -17% | +6% · 0.55 · -17% |
| momentum · pos5 | -10% · -0.52 · -31% | +9% · 0.66 · -25% | +6% · 0.44 · -23% | +20% · 0.89 · -18% | +5% · 0.34 · -23% | -22% · -1.05 · -26% | +42% · 1.56 · -18% | +7% · 0.55 · -30% | +21% · 0.91 · -33% | +10% · 0.60 · -33% |
| momentum · pos7 | -16% · -0.76 · -44% | +15% · 0.87 · -21% | +9% · 0.62 · -23% | +12% · 0.62 · -15% | +32% · 1.42 · -10% | -25% · -1.42 · -27% | +19% · 0.93 · -22% | +12% · 0.75 · -23% | +11% · 0.61 · -31% | +8% · 0.52 · -44% |
| |  | | | | | | | | | |
| **pullback** · smart | -13% · -0.84 · -36% | +11% · 0.72 · -23% | +12% · 0.92 · -18% | +23% · 1.07 · -14% | +26% · 1.35 · -9% | -25% · -1.64 · -28% | +23% · 1.10 · -15% | +12% · 0.81 · -23% | +14% · 0.78 · -28% | +10% · 0.63 · -36% |
| pullback · plain | -26% · -0.59 · -65% | +17% · 0.81 · -24% | +17% · 0.93 · -31% | +27% · 0.83 · -46% | +34% · 1.04 · -22% | -34% · -1.37 · -37% | +74% · 1.65 · -39% | +17% · 0.86 · -31% | +39% · 1.09 · -46% | +18% · 0.72 · -65% |
| pullback · no_regime | -23% · -1.27 · -47% | +18% · 1.06 · -24% | +12% · 0.88 · -19% | +30% · 1.06 · -26% | +29% · 1.53 · -9% | -22% · -1.42 · -26% | +22% · 1.00 · -17% | +15% · 0.97 · -24% | +16% · 0.78 · -28% | +10% · 0.63 · -47% |
| pullback · no_score | -12% · -0.86 · -31% | +11% · 0.99 · -12% | +12% · 0.92 · -18% | +23% · 1.07 · -14% | +26% · 1.35 · -9% | -25% · -1.64 · -28% | +23% · 1.10 · -15% | +12% · 0.95 · -18% | +14% · 0.78 · -28% | +10% · 0.68 · -31% |
| pullback · no_selfcheck | -10% · -0.70 · -33% | +16% · 1.08 · -22% | +13% · 0.93 · -18% | +23% · 1.07 · -14% | +26% · 1.35 · -9% | -25% · -1.64 · -28% | +23% · 1.10 · -15% | +14% · 1.01 · -22% | +14% · 0.78 · -28% | +11% · 0.74 · -33% |
| pullback · score_m10 | -12% · -0.87 · -31% | +12% · 0.99 · -12% | +12% · 0.92 · -18% | +23% · 1.07 · -14% | +26% · 1.35 · -9% | -25% · -1.64 · -28% | +23% · 1.10 · -15% | +12% · 0.95 · -18% | +14% · 0.78 · -28% | +10% · 0.69 · -31% |
| pullback · score_p10 | -9% · -0.52 · -36% | +12% · 0.77 · -22% | +12% · 0.92 · -18% | +23% · 1.07 · -14% | +26% · 1.35 · -9% | -25% · -1.64 · -28% | +23% · 1.10 · -15% | +12% · 0.83 · -22% | +14% · 0.78 · -28% | +11% · 0.68 · -36% |
| pullback · first_combo | -11% · -0.72 · -33% | +11% · 0.85 · -20% | +8% · 0.66 · -18% | +25% · 1.11 · -17% | +29% · 1.47 · -11% | -24% · -1.47 · -28% | +21% · 1.10 · -15% | +9% · 0.75 · -20% | +14% · 0.79 · -28% | +9% · 0.62 · -33% |
| pullback · risk_moderate | -3% · -0.54 · -15% | +12% · 0.98 · -14% | +9% · 0.73 · -16% | +8% · 0.52 · -14% | +21% · 1.14 · -11% | -17% · -2.17 · -18% | +20% · 1.09 · -14% | +10% · 0.85 · -16% | +12% · 0.72 · -22% | +9% · 0.71 · -22% |
| pullback · risk_conservative | +2% · 0.42 · -6% | +2% · 0.26 · -16% | +0% · 0.09 · -11% | +10% · 0.77 · -11% | +32% · 1.27 · -15% | -11% · -2.24 · -11% | +10% · 0.74 · -13% | +1% · 0.19 · -17% | +9% · 0.67 · -17% | +4% · 0.43 · -17% |
| pullback · pos5 | -13% · -0.76 · -40% | +24% · 1.27 · -21% | +10% · 0.65 · -17% | +9% · 0.52 · -15% | +8% · 0.50 · -13% | -33% · -2.22 · -35% | +23% · 0.94 · -26% | +16% · 0.97 · -21% | +8% · 0.46 · -40% | +10% · 0.59 · -40% |
| pullback · pos7 | -15% · -1.04 · -40% | +21% · 1.18 · -19% | +11% · 0.77 · -17% | +14% · 0.70 · -17% | +13% · 0.80 · -11% | -27% · -1.82 · -31% | +9% · 0.59 · -21% | +16% · 0.99 · -19% | +4% · 0.29 · -34% | +8% · 0.54 · -40% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.44 · -19% | +13% · 0.92 · -19% | +15% · 0.82 · -34% | +11% · 0.65 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.13 · -20% | +21% · 0.72 · -38% | +34% · 2.15 · -6% | -10% · -0.37 · -20% | +27% · 1.37 · -23% | +18% · 1.16 · -21% | +18% · 0.87 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| strong · smart | +13% | 1.01 | -16% | 85% | +6% | 0.41 | -30% | 88% |
| strong · plain | +23% | 1.08 | -29% | 99% | +43% | 1.09 | -47% | 98% |
| strong · no_regime | +17% | 1.10 | -22% | 99% | +4% | 0.28 | -32% | 90% |
| strong · no_score | +13% | 1.02 | -16% | 83% | +7% | 0.43 | -30% | 89% |
| strong · no_selfcheck | +13% | 1.01 | -16% | 85% | +6% | 0.42 | -30% | 89% |
| strong · score_m10 | +15% | 1.00 | -22% | 96% | +7% | 0.46 | -30% | 89% |
| strong · score_p10 | +16% | 1.06 | -23% | 96% | +7% | 0.46 | -30% | 89% |
| strong · first_combo | +12% | 0.98 | -17% | 83% | +5% | 0.37 | -31% | 86% |
| strong · risk_moderate | +8% | 0.68 | -21% | 75% | +3% | 0.29 | -18% | 64% |
| strong · risk_conservative | +8% | 0.78 | -19% | 66% | +2% | 0.30 | -16% | 41% |
| strong · combo_back | +11% | 0.77 | -23% | 64% | +12% | 0.74 | -24% | 71% |
| strong · pos5 | +13% | 0.83 | -25% | 96% | +11% | 0.60 | -33% | 87% |
| strong · pos7 | +13% | 0.85 | -26% | 97% | +4% | 0.31 | -32% | 86% |
| adaptive · smart | +9% | 0.69 | -20% | 92% | +8% | 0.50 | -30% | 90% |
| adaptive · plain | +23% | 1.04 | -27% | 99% | +47% | 1.24 | -42% | 99% |
| adaptive · no_regime | +12% | 0.84 | -20% | 98% | +8% | 0.50 | -30% | 92% |
| adaptive · no_score | +9% | 0.68 | -20% | 92% | +8% | 0.50 | -30% | 90% |
| adaptive · no_selfcheck | +9% | 0.69 | -20% | 93% | +8% | 0.50 | -30% | 90% |
| adaptive · score_m10 | +9% | 0.69 | -20% | 92% | +8% | 0.50 | -30% | 90% |
| adaptive · score_p10 | +9% | 0.66 | -20% | 98% | +8% | 0.49 | -30% | 90% |
| adaptive · first_combo | +11% | 0.78 | -20% | 95% | +9% | 0.54 | -30% | 88% |
| adaptive · risk_moderate | +7% | 0.62 | -19% | 85% | +12% | 0.69 | -23% | 71% |
| adaptive · risk_conservative | +4% | 0.46 | -14% | 62% | +5% | 0.45 | -16% | 66% |
| adaptive · pos5 | +10% | 0.63 | -27% | 96% | +6% | 0.40 | -32% | 78% |
| adaptive · pos7 | +11% | 0.72 | -20% | 97% | +13% | 0.70 | -30% | 91% |
| trend · smart | +11% | 0.74 | -30% | 95% | +8% | 0.50 | -30% | 86% |
| trend · plain | +23% | 1.04 | -27% | 99% | +47% | 1.24 | -42% | 99% |
| trend · no_regime | +14% | 0.90 | -20% | 99% | +5% | 0.37 | -30% | 87% |
| trend · no_score | +10% | 0.73 | -19% | 92% | +8% | 0.50 | -30% | 86% |
| trend · no_selfcheck | +11% | 0.74 | -30% | 95% | +8% | 0.50 | -30% | 86% |
| trend · score_m10 | +10% | 0.73 | -19% | 92% | +8% | 0.50 | -30% | 86% |
| trend · score_p10 | +10% | 0.69 | -31% | 93% | +7% | 0.45 | -31% | 83% |
| trend · first_combo | +12% | 0.84 | -24% | 93% | +9% | 0.53 | -31% | 85% |
| trend · risk_moderate | +7% | 0.65 | -18% | 78% | +5% | 0.36 | -21% | 71% |
| trend · risk_conservative | +4% | 0.43 | -15% | 54% | +1% | 0.18 | -16% | 50% |
| trend · pos5 | +9% | 0.59 | -27% | 91% | +13% | 0.69 | -36% | 84% |
| trend · pos7 | +10% | 0.68 | -23% | 91% | +13% | 0.72 | -34% | 85% |
| momentum · smart | +9% | 0.71 | -23% | 85% | +8% | 0.47 | -30% | 89% |
| momentum · plain | +23% | 1.04 | -27% | 99% | +47% | 1.24 | -42% | 99% |
| momentum · no_regime | +14% | 0.90 | -26% | 99% | +8% | 0.48 | -28% | 97% |
| momentum · no_score | +9% | 0.70 | -23% | 85% | +8% | 0.47 | -30% | 89% |
| momentum · no_selfcheck | +10% | 0.73 | -23% | 89% | +8% | 0.47 | -30% | 89% |
| momentum · score_m10 | +9% | 0.70 | -23% | 85% | +8% | 0.47 | -30% | 89% |
| momentum · score_p10 | +10% | 0.75 | -23% | 89% | +8% | 0.47 | -30% | 89% |
| momentum · first_combo | +10% | 0.78 | -22% | 88% | +11% | 0.63 | -29% | 92% |
| momentum · risk_moderate | +7% | 0.62 | -18% | 77% | +18% | 0.88 | -26% | 82% |
| momentum · risk_conservative | +4% | 0.42 | -15% | 56% | +11% | 0.76 | -17% | 56% |
| momentum · pos5 | +7% | 0.55 | -30% | 85% | +21% | 0.91 | -33% | 87% |
| momentum · pos7 | +12% | 0.75 | -23% | 98% | +11% | 0.61 | -31% | 89% |
| pullback · smart | +12% | 0.81 | -23% | 97% | +14% | 0.78 | -28% | 91% |
| pullback · plain | +17% | 0.86 | -31% | 98% | +39% | 1.09 | -46% | 98% |
| pullback · no_regime | +15% | 0.97 | -24% | 98% | +16% | 0.78 | -28% | 96% |
| pullback · no_score | +12% | 0.95 | -18% | 85% | +14% | 0.78 | -28% | 91% |
| pullback · no_selfcheck | +14% | 1.01 | -22% | 93% | +14% | 0.78 | -28% | 91% |
| pullback · score_m10 | +12% | 0.95 | -18% | 85% | +14% | 0.78 | -28% | 91% |
| pullback · score_p10 | +12% | 0.83 | -22% | 97% | +14% | 0.78 | -28% | 91% |
| pullback · first_combo | +9% | 0.75 | -20% | 90% | +14% | 0.79 | -28% | 92% |
| pullback · risk_moderate | +10% | 0.85 | -16% | 78% | +12% | 0.72 | -22% | 72% |
| pullback · risk_conservative | +1% | 0.19 | -17% | 45% | +9% | 0.67 | -17% | 55% |
| pullback · pos5 | +16% | 0.97 | -21% | 97% | +8% | 0.46 | -40% | 84% |
| pullback · pos7 | +16% | 0.99 | -19% | 97% | +4% | 0.29 | -34% | 73% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.87 / 0.82 | -38% / -34% | | | | | |

## Inside each smart bot

### Strong Stocks on Sale

Sectors (first day, sector): []

Closed trades 2205 · exits {'Signal': 1795, 'Stop Loss': 410} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +8%/yr Sharpe 0.55, neutral 1178 days +23%/yr Sharpe 1.44, bear 606 days -17%/yr Sharpe -0.90, stress 278 days +11%/yr Sharpe 0.93

By strategy: Donchian Breakout (Turtle) 1712 trades +235,673 win 40%, Mean Reversion & Multi-Factor Strategy & Regime-Based Strategy & Portfolio-Level Strategy (4/4) 88 trades +1,431 win 57%, Momentum Strategy & VWAP Mean Reversion & Multi-Factor Strategy (3/3) 50 trades +11,356 win 68%, VWAP Mean Reversion & Multi-Factor Strategy & Momentum Strategy & Portfolio-Level Strategy (4/4) 42 trades +7,839 win 57%, VWAP Mean Reversion & RSI Mean Reversion & Relative Strength Strategy & Portfolio-Level Strategy (3/4) 209 trades +38,259 win 63%, VWAP Mean Reversion & Statistical Arbitrage & Multi-Factor Strategy & Relative Strength Strategy (3/4) 104 trades +5,396 win 63%

### Adaptive All-Weather

Sectors (first day, sector): []

Closed trades 1713 · exits {'Signal': 1349, 'Stop Loss': 364} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +5%/yr Sharpe 0.35, neutral 1178 days +20%/yr Sharpe 1.22, bear 606 days -11%/yr Sharpe -0.55, stress 278 days +13%/yr Sharpe 1.02

By strategy: Bollinger Breakout 66 trades -12,604 win 33%, Breakout Strategy 124 trades +12,456 win 29%, Donchian Breakout (Turtle) 133 trades +18,507 win 46%, EMA Crossover 16 trades -4,309 win 25%, Golden Cross (50/200) 6 trades +11,245 win 17%, MACD Crossover 94 trades +598 win 37%, MFI Money Flow (Volume) 3 trades +5,683 win 67%, Machine Learning Signal Combination 21 trades +1,125 win 29%, Mean Reversion 25 trades +6,800 win 100%, Momentum Strategy 80 trades +8,083 win 35%, Moving Average Crossover 11 trades +9,127 win 45%, Multi-Factor Strategy 40 trades -787 win 25%, OBV Trend (Volume) 104 trades -355 win 38%, Pairs Trading 1 trades +377 win 100%, Portfolio-Level Strategy 64 trades +63,888 win 36%, Regime-Based Strategy 65 trades -146 win 48%, Relative Strength Strategy 250 trades +72,040 win 44%, SMA Crossover 22 trades +436 win 41%, Statistical Arbitrage 9 trades +2,021 win 67%, Trend Following 54 trades +3,910 win 39%, VWAP Mean Reversion 29 trades +6,061 win 76%, VWAP Reclaim / Pullback 46 trades +3,343 win 30%, VWMA Crossover (Volume) 44 trades -2,997 win 30%, Volatility Breakout 196 trades -17,214 win 38%, Volume Breakout 210 trades +17,033 win 39%

### Trend Rider

Sectors (first day, sector): []

Closed trades 1711 · exits {'Signal': 1346, 'Stop Loss': 365} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +7%/yr Sharpe 0.44, neutral 1178 days +23%/yr Sharpe 1.36, bear 606 days -13%/yr Sharpe -0.65, stress 278 days +9%/yr Sharpe 0.60

By strategy: Bollinger Breakout 81 trades +1,679 win 43%, Breakout Strategy 116 trades +115,800 win 34%, Donchian Breakout (Turtle) 145 trades +32,854 win 45%, EMA Crossover 12 trades -1,536 win 33%, Golden Cross (50/200) 7 trades +8,832 win 14%, MACD Crossover 106 trades +542 win 32%, MFI Money Flow (Volume) 3 trades +2,250 win 67%, Machine Learning Signal Combination 26 trades -463 win 35%, Mean Reversion 24 trades +5,160 win 83%, Momentum Strategy 70 trades +9,462 win 36%, Moving Average Crossover 5 trades -1,474 win 40%, Multi-Factor Strategy 45 trades -3,596 win 24%, OBV Trend (Volume) 80 trades +4,283 win 41%, Pairs Trading 1 trades +3,298 win 100%, Portfolio-Level Strategy 60 trades +69,991 win 38%, RSI Mean Reversion 1 trades +1,163 win 100%, Regime-Based Strategy 63 trades -2,185 win 43%, Relative Strength Strategy 263 trades +13,857 win 42%, SMA Crossover 19 trades +115 win 47%, Statistical Arbitrage 6 trades -1,236 win 67%, Trend Following 62 trades +406 win 44%, VWAP Mean Reversion 28 trades +6,489 win 71%, VWAP Reclaim / Pullback 48 trades -8,335 win 25%, VWMA Crossover (Volume) 40 trades -3,610 win 32%, Volatility Breakout 195 trades -15,402 win 39%, Volume Breakout 205 trades +18,585 win 42%

### Momentum Leaders

Sectors (first day, sector): []

Closed trades 1804 · exits {'Signal': 1395, 'Stop Loss': 409} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +8%/yr Sharpe 0.49, neutral 1178 days +22%/yr Sharpe 1.32, bear 606 days -25%/yr Sharpe -1.26, stress 278 days +17%/yr Sharpe 1.16

By strategy: Bollinger Breakout 79 trades -11,164 win 38%, Breakout Strategy 143 trades +39,495 win 34%, Donchian Breakout (Turtle) 168 trades +75,486 win 43%, EMA Crossover 12 trades +4,105 win 42%, Golden Cross (50/200) 4 trades -4,468 win 0%, MACD Crossover 94 trades -8,381 win 29%, Machine Learning Signal Combination 32 trades +7,931 win 44%, Mean Reversion 24 trades +7,661 win 83%, Momentum Strategy 70 trades +10,256 win 37%, Moving Average Crossover 6 trades -2,086 win 17%, Multi-Factor Strategy 49 trades -4,007 win 37%, OBV Trend (Volume) 109 trades +13,075 win 41%, Portfolio-Level Strategy 56 trades +6,049 win 34%, Regime-Based Strategy 70 trades +4,244 win 59%, Relative Strength Strategy 274 trades +76,468 win 43%, SMA Crossover 23 trades -2,337 win 39%, Statistical Arbitrage 7 trades +412 win 57%, Trend Following 61 trades +15,732 win 48%, VWAP Mean Reversion 27 trades +4,145 win 81%, VWAP Reclaim / Pullback 55 trades +2,058 win 27%, VWMA Crossover (Volume) 39 trades -1,980 win 36%, Volatility Breakout 187 trades +19,890 win 39%, Volume Breakout 215 trades -40,698 win 37%

### Pullback Buyer

Sectors (first day, sector): []

Closed trades 3097 · exits {'Signal': 1643, 'Time Stop': 860, 'Stop Loss': 594} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +10%/yr Sharpe 0.59, neutral 1178 days +23%/yr Sharpe 1.29, bear 606 days -11%/yr Sharpe -0.56, stress 278 days +9%/yr Sharpe 0.76

By strategy: Bollinger Breakout 138 trades -8,683 win 37%, Breakout Strategy 269 trades +238,651 win 26%, Donchian Breakout (Turtle) 254 trades +44,229 win 35%, EMA Crossover 28 trades +7,387 win 43%, Golden Cross (50/200) 20 trades +4,299 win 15%, MACD Crossover 169 trades +1,138 win 37%, MFI Money Flow (Volume) 1 trades +1,016 win 100%, Machine Learning Signal Combination 49 trades +1,784 win 27%, Mean Reversion 57 trades -2,049 win 61%, Momentum Strategy 129 trades +9,430 win 23%, Moving Average Crossover 8 trades +4,280 win 38%, Multi-Factor Strategy 85 trades +21 win 21%, OBV Trend (Volume) 190 trades +2,234 win 36%, Portfolio-Level Strategy 88 trades +6,533 win 20%, RSI Mean Reversion 1 trades +5,048 win 100%, Regime-Based Strategy 110 trades -110 win 49%, Relative Strength Strategy 553 trades +71,908 win 32%, SMA Crossover 33 trades -2,336 win 27%, Statistical Arbitrage 17 trades +1,251 win 59%, Trend Following 86 trades +24,035 win 37%, VWAP Mean Reversion 58 trades +18,628 win 67%, VWAP Reclaim / Pullback 76 trades -6,421 win 24%, VWMA Crossover (Volume) 65 trades +13,444 win 38%, Volatility Breakout 304 trades +35,736 win 41%, Volume Breakout 309 trades -38,063 win 32%

