# Smart bots · period test

Run 2026-10-12 19:41 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 14 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **strong** · smart | -13% · -0.86 · -34% | +15% · 1.16 · -21% | +9% · 0.72 · -17% | +4% · 0.30 · -19% | +17% · 0.97 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +12% · 0.94 · -21% | +6% · 0.42 · -30% | +7% · 0.52 · -34% |
| strong · plain | -24% · -0.55 · -68% | +25% · 1.11 · -22% | +15% · 0.81 · -34% | +31% · 0.94 · -38% | +17% · 0.70 · -23% | -21% · -0.64 · -28% | +70% · 1.38 · -51% | +20% · 0.96 · -34% | +38% · 1.01 · -51% | +21% · 0.76 · -68% |
| strong · no_regime | -20% · -0.87 · -51% | +19% · 1.15 · -22% | +14% · 0.96 · -13% | -12% · -0.33 · -30% | +17% · 0.96 · -13% | -23% · -1.29 · -27% | +12% · 0.71 · -17% | +16% · 1.06 · -22% | +2% · 0.22 · -30% | +7% · 0.46 · -51% |
| strong · no_score | -15% · -0.97 · -34% | +15% · 1.21 · -17% | +11% · 0.81 · -17% | +8% · 0.43 · -19% | +17% · 0.96 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +13% · 0.99 · -17% | +7% · 0.44 · -30% | +7% · 0.54 · -34% |
| strong · no_selfcheck | -13% · -0.86 · -34% | +15% · 1.16 · -21% | +9% · 0.72 · -17% | +4% · 0.30 · -19% | +17% · 0.97 · -13% | -22% · -1.25 · -27% | +14% · 0.83 · -17% | +12% · 0.94 · -21% | +6% · 0.43 · -29% | +7% · 0.52 · -34% |
| strong · score_m10 | -10% · -0.47 · -35% | +19% · 1.13 · -24% | +11% · 0.81 · -17% | +9% · 0.47 · -19% | +19% · 1.05 · -13% | -23% · -1.29 · -27% | +14% · 0.83 · -17% | +15% · 0.98 · -24% | +7% · 0.46 · -30% | +9% · 0.61 · -35% |
| strong · score_p10 | -6% · -0.23 · -34% | +18% · 1.10 · -23% | +9% · 0.72 · -17% | +8% · 0.44 · -19% | +19% · 1.05 · -13% | -24% · -1.35 · -28% | +13% · 0.82 · -17% | +13% · 0.92 · -23% | +7% · 0.43 · -31% | +9% · 0.59 · -34% |
| strong · first_combo | -13% · -0.84 · -33% | +13% · 1.08 · -19% | +9% · 0.68 · -18% | +2% · 0.19 · -16% | +19% · 1.05 · -13% | -24% · -1.36 · -28% | +12% · 0.77 · -17% | +11% · 0.86 · -19% | +5% · 0.37 · -30% | +6% · 0.46 · -33% |
| strong · risk_moderate | -1% · -0.12 · -13% | +12% · 0.92 · -20% | +4% · 0.39 · -20% | -1% · -0.01 · -12% | +9% · 0.75 · -11% | -12% · -1.49 · -14% | +7% · 0.53 · -17% | +8% · 0.68 · -20% | +3% · 0.29 · -17% | +5% · 0.47 · -23% |
| strong · risk_conservative | -1% · -0.11 · -9% | +10% · 0.83 · -13% | +4% · 0.46 · -19% | +1% · 0.17 · -7% | +4% · 0.54 · -5% | -6% · -1.31 · -7% | +5% · 0.48 · -16% | +7% · 0.66 · -19% | +3% · 0.31 · -16% | +4% · 0.48 · -19% |
| strong · combo_back | +5% · 0.33 · -17% | +9% · 0.66 · -19% | +12% · 0.91 · -18% | +18% · 1.06 · -18% | +7% · 0.46 · -13% | -10% · -0.55 · -19% | +19% · 1.11 · -22% | +11% · 0.78 · -23% | +12% · 0.74 · -24% | +11% · 0.70 · -24% |
| strong · pos5 | -17% · -0.88 · -44% | +19% · 1.07 · -25% | +10% · 0.67 · -16% | +13% · 0.63 · -17% | +13% · 0.71 · -14% | -26% · -1.33 · -31% | +23% · 1.15 · -19% | +14% · 0.88 · -25% | +11% · 0.62 · -31% | +9% · 0.58 · -44% |
| strong · pos7 | -16% · -0.83 · -41% | +19% · 1.10 · -25% | +10% · 0.72 · -17% | +7% · 0.39 · -16% | +10% · 0.64 · -14% | -26% · -1.47 · -29% | +18% · 0.95 · -16% | +14% · 0.92 · -25% | +7% · 0.45 · -30% | +8% · 0.54 · -41% |
| |  | | | | | | | | | |
| **adaptive** · smart | -7% · -0.36 · -35% | +12% · 0.76 · -20% | +10% · 0.74 · -20% | +16% · 0.83 · -15% | +8% · 0.51 · -12% | -22% · -1.26 · -26% | +17% · 0.89 · -18% | +11% · 0.75 · -20% | +8% · 0.52 · -30% | +8% · 0.54 · -35% |
| adaptive · plain | -23% · -0.39 · -65% | +22% · 0.98 · -25% | +14% · 0.76 · -32% | +110% · 1.96 · -42% | +10% · 0.44 · -25% | -24% · -0.77 · -31% | +67% · 1.53 · -38% | +18% · 0.88 · -32% | +45% · 1.18 · -42% | +22% · 0.79 · -65% |
| adaptive · no_regime | -14% · -0.58 · -42% | +16% · 1.00 · -19% | +7% · 0.57 · -21% | +24% · 0.93 · -27% | -1% · 0.05 · -15% | -20% · -1.21 · -25% | +19% · 1.00 · -18% | +12% · 0.80 · -21% | +10% · 0.56 · -30% | +8% · 0.52 · -42% |
| adaptive · no_score | -11% · -0.70 · -33% | +11% · 0.89 · -12% | +6% · 0.47 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +17% · 0.89 · -18% | +8% · 0.67 · -20% | +8% · 0.52 · -30% | +6% · 0.46 · -33% |
| adaptive · no_selfcheck | -12% · -0.76 · -34% | +11% · 0.89 · -11% | +6% · 0.47 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +17% · 0.89 · -18% | +8% · 0.68 · -20% | +8% · 0.52 · -30% | +6% · 0.46 · -34% |
| adaptive · score_m10 | -11% · -0.71 · -34% | +11% · 0.88 · -12% | +6% · 0.47 · -20% | +16% · 0.82 · -15% | +7% · 0.51 · -12% | -22% · -1.26 · -26% | +17% · 0.89 · -18% | +8% · 0.67 · -20% | +8% · 0.52 · -30% | +6% · 0.46 · -34% |
| adaptive · score_p10 | -7% · -0.38 · -35% | +14% · 0.89 · -19% | +10% · 0.74 · -20% | +16% · 0.83 · -15% | +8% · 0.51 · -12% | -22% · -1.26 · -26% | +17% · 0.89 · -18% | +12% · 0.82 · -20% | +8% · 0.52 · -30% | +9% · 0.57 · -35% |
| adaptive · first_combo | -6% · -0.32 · -31% | +14% · 0.93 · -18% | +8% · 0.61 · -19% | +17% · 0.81 · -14% | +15% · 0.70 · -16% | -21% · -1.15 · -25% | +17% · 0.96 · -16% | +11% · 0.78 · -21% | +10% · 0.59 · -30% | +9% · 0.58 · -31% |
| adaptive · risk_moderate | -0% · -0.01 · -13% | +12% · 0.90 · -19% | +2% · 0.27 · -18% | +28% · 1.30 · -13% | +22% · 1.17 · -9% | -11% · -0.95 · -15% | +20% · 0.99 · -18% | +7% · 0.61 · -19% | +16% · 0.86 · -23% | +9% · 0.67 · -23% |
| adaptive · risk_conservative | -1% · -0.31 · -8% | +4% · 0.48 · -11% | +6% · 0.66 · -13% | +3% · 0.29 · -12% | -2% · -0.14 · -13% | -3% · -0.60 · -4% | +2% · 0.26 · -16% | +5% · 0.57 · -13% | +1% · 0.12 · -16% | +3% · 0.36 · -16% |
| adaptive · pos5 | -3% · -0.06 · -28% | +13% · 0.75 · -27% | +6% · 0.44 · -19% | +18% · 0.80 · -15% | +26% · 1.32 · -10% | -24% · -1.32 · -28% | +8% · 0.58 · -16% | +10% · 0.61 · -27% | +5% · 0.38 · -32% | +7% · 0.46 · -32% |
| adaptive · pos7 | -4% · -0.20 · -31% | +13% · 0.76 · -20% | +9% · 0.64 · -19% | +19% · 0.88 · -14% | +9% · 0.60 · -12% | -22% · -1.13 · -26% | +24% · 1.10 · -17% | +11% · 0.71 · -20% | +12% · 0.66 · -30% | +10% · 0.60 · -31% |
| |  | | | | | | | | | |
| **trend** · smart | -9% · -0.53 · -31% | +14% · 0.92 · -18% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +5% · 0.38 · -14% | -23% · -1.31 · -24% | +17% · 0.95 · -18% | +11% · 0.77 · -19% | +7% · 0.48 · -30% | +7% · 0.52 · -31% |
| trend · plain | -23% · -0.39 · -65% | +22% · 0.98 · -25% | +14% · 0.76 · -32% | +110% · 1.96 · -42% | +10% · 0.44 · -25% | -24% · -0.77 · -31% | +67% · 1.53 · -38% | +18% · 0.88 · -32% | +45% · 1.18 · -42% | +22% · 0.79 · -65% |
| trend · no_regime | -15% · -0.66 · -46% | +16% · 0.97 · -19% | +10% · 0.78 · -18% | +22% · 0.84 · -23% | +9% · 0.58 · -11% | -22% · -1.26 · -24% | +13% · 0.76 · -21% | +13% · 0.88 · -19% | +7% · 0.45 · -31% | +8% · 0.50 · -46% |
| trend · no_score | -10% · -0.65 · -33% | +14% · 0.97 · -19% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +5% · 0.38 · -14% | -23% · -1.31 · -24% | +17% · 0.95 · -18% | +11% · 0.79 · -19% | +7% · 0.48 · -30% | +7% · 0.52 · -33% |
| trend · no_selfcheck | -9% · -0.53 · -31% | +14% · 0.92 · -18% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +5% · 0.38 · -14% | -23% · -1.31 · -24% | +17% · 0.95 · -18% | +11% · 0.77 · -19% | +7% · 0.48 · -30% | +7% · 0.52 · -31% |
| trend · score_m10 | -10% · -0.65 · -33% | +14% · 0.97 · -19% | +8% · 0.61 · -19% | +14% · 0.72 · -16% | +5% · 0.38 · -14% | -23% · -1.31 · -24% | +17% · 0.95 · -18% | +11% · 0.79 · -19% | +7% · 0.48 · -30% | +7% · 0.52 · -33% |
| trend · score_p10 | -10% · -0.63 · -31% | +10% · 0.75 · -15% | +10% · 0.74 · -18% | +11% · 0.63 · -17% | +5% · 0.37 · -12% | -22% · -1.24 · -24% | +17% · 0.95 · -18% | +10% · 0.75 · -19% | +7% · 0.48 · -31% | +7% · 0.49 · -31% |
| trend · first_combo | -8% · -0.52 · -32% | +13% · 0.94 · -16% | +11% · 0.78 · -21% | +15% · 0.75 · -14% | +21% · 1.05 · -10% | -26% · -1.43 · -27% | +12% · 0.75 · -18% | +12% · 0.86 · -24% | +7% · 0.44 · -32% | +8% · 0.55 · -32% |
| trend · risk_moderate | -5% · -0.73 · -16% | +13% · 1.01 · -16% | +3% · 0.30 · -18% | +20% · 1.15 · -15% | +10% · 0.65 · -11% | -16% · -1.54 · -16% | +18% · 0.93 · -19% | +8% · 0.68 · -18% | +11% · 0.66 · -22% | +8% · 0.59 · -22% |
| trend · risk_conservative | -2% · -0.39 · -7% | +6% · 0.67 · -12% | +2% · 0.31 · -15% | +3% · 0.36 · -8% | -4% · -0.30 · -13% | -7% · -1.80 · -6% | +2% · 0.25 · -16% | +4% · 0.50 · -15% | -0% · 0.04 · -18% | +2% · 0.28 · -19% |
| trend · pos5 | -10% · -0.55 · -34% | +16% · 0.94 · -20% | +2% · 0.21 · -27% | +12% · 0.61 · -15% | +17% · 0.87 · -13% | -26% · -1.47 · -30% | +27% · 1.27 · -17% | +9% · 0.59 · -27% | +13% · 0.69 · -36% | +8% · 0.52 · -36% |
| trend · pos7 | -11% · -0.68 · -34% | +13% · 0.84 · -18% | +6% · 0.48 · -23% | +26% · 1.07 · -16% | +18% · 0.99 · -12% | -27% · -1.61 · -29% | +24% · 1.18 · -15% | +9% · 0.66 · -23% | +13% · 0.72 · -34% | +9% · 0.57 · -34% |
| |  | | | | | | | | | |
| **momentum** · smart | -14% · -0.81 · -37% | +8% · 0.57 · -21% | +13% · 0.93 · -17% | +27% · 1.17 · -20% | +29% · 1.39 · -10% | -25% · -1.46 · -26% | +11% · 0.64 · -20% | +11% · 0.73 · -21% | +9% · 0.52 · -30% | +7% · 0.49 · -37% |
| momentum · plain | -23% · -0.39 · -65% | +22% · 0.98 · -25% | +14% · 0.76 · -32% | +110% · 1.96 · -42% | +10% · 0.44 · -25% | -24% · -0.77 · -31% | +67% · 1.53 · -38% | +18% · 0.88 · -32% | +45% · 1.18 · -42% | +22% · 0.79 · -65% |
| momentum · no_regime | -13% · -0.47 · -43% | +15% · 0.96 · -19% | +12% · 0.84 · -24% | +14% · 0.62 · -27% | +33% · 1.59 · -9% | -26% · -1.46 · -27% | +9% · 0.54 · -21% | +14% · 0.90 · -24% | +6% · 0.40 · -30% | +8% · 0.51 · -43% |
| momentum · no_score | -11% · -0.64 · -35% | +10% · 0.63 · -19% | +13% · 0.92 · -17% | +27% · 1.17 · -20% | +29% · 1.39 · -10% | -25% · -1.46 · -26% | +11% · 0.64 · -20% | +11% · 0.77 · -19% | +9% · 0.52 · -30% | +8% · 0.52 · -35% |
| momentum · no_selfcheck | -14% · -0.98 · -35% | +8% · 0.68 · -18% | +13% · 0.93 · -17% | +27% · 1.17 · -20% | +29% · 1.39 · -10% | -25% · -1.46 · -26% | +11% · 0.64 · -20% | +11% · 0.81 · -19% | +9% · 0.52 · -30% | +7% · 0.50 · -35% |
| momentum · score_m10 | -11% · -0.64 · -35% | +10% · 0.63 · -19% | +13% · 0.92 · -17% | +27% · 1.17 · -20% | +29% · 1.39 · -10% | -25% · -1.46 · -26% | +11% · 0.64 · -20% | +11% · 0.77 · -19% | +9% · 0.52 · -30% | +8% · 0.52 · -35% |
| momentum · score_p10 | -9% · -0.50 · -38% | +18% · 1.04 · -18% | +13% · 0.92 · -17% | +27% · 1.17 · -20% | +29% · 1.39 · -10% | -25% · -1.46 · -26% | +11% · 0.64 · -20% | +15% · 0.98 · -19% | +9% · 0.52 · -30% | +10% · 0.65 · -38% |
| momentum · first_combo | -11% · -0.71 · -36% | +6% · 0.54 · -22% | +12% · 0.90 · -18% | +23% · 1.01 · -19% | +25% · 1.20 · -11% | -19% · -0.97 · -23% | +17% · 0.93 · -20% | +9% · 0.73 · -22% | +13% · 0.69 · -27% | +8% · 0.56 · -36% |
| momentum · risk_moderate | -2% · -0.28 · -13% | +10% · 0.80 · -14% | +5% · 0.48 · -18% | +30% · 1.32 · -16% | +13% · 0.61 · -23% | -8% · -1.29 · -9% | +9% · 0.62 · -18% | +7% · 0.64 · -18% | +10% · 0.62 · -25% | +7% · 0.57 · -25% |
| momentum · risk_conservative | -2% · -0.35 · -10% | +4% · 0.41 · -12% | +3% · 0.43 · -14% | +15% · 1.17 · -9% | +31% · 1.29 · -13% | -8% · -1.58 · -8% | +1% · 0.17 · -21% | +3% · 0.42 · -14% | +6% · 0.46 · -21% | +4% · 0.39 · -21% |
| momentum · pos5 | -10% · -0.52 · -31% | +7% · 0.52 · -18% | +9% · 0.64 · -16% | +23% · 1.00 · -13% | +47% · 1.82 · -10% | -24% · -1.09 · -27% | +42% · 1.57 · -23% | +8% · 0.58 · -18% | +27% · 1.12 · -30% | +12% · 0.71 · -31% |
| momentum · pos7 | -10% · -0.45 · -40% | +14% · 0.82 · -21% | +11% · 0.77 · -20% | +12% · 0.62 · -15% | +32% · 1.42 · -10% | -26% · -1.45 · -26% | +12% · 0.68 · -20% | +13% · 0.79 · -22% | +7% · 0.45 · -31% | +8% · 0.52 · -40% |
| |  | | | | | | | | | |
| **pullback** · smart | -10% · -0.60 · -35% | +10% · 0.71 · -22% | +12% · 0.88 · -19% | +23% · 1.08 · -14% | +25% · 1.34 · -9% | -25% · -1.70 · -29% | +23% · 1.10 · -15% | +11% · 0.79 · -22% | +14% · 0.77 · -29% | +10% · 0.65 · -35% |
| pullback · plain | -27% · -0.61 · -66% | +25% · 1.09 · -23% | +17% · 0.91 · -32% | +31% · 0.94 · -42% | +14% · 0.62 · -15% | -27% · -0.97 · -34% | +79% · 1.76 · -36% | +21% · 1.00 · -32% | +40% · 1.16 · -42% | +21% · 0.81 · -66% |
| pullback · no_regime | -23% · -1.16 · -52% | +15% · 0.92 · -26% | +14% · 0.97 · -20% | +42% · 1.34 · -26% | +31% · 1.64 · -8% | -23% · -1.47 · -26% | +24% · 1.09 · -16% | +14% · 0.94 · -26% | +19% · 0.89 · -28% | +11% · 0.66 · -52% |
| pullback · no_score | -13% · -0.88 · -32% | +11% · 0.99 · -10% | +12% · 0.88 · -19% | +23% · 1.08 · -14% | +25% · 1.34 · -9% | -25% · -1.70 · -29% | +23% · 1.10 · -15% | +12% · 0.93 · -19% | +14% · 0.77 · -29% | +10% · 0.67 · -32% |
| pullback · no_selfcheck | -11% · -0.73 · -34% | +15% · 1.06 · -21% | +12% · 0.90 · -19% | +23% · 1.08 · -14% | +25% · 1.34 · -9% | -25% · -1.70 · -29% | +23% · 1.10 · -15% | +14% · 0.99 · -21% | +14% · 0.77 · -29% | +11% · 0.73 · -34% |
| pullback · score_m10 | -13% · -0.89 · -32% | +11% · 0.99 · -10% | +12% · 0.88 · -19% | +23% · 1.08 · -14% | +25% · 1.34 · -9% | -25% · -1.70 · -29% | +23% · 1.10 · -15% | +12% · 0.93 · -19% | +14% · 0.77 · -29% | +10% · 0.67 · -32% |
| pullback · score_p10 | -12% · -0.87 · -33% | +9% · 0.75 · -25% | +12% · 0.90 · -19% | +23% · 1.08 · -14% | +25% · 1.34 · -9% | -25% · -1.70 · -29% | +23% · 1.10 · -15% | +11% · 0.83 · -25% | +14% · 0.77 · -29% | +9% · 0.64 · -33% |
| pullback · first_combo | -11% · -0.75 · -33% | +13% · 0.97 · -20% | +10% · 0.74 · -18% | +24% · 1.07 · -17% | +27% · 1.39 · -11% | -25% · -1.58 · -29% | +12% · 0.75 · -14% | +11% · 0.86 · -20% | +9% · 0.57 · -30% | +8% · 0.58 · -33% |
| pullback · risk_moderate | -4% · -0.70 · -16% | +10% · 0.86 · -14% | +9% · 0.75 · -16% | +8% · 0.51 · -13% | +29% · 1.50 · -11% | -16% · -1.97 · -17% | +19% · 1.06 · -14% | +10% · 0.80 · -16% | +13% · 0.77 · -19% | +9% · 0.71 · -19% |
| pullback · risk_conservative | +2% · 0.42 · -6% | +4% · 0.42 · -15% | +0% · 0.07 · -13% | +10% · 0.78 · -11% | +35% · 1.36 · -15% | -7% · -1.55 · -7% | +11% · 0.81 · -14% | +2% · 0.26 · -15% | +11% · 0.78 · -15% | +5% · 0.51 · -15% |
| pullback · pos5 | -13% · -0.75 · -40% | +24% · 1.29 · -21% | +10% · 0.66 · -19% | +9% · 0.52 · -15% | +8% · 0.50 · -13% | -32% · -2.10 · -34% | +26% · 0.99 · -26% | +17% · 0.99 · -21% | +10% · 0.51 · -40% | +11% · 0.62 · -40% |
| pullback · pos7 | -15% · -1.09 · -41% | +21% · 1.17 · -18% | +13% · 0.87 · -16% | +14% · 0.73 · -14% | +13% · 0.80 · -11% | -27% · -1.82 · -31% | +7% · 0.52 · -21% | +17% · 1.03 · -18% | +3% · 0.25 · -36% | +8% · 0.55 · -41% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.44 · -19% | +13% · 0.92 · -19% | +15% · 0.82 · -34% | +11% · 0.65 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.13 · -20% | +21% · 0.72 · -38% | +34% · 2.15 · -6% | -10% · -0.37 · -20% | +27% · 1.36 · -23% | +18% · 1.16 · -21% | +18% · 0.87 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| strong · smart | +12% | 0.94 | -21% | 87% | +6% | 0.42 | -30% | 89% |
| strong · plain | +20% | 0.96 | -34% | 99% | +38% | 1.01 | -51% | 98% |
| strong · no_regime | +16% | 1.06 | -22% | 99% | +2% | 0.22 | -30% | 90% |
| strong · no_score | +13% | 0.99 | -17% | 85% | +7% | 0.44 | -30% | 89% |
| strong · no_selfcheck | +12% | 0.94 | -21% | 87% | +6% | 0.43 | -29% | 89% |
| strong · score_m10 | +15% | 0.98 | -24% | 96% | +7% | 0.46 | -30% | 89% |
| strong · score_p10 | +13% | 0.92 | -23% | 96% | +7% | 0.43 | -31% | 89% |
| strong · first_combo | +11% | 0.86 | -19% | 84% | +5% | 0.37 | -30% | 86% |
| strong · risk_moderate | +8% | 0.68 | -20% | 75% | +3% | 0.29 | -17% | 64% |
| strong · risk_conservative | +7% | 0.66 | -19% | 63% | +3% | 0.31 | -16% | 41% |
| strong · combo_back | +11% | 0.78 | -23% | 64% | +12% | 0.74 | -24% | 71% |
| strong · pos5 | +14% | 0.88 | -25% | 96% | +11% | 0.62 | -31% | 89% |
| strong · pos7 | +14% | 0.92 | -25% | 97% | +7% | 0.45 | -30% | 89% |
| adaptive · smart | +11% | 0.75 | -20% | 98% | +8% | 0.52 | -30% | 90% |
| adaptive · plain | +18% | 0.88 | -32% | 99% | +45% | 1.18 | -42% | 99% |
| adaptive · no_regime | +12% | 0.80 | -21% | 99% | +10% | 0.56 | -30% | 92% |
| adaptive · no_score | +8% | 0.67 | -20% | 89% | +8% | 0.52 | -30% | 90% |
| adaptive · no_selfcheck | +8% | 0.68 | -20% | 89% | +8% | 0.52 | -30% | 90% |
| adaptive · score_m10 | +8% | 0.67 | -20% | 88% | +8% | 0.52 | -30% | 90% |
| adaptive · score_p10 | +12% | 0.82 | -20% | 98% | +8% | 0.52 | -30% | 90% |
| adaptive · first_combo | +11% | 0.78 | -21% | 95% | +10% | 0.59 | -30% | 91% |
| adaptive · risk_moderate | +7% | 0.61 | -19% | 82% | +16% | 0.86 | -23% | 71% |
| adaptive · risk_conservative | +5% | 0.57 | -13% | 62% | +1% | 0.12 | -16% | 51% |
| adaptive · pos5 | +10% | 0.61 | -27% | 97% | +5% | 0.38 | -32% | 78% |
| adaptive · pos7 | +11% | 0.71 | -20% | 97% | +12% | 0.66 | -30% | 91% |
| trend · smart | +11% | 0.77 | -19% | 93% | +7% | 0.48 | -30% | 87% |
| trend · plain | +18% | 0.88 | -32% | 99% | +45% | 1.18 | -42% | 99% |
| trend · no_regime | +13% | 0.88 | -19% | 99% | +7% | 0.45 | -31% | 89% |
| trend · no_score | +11% | 0.79 | -19% | 93% | +7% | 0.48 | -30% | 87% |
| trend · no_selfcheck | +11% | 0.77 | -19% | 93% | +7% | 0.48 | -30% | 87% |
| trend · score_m10 | +11% | 0.79 | -19% | 93% | +7% | 0.48 | -30% | 87% |
| trend · score_p10 | +10% | 0.75 | -19% | 89% | +7% | 0.48 | -31% | 87% |
| trend · first_combo | +12% | 0.86 | -24% | 93% | +7% | 0.44 | -32% | 83% |
| trend · risk_moderate | +8% | 0.68 | -18% | 78% | +11% | 0.66 | -22% | 73% |
| trend · risk_conservative | +4% | 0.50 | -15% | 53% | -0% | 0.04 | -18% | 46% |
| trend · pos5 | +9% | 0.59 | -27% | 93% | +13% | 0.69 | -36% | 84% |
| trend · pos7 | +9% | 0.66 | -23% | 91% | +13% | 0.72 | -34% | 85% |
| momentum · smart | +11% | 0.73 | -21% | 97% | +9% | 0.52 | -30% | 84% |
| momentum · plain | +18% | 0.88 | -32% | 99% | +45% | 1.18 | -42% | 99% |
| momentum · no_regime | +14% | 0.90 | -24% | 99% | +6% | 0.40 | -30% | 87% |
| momentum · no_score | +11% | 0.77 | -19% | 98% | +9% | 0.52 | -30% | 84% |
| momentum · no_selfcheck | +11% | 0.81 | -19% | 85% | +9% | 0.52 | -30% | 84% |
| momentum · score_m10 | +11% | 0.77 | -19% | 98% | +9% | 0.52 | -30% | 84% |
| momentum · score_p10 | +15% | 0.98 | -19% | 98% | +9% | 0.52 | -30% | 84% |
| momentum · first_combo | +9% | 0.73 | -22% | 86% | +13% | 0.69 | -27% | 94% |
| momentum · risk_moderate | +7% | 0.64 | -18% | 75% | +10% | 0.62 | -25% | 60% |
| momentum · risk_conservative | +3% | 0.42 | -14% | 50% | +6% | 0.46 | -21% | 49% |
| momentum · pos5 | +8% | 0.58 | -18% | 89% | +27% | 1.12 | -30% | 88% |
| momentum · pos7 | +13% | 0.79 | -22% | 98% | +7% | 0.45 | -31% | 81% |
| pullback · smart | +11% | 0.79 | -22% | 97% | +14% | 0.77 | -29% | 91% |
| pullback · plain | +21% | 1.00 | -32% | 98% | +40% | 1.16 | -42% | 98% |
| pullback · no_regime | +14% | 0.94 | -26% | 99% | +19% | 0.89 | -28% | 97% |
| pullback · no_score | +12% | 0.93 | -19% | 85% | +14% | 0.77 | -29% | 91% |
| pullback · no_selfcheck | +14% | 0.99 | -21% | 94% | +14% | 0.77 | -29% | 91% |
| pullback · score_m10 | +12% | 0.93 | -19% | 85% | +14% | 0.77 | -29% | 91% |
| pullback · score_p10 | +11% | 0.83 | -25% | 85% | +14% | 0.77 | -29% | 91% |
| pullback · first_combo | +11% | 0.86 | -20% | 92% | +9% | 0.57 | -30% | 85% |
| pullback · risk_moderate | +10% | 0.80 | -16% | 79% | +13% | 0.77 | -19% | 73% |
| pullback · risk_conservative | +2% | 0.26 | -15% | 50% | +11% | 0.78 | -15% | 55% |
| pullback · pos5 | +17% | 0.99 | -21% | 97% | +10% | 0.51 | -40% | 85% |
| pullback · pos7 | +17% | 1.03 | -18% | 96% | +3% | 0.25 | -36% | 73% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.87 / 0.82 | -38% / -34% | | | | | |

## Inside each smart bot

### Strong Stocks on Sale

Sectors (first day, sector): []

Closed trades 2203 · exits {'Signal': 1794, 'Stop Loss': 409} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +9%/yr Sharpe 0.57, neutral 1178 days +22%/yr Sharpe 1.36, bear 606 days -17%/yr Sharpe -0.89, stress 278 days +10%/yr Sharpe 0.91

By strategy: Donchian Breakout (Turtle) 1712 trades +232,377 win 40%, Mean Reversion & Multi-Factor Strategy & Regime-Based Strategy & Portfolio-Level Strategy (4/4) 85 trades +2,888 win 56%, Momentum Strategy & VWAP Mean Reversion & Multi-Factor Strategy (3/3) 45 trades +8,724 win 62%, VWAP Mean Reversion & Multi-Factor Strategy & Momentum Strategy & Portfolio-Level Strategy (4/4) 45 trades +6,816 win 60%, VWAP Mean Reversion & RSI Mean Reversion & Relative Strength Strategy & Portfolio-Level Strategy (3/4) 209 trades +40,533 win 64%, VWAP Mean Reversion & Statistical Arbitrage & Multi-Factor Strategy & Relative Strength Strategy (3/4) 107 trades +1,849 win 62%

### Adaptive All-Weather

Sectors (first day, sector): []

Closed trades 1767 · exits {'Signal': 1403, 'Stop Loss': 364} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +7%/yr Sharpe 0.44, neutral 1178 days +24%/yr Sharpe 1.37, bear 606 days -13%/yr Sharpe -0.63, stress 278 days +9%/yr Sharpe 0.70

By strategy: Bollinger Breakout 80 trades -3,961 win 38%, Breakout Strategy 129 trades +29,141 win 32%, Donchian Breakout (Turtle) 130 trades +26,724 win 46%, EMA Crossover 17 trades -5,372 win 24%, Golden Cross (50/200) 7 trades +19,535 win 14%, MACD Crossover 97 trades +502 win 37%, MFI Money Flow (Volume) 3 trades +7,244 win 67%, Machine Learning Signal Combination 27 trades +448 win 30%, Mean Reversion 25 trades +8,074 win 96%, Momentum Strategy 84 trades +13,121 win 36%, Moving Average Crossover 12 trades +12,278 win 50%, Multi-Factor Strategy 41 trades -4,284 win 22%, OBV Trend (Volume) 101 trades -1,192 win 41%, Pairs Trading 1 trades +476 win 100%, Portfolio-Level Strategy 52 trades +54,156 win 35%, Regime-Based Strategy 68 trades -1,987 win 44%, Relative Strength Strategy 260 trades +117,019 win 44%, SMA Crossover 25 trades -4,802 win 36%, Statistical Arbitrage 9 trades +1,818 win 67%, Trend Following 56 trades +8,475 win 43%, VWAP Mean Reversion 29 trades +9,142 win 76%, VWAP Reclaim / Pullback 45 trades +7,606 win 36%, VWMA Crossover (Volume) 45 trades -8,909 win 22%, Volatility Breakout 207 trades -14,976 win 38%, Volume Breakout 217 trades +25,123 win 39%

### Trend Rider

Sectors (first day, sector): []

Closed trades 1714 · exits {'Signal': 1344, 'Stop Loss': 370} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +6%/yr Sharpe 0.36, neutral 1178 days +24%/yr Sharpe 1.40, bear 606 days -11%/yr Sharpe -0.54, stress 278 days +14%/yr Sharpe 1.05

By strategy: Bollinger Breakout 73 trades -6,503 win 38%, Breakout Strategy 129 trades +105,881 win 35%, Donchian Breakout (Turtle) 138 trades +15,049 win 38%, EMA Crossover 9 trades -346 win 33%, Golden Cross (50/200) 7 trades +8,842 win 14%, MACD Crossover 94 trades -1,144 win 30%, MFI Money Flow (Volume) 3 trades +2,207 win 67%, Machine Learning Signal Combination 23 trades -784 win 35%, Mean Reversion 26 trades +4,150 win 81%, Momentum Strategy 69 trades +9,617 win 35%, Moving Average Crossover 5 trades +1,980 win 40%, Multi-Factor Strategy 44 trades -1,972 win 25%, OBV Trend (Volume) 81 trades +8,143 win 40%, Pairs Trading 1 trades +3,291 win 100%, Portfolio-Level Strategy 63 trades +59,136 win 35%, RSI Mean Reversion 1 trades +1,134 win 100%, Regime-Based Strategy 64 trades -2,609 win 42%, Relative Strength Strategy 266 trades +20,448 win 42%, SMA Crossover 21 trades +712 win 52%, Statistical Arbitrage 6 trades -3,671 win 50%, Trend Following 63 trades +11,719 win 51%, VWAP Mean Reversion 30 trades +6,334 win 73%, VWAP Reclaim / Pullback 49 trades -3,969 win 27%, VWMA Crossover (Volume) 39 trades -3,645 win 31%, Volatility Breakout 201 trades -14,456 win 38%, Volume Breakout 209 trades +30,716 win 45%

### Momentum Leaders

Sectors (first day, sector): []

Closed trades 1831 · exits {'Signal': 1428, 'Stop Loss': 403} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +7%/yr Sharpe 0.44, neutral 1178 days +22%/yr Sharpe 1.23, bear 606 days -16%/yr Sharpe -0.79, stress 278 days +17%/yr Sharpe 1.23

By strategy: Bollinger Breakout 78 trades -15,406 win 42%, Breakout Strategy 142 trades +71,042 win 37%, Donchian Breakout (Turtle) 167 trades +32,856 win 44%, EMA Crossover 12 trades +11,532 win 42%, Golden Cross (50/200) 3 trades -3,311 win 0%, MACD Crossover 101 trades -6,361 win 32%, MFI Money Flow (Volume) 2 trades +1,484 win 50%, Machine Learning Signal Combination 35 trades +3,079 win 37%, Mean Reversion 23 trades +6,530 win 87%, Momentum Strategy 71 trades +7,950 win 35%, Moving Average Crossover 7 trades +5,654 win 29%, Multi-Factor Strategy 46 trades -8,102 win 30%, OBV Trend (Volume) 100 trades +6,595 win 42%, Portfolio-Level Strategy 56 trades +18,291 win 30%, Regime-Based Strategy 72 trades -1,439 win 53%, Relative Strength Strategy 287 trades +97,405 win 44%, SMA Crossover 28 trades +1,926 win 43%, Statistical Arbitrage 12 trades +1,778 win 67%, Trend Following 59 trades +24,425 win 56%, VWAP Mean Reversion 31 trades +12,372 win 84%, VWAP Reclaim / Pullback 50 trades +1,035 win 24%, VWMA Crossover (Volume) 40 trades -6,949 win 25%, Volatility Breakout 196 trades +22,592 win 38%, Volume Breakout 213 trades -28,834 win 39%

### Pullback Buyer

Sectors (first day, sector): []

Closed trades 3031 · exits {'Signal': 1592, 'Time Stop': 850, 'Stop Loss': 589} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2912, 'neutral': 1179, 'bear': 606, 'stress': 278} · regime now neutral

By regime (the session before): bull 2912 days +11%/yr Sharpe 0.67, neutral 1178 days +23%/yr Sharpe 1.25, bear 606 days -12%/yr Sharpe -0.62, stress 278 days +8%/yr Sharpe 0.65

By strategy: Bollinger Breakout 131 trades -9,805 win 36%, Breakout Strategy 259 trades +257,109 win 25%, Donchian Breakout (Turtle) 259 trades +47,520 win 33%, EMA Crossover 26 trades +4,075 win 35%, Golden Cross (50/200) 17 trades +7,858 win 18%, MACD Crossover 163 trades +6,327 win 40%, MFI Money Flow (Volume) 2 trades +2,442 win 100%, Machine Learning Signal Combination 46 trades +2,240 win 22%, Mean Reversion 54 trades -623 win 59%, Momentum Strategy 118 trades +14,087 win 24%, Moving Average Crossover 11 trades +3,682 win 45%, Multi-Factor Strategy 83 trades +1,036 win 22%, OBV Trend (Volume) 182 trades -197 win 34%, Portfolio-Level Strategy 92 trades +19,542 win 21%, Regime-Based Strategy 108 trades -5,050 win 46%, Relative Strength Strategy 548 trades +84,298 win 33%, SMA Crossover 34 trades -5,023 win 24%, Statistical Arbitrage 18 trades +146 win 56%, Trend Following 83 trades +32,437 win 41%, VWAP Mean Reversion 58 trades +15,899 win 66%, VWAP Reclaim / Pullback 83 trades -3,287 win 25%, VWMA Crossover (Volume) 56 trades +13,897 win 38%, Volatility Breakout 295 trades +29,006 win 37%, Volume Breakout 305 trades -49,147 win 31%

