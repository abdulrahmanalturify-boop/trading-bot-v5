# Smart bots · period test

Run 2026-09-29 08:56 UTC · 515 stocks · from 2007-01-03 · fee+slippage 0.1% per side · took 13 min

Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.

| Bot · variant | 2008-2009 crisis | 2010-2014 | 2015-2019 | 2020 COVID | 2021 | 2022 bear market | 2023-now | In-sample 2010-2019 | Out-of-sample 2020-now | Whole test 2008-now |
|---|---|---|---|---|---|---|---|---|---|---|
| **strong** · smart | -15% · -0.79 · -35% | +19% · 1.17 · -21% | +12% · 0.90 · -15% | +5% · 0.32 · -19% | +24% · 1.35 · -12% | -24% · -1.36 · -29% | +13% · 0.79 · -17% | +15% · 1.04 · -21% | +7% · 0.44 · -30% | +9% · 0.59 · -35% |
| strong · plain | -24% · -0.55 · -68% | +21% · 0.97 · -22% | +23% · 1.12 · -30% | +30% · 0.92 · -38% | +25% · 0.95 · -20% | -25% · -0.85 · -32% | +62% · 1.48 · -35% | +22% · 1.03 · -30% | +35% · 1.03 · -41% | +20% · 0.79 · -68% |
| strong · no_regime | -23% · -1.08 · -51% | +20% · 1.18 · -20% | +14% · 0.98 · -13% | -9% · -0.18 · -32% | +25% · 1.37 · -12% | -24% · -1.36 · -29% | +11% · 0.71 · -14% | +17% · 1.08 · -20% | +4% · 0.28 · -32% | +7% · 0.47 · -51% |
| strong · no_score | -17% · -1.12 · -35% | +15% · 1.29 · -11% | +11% · 0.85 · -17% | +7% · 0.40 · -19% | +24% · 1.35 · -12% | -24% · -1.36 · -29% | +13% · 0.79 · -17% | +13% · 1.05 · -17% | +7% · 0.45 · -30% | +7% · 0.55 · -35% |
| strong · no_selfcheck | -15% · -1.02 · -35% | +15% · 1.26 · -13% | +12% · 0.90 · -15% | +5% · 0.32 · -19% | +24% · 1.35 · -12% | -25% · -1.38 · -29% | +13% · 0.79 · -17% | +13% · 1.06 · -15% | +7% · 0.43 · -30% | +8% · 0.55 · -35% |
| strong · score_m10 | -15% · -0.82 · -36% | +19% · 1.16 · -21% | +11% · 0.85 · -17% | +7% · 0.42 · -19% | +24% · 1.36 · -12% | -24% · -1.36 · -29% | +13% · 0.79 · -17% | +15% · 1.01 · -21% | +7% · 0.46 · -30% | +9% · 0.58 · -36% |
| strong · score_p10 | -14% · -0.73 · -37% | +17% · 1.09 · -23% | +12% · 0.90 · -15% | +6% · 0.39 · -19% | +24% · 1.36 · -12% | -25% · -1.41 · -30% | +13% · 0.79 · -17% | +15% · 1.00 · -23% | +7% · 0.44 · -31% | +8% · 0.57 · -37% |
| strong · first_combo | -15% · -1.00 · -34% | +14% · 1.17 · -15% | +10% · 0.80 · -15% | +2% · 0.18 · -16% | +27% · 1.39 · -14% | -24% · -1.46 · -28% | +12% · 0.75 · -18% | +12% · 0.97 · -15% | +6% · 0.40 · -32% | +7% · 0.50 · -34% |
| strong · risk_1 | -15% · -1.09 · -32% | +15% · 1.27 · -14% | +12% · 0.90 · -15% | +3% · 0.23 · -18% | +24% · 1.35 · -12% | -24% · -1.42 · -28% | +13% · 0.82 · -16% | +13% · 1.07 · -15% | +6% · 0.43 · -30% | +8% · 0.57 · -32% |
| strong · loose_risk | -2% · -0.19 · -13% | +16% · 1.11 · -18% | +5% · 0.52 · -20% | -2% · -0.10 · -12% | +21% · 1.32 · -11% | -16% · -1.56 · -18% | +5% · 0.38 · -20% | +10% · 0.85 · -20% | +2% · 0.24 · -21% | +6% · 0.53 · -21% |
| strong · combo_back | +5% · 0.35 · -17% | +9% · 0.65 · -19% | +12% · 0.90 · -18% | +18% · 1.06 · -18% | +6% · 0.41 · -13% | -8% · -0.45 · -18% | +20% · 1.14 · -22% | +10% · 0.76 · -23% | +12% · 0.76 · -23% | +11% · 0.71 · -23% |
| strong · pos5 | -18% · -1.02 · -40% | +13% · 0.80 · -27% | +10% · 0.69 · -16% | +11% · 0.54 · -15% | +24% · 1.23 · -13% | -28% · -1.50 · -33% | +18% · 0.99 · -18% | +12% · 0.75 · -27% | +9% · 0.54 · -33% | +7% · 0.48 · -40% |
| strong · pos7 | -15% · -0.80 · -38% | +17% · 1.00 · -25% | +11% · 0.75 · -17% | +3% · 0.23 · -18% | +18% · 0.99 · -14% | -28% · -1.62 · -31% | +15% · 0.82 · -20% | +14% · 0.88 · -25% | +5% · 0.37 · -35% | +7% · 0.50 · -38% |
| |  | | | | | | | | | |
| **adaptive** · smart | -11% · -0.70 · -33% | +12% · 0.94 · -12% | +8% · 0.62 · -18% | +14% · 0.73 · -17% | +8% · 0.52 · -12% | -20% · -1.09 · -26% | +21% · 1.04 · -18% | +10% · 0.78 · -18% | +10% · 0.60 · -30% | +8% · 0.54 · -33% |
| adaptive · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| adaptive · no_regime | -14% · -0.54 · -44% | +13% · 0.79 · -21% | +9% · 0.68 · -20% | +22% · 0.89 · -26% | +6% · 0.45 · -13% | -19% · -1.05 · -24% | +20% · 0.94 · -18% | +11% · 0.74 · -21% | +11% · 0.60 · -30% | +8% · 0.51 · -44% |
| adaptive · no_score | -9% · -0.51 · -33% | +17% · 1.14 · -14% | +11% · 0.81 · -18% | +16% · 0.79 · -15% | +8% · 0.52 · -12% | -20% · -1.09 · -26% | +21% · 1.04 · -18% | +14% · 0.98 · -18% | +11% · 0.61 · -30% | +10% · 0.66 · -33% |
| adaptive · no_selfcheck | -11% · -0.69 · -33% | +12% · 0.93 · -13% | +8% · 0.62 · -18% | +14% · 0.73 · -17% | +8% · 0.52 · -12% | -20% · -1.09 · -26% | +21% · 1.04 · -18% | +10% · 0.77 · -18% | +10% · 0.60 · -30% | +8% · 0.54 · -33% |
| adaptive · score_m10 | -9% · -0.52 · -33% | +17% · 1.14 · -14% | +11% · 0.81 · -18% | +16% · 0.79 · -15% | +8% · 0.52 · -12% | -20% · -1.09 · -26% | +21% · 1.04 · -18% | +14% · 0.98 · -18% | +11% · 0.61 · -30% | +10% · 0.66 · -33% |
| adaptive · score_p10 | -9% · -0.51 · -36% | +16% · 0.98 · -18% | +12% · 0.89 · -16% | +16% · 0.79 · -15% | +8% · 0.52 · -12% | -20% · -1.09 · -26% | +21% · 1.04 · -18% | +14% · 0.94 · -18% | +11% · 0.61 · -30% | +10% · 0.65 · -36% |
| adaptive · first_combo | -9% · -0.50 · -32% | +16% · 1.12 · -18% | +6% · 0.48 · -18% | +13% · 0.66 · -14% | +11% · 0.69 · -10% | -19% · -0.96 · -25% | +11% · 0.68 · -20% | +11% · 0.82 · -18% | +6% · 0.40 · -29% | +7% · 0.50 · -32% |
| adaptive · risk_1 | -10% · -0.69 · -32% | +12% · 0.91 · -14% | +8% · 0.62 · -18% | +14% · 0.72 · -17% | +9% · 0.57 · -11% | -20% · -1.09 · -26% | +22% · 1.10 · -18% | +10% · 0.76 · -18% | +11% · 0.64 · -29% | +8% · 0.56 · -32% |
| adaptive · loose_risk | -2% · -0.18 · -12% | +11% · 0.92 · -15% | +3% · 0.30 · -18% | +19% · 0.99 · -12% | +18% · 1.07 · -8% | -8% · -0.61 · -13% | +17% · 0.87 · -19% | +7% · 0.62 · -18% | +13% · 0.74 · -19% | +8% · 0.61 · -19% |
| adaptive · pos5 | -4% · -0.16 · -27% | +14% · 0.80 · -26% | +4% · 0.35 · -26% | +18% · 0.80 · -15% | +26% · 1.32 · -10% | -26% · -1.38 · -28% | +20% · 1.02 · -15% | +9% · 0.60 · -26% | +12% · 0.64 · -40% | +9% · 0.54 · -40% |
| adaptive · pos7 | -6% · -0.27 · -32% | +13% · 0.83 · -20% | +6% · 0.45 · -25% | +20% · 0.92 · -14% | +10% · 0.61 · -12% | -21% · -1.00 · -25% | +31% · 1.19 · -18% | +10% · 0.65 · -25% | +16% · 0.75 · -30% | +10% · 0.60 · -32% |
| |  | | | | | | | | | |
| **trend** · smart | -8% · -0.46 · -30% | +13% · 0.84 · -21% | +10% · 0.73 · -15% | +16% · 0.78 · -16% | +15% · 0.91 · -11% | -22% · -1.30 · -24% | +26% · 1.22 · -15% | +12% · 0.79 · -21% | +13% · 0.74 · -30% | +10% · 0.65 · -30% |
| trend · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| trend · no_regime | -14% · -0.59 · -45% | +20% · 1.19 · -18% | +8% · 0.60 · -18% | +11% · 0.50 · -26% | +24% · 1.35 · -11% | -21% · -1.20 · -24% | +23% · 1.12 · -15% | +14% · 0.92 · -18% | +13% · 0.68 · -30% | +10% · 0.63 · -45% |
| trend · no_score | -10% · -0.62 · -33% | +14% · 0.97 · -17% | +10% · 0.73 · -15% | +16% · 0.78 · -16% | +15% · 0.91 · -11% | -22% · -1.30 · -24% | +26% · 1.22 · -15% | +12% · 0.85 · -17% | +13% · 0.74 · -30% | +10% · 0.66 · -33% |
| trend · no_selfcheck | -8% · -0.46 · -30% | +13% · 0.84 · -21% | +10% · 0.73 · -15% | +16% · 0.78 · -16% | +15% · 0.91 · -11% | -22% · -1.30 · -24% | +26% · 1.22 · -15% | +12% · 0.79 · -21% | +13% · 0.74 · -30% | +10% · 0.65 · -30% |
| trend · score_m10 | -10% · -0.62 · -33% | +14% · 0.97 · -17% | +10% · 0.73 · -15% | +16% · 0.78 · -16% | +15% · 0.91 · -11% | -22% · -1.30 · -24% | +26% · 1.22 · -15% | +12% · 0.85 · -17% | +13% · 0.74 · -30% | +10% · 0.66 · -33% |
| trend · score_p10 | -9% · -0.54 · -30% | +15% · 1.00 · -18% | +9% · 0.64 · -15% | +13% · 0.69 · -17% | +17% · 0.97 · -10% | -22% · -1.23 · -24% | +27% · 1.27 · -15% | +12% · 0.83 · -18% | +14% · 0.77 · -31% | +10% · 0.67 · -31% |
| trend · first_combo | -8% · -0.50 · -32% | +12% · 0.87 · -16% | +10% · 0.73 · -21% | +21% · 0.93 · -17% | +31% · 1.53 · -9% | -26% · -1.46 · -27% | +10% · 0.69 · -18% | +11% · 0.80 · -24% | +8% · 0.51 · -32% | +8% · 0.55 · -32% |
| trend · risk_1 | -8% · -0.49 · -29% | +13% · 0.87 · -22% | +10% · 0.73 · -15% | +12% · 0.66 · -15% | +15% · 0.95 · -11% | -22% · -1.36 · -24% | +26% · 1.25 · -15% | +12% · 0.80 · -22% | +13% · 0.74 · -30% | +10% · 0.65 · -30% |
| trend · loose_risk | -4% · -0.67 · -18% | +15% · 1.15 · -17% | +7% · 0.60 · -17% | +21% · 1.04 · -16% | +23% · 1.32 · -10% | -17% · -1.62 · -17% | +20% · 1.05 · -17% | +11% · 0.88 · -17% | +14% · 0.80 · -19% | +11% · 0.75 · -19% |
| trend · pos5 | -10% · -0.55 · -34% | +14% · 0.86 · -20% | +5% · 0.37 · -22% | +12% · 0.61 · -15% | +22% · 1.07 · -12% | -26% · -1.47 · -30% | +33% · 1.28 · -17% | +9% · 0.62 · -22% | +16% · 0.77 · -38% | +10% · 0.57 · -38% |
| trend · pos7 | -9% · -0.44 · -39% | +14% · 0.81 · -22% | +8% · 0.58 · -21% | +26% · 1.07 · -16% | +21% · 1.14 · -10% | -26% · -1.56 · -28% | +32% · 1.31 · -15% | +11% · 0.71 · -22% | +18% · 0.86 · -35% | +11% · 0.65 · -39% |
| |  | | | | | | | | | |
| **momentum** · smart | -12% · -0.63 · -37% | +13% · 0.81 · -19% | +12% · 0.84 · -19% | +19% · 0.88 · -21% | +35% · 1.65 · -9% | -27% · -1.64 · -29% | +22% · 1.02 · -22% | +12% · 0.82 · -20% | +14% · 0.72 · -30% | +10% · 0.62 · -37% |
| momentum · plain | -28% · -0.59 · -71% | +29% · 1.21 · -24% | +19% · 0.98 · -31% | +110% · 1.95 · -42% | +9% · 0.43 · -25% | -13% · -0.35 · -27% | +59% · 1.34 · -45% | +24% · 1.10 · -31% | +44% · 1.14 · -45% | +24% · 0.84 · -71% |
| momentum · no_regime | -17% · -0.77 · -49% | +20% · 1.17 · -20% | +12% · 0.84 · -22% | +26% · 0.95 · -26% | +30% · 1.47 · -9% | -26% · -1.51 · -26% | +23% · 1.00 · -21% | +16% · 1.01 · -22% | +15% · 0.72 · -31% | +12% · 0.66 · -49% |
| momentum · no_score | -12% · -0.63 · -37% | +13% · 0.81 · -19% | +12% · 0.84 · -19% | +19% · 0.88 · -21% | +35% · 1.65 · -9% | -27% · -1.64 · -29% | +22% · 1.02 · -22% | +12% · 0.82 · -20% | +14% · 0.72 · -30% | +10% · 0.62 · -37% |
| momentum · no_selfcheck | -12% · -0.73 · -35% | +13% · 0.86 · -17% | +11% · 0.81 · -19% | +19% · 0.88 · -21% | +35% · 1.65 · -9% | -27% · -1.64 · -29% | +22% · 1.02 · -22% | +12% · 0.83 · -22% | +14% · 0.72 · -30% | +10% · 0.63 · -35% |
| momentum · score_m10 | -12% · -0.63 · -37% | +13% · 0.81 · -19% | +12% · 0.84 · -19% | +19% · 0.88 · -21% | +35% · 1.65 · -9% | -27% · -1.64 · -29% | +22% · 1.02 · -22% | +12% · 0.82 · -20% | +14% · 0.72 · -30% | +10% · 0.62 · -37% |
| momentum · score_p10 | -9% · -0.47 · -39% | +16% · 0.92 · -21% | +12% · 0.87 · -17% | +19% · 0.88 · -21% | +35% · 1.65 · -9% | -27% · -1.64 · -29% | +22% · 1.02 · -22% | +14% · 0.90 · -23% | +14% · 0.72 · -30% | +11% · 0.68 · -39% |
| momentum · first_combo | -5% · -0.19 · -38% | +15% · 0.93 · -20% | +13% · 0.94 · -20% | +25% · 1.07 · -19% | +26% · 1.26 · -11% | -23% · -1.28 · -25% | +14% · 0.79 · -20% | +14% · 0.93 · -24% | +10% · 0.60 · -29% | +11% · 0.68 · -38% |
| momentum · risk_1 | -12% · -0.80 · -32% | +12% · 0.85 · -17% | +11% · 0.81 · -18% | +16% · 0.80 · -20% | +35% · 1.66 · -9% | -28% · -1.83 · -29% | +17% · 0.88 · -21% | +12% · 0.83 · -21% | +11% · 0.62 · -31% | +9% · 0.59 · -32% |
| momentum · loose_risk | -2% · -0.35 · -13% | +10% · 0.76 · -15% | +7% · 0.63 · -17% | +40% · 1.74 · -13% | +29% · 1.12 · -17% | -13% · -1.56 · -14% | +23% · 1.06 · -23% | +9% · 0.69 · -17% | +20% · 0.97 · -23% | +11% · 0.75 · -23% |
| momentum · pos5 | -8% · -0.39 · -32% | +13% · 0.78 · -20% | +5% · 0.36 · -25% | +24% · 1.05 · -14% | +13% · 0.66 · -22% | -24% · -1.12 · -26% | +41% · 1.43 · -23% | +9% · 0.57 · -28% | +22% · 0.91 · -29% | +11% · 0.63 · -32% |
| momentum · pos7 | -14% · -0.63 · -45% | +18% · 1.01 · -23% | +9% · 0.62 · -21% | +22% · 0.97 · -18% | +39% · 1.68 · -10% | -25% · -1.34 · -26% | +24% · 1.06 · -22% | +13% · 0.82 · -27% | +16% · 0.78 · -30% | +11% · 0.65 · -45% |
| |  | | | | | | | | | |
| **pullback** · smart | -8% · -0.46 · -33% | +17% · 1.07 · -22% | +12% · 0.86 · -18% | +23% · 1.08 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +15% · 0.97 · -22% | +16% · 0.85 · -28% | +13% · 0.78 · -33% |
| pullback · plain | -28% · -0.63 · -67% | +23% · 1.03 · -23% | +16% · 0.85 · -32% | +35% · 0.99 · -45% | +34% · 1.06 · -21% | -30% · -1.11 · -36% | +85% · 1.81 · -37% | +20% · 0.94 · -32% | +46% · 1.23 · -45% | +22% · 0.81 · -67% |
| pullback · no_regime | -26% · -1.36 · -53% | +16% · 0.97 · -25% | +12% · 0.90 · -20% | +37% · 1.25 · -26% | +26% · 1.36 · -9% | -21% · -1.33 · -26% | +23% · 1.04 · -17% | +14% · 0.94 · -25% | +17% · 0.83 · -28% | +10% · 0.61 · -53% |
| pullback · no_score | -12% · -0.79 · -31% | +9% · 0.72 · -22% | +12% · 0.91 · -18% | +23% · 1.08 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +11% · 0.82 · -22% | +16% · 0.85 · -28% | +10% · 0.68 · -31% |
| pullback · no_selfcheck | -12% · -0.81 · -33% | +12% · 0.89 · -22% | +12% · 0.85 · -18% | +23% · 1.08 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +12% · 0.87 · -22% | +16% · 0.85 · -28% | +11% · 0.70 · -33% |
| pullback · score_m10 | -12% · -0.81 · -32% | +9% · 0.83 · -12% | +11% · 0.84 · -18% | +23% · 1.08 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +10% · 0.83 · -18% | +16% · 0.85 · -28% | +10% · 0.67 · -32% |
| pullback · score_p10 | -10% · -0.72 · -32% | +8% · 0.65 · -25% | +11% · 0.84 · -18% | +23% · 1.08 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +10% · 0.75 · -25% | +16% · 0.85 · -28% | +10% · 0.65 · -32% |
| pullback · first_combo | -11% · -0.78 · -34% | +13% · 0.91 · -20% | +11% · 0.81 · -21% | +26% · 1.12 · -17% | +38% · 1.78 · -9% | -24% · -1.48 · -28% | +13% · 0.77 · -15% | +12% · 0.86 · -21% | +11% · 0.66 · -28% | +9% · 0.62 · -34% |
| pullback · risk_1 | -11% · -0.76 · -32% | +14% · 0.93 · -22% | +12% · 0.85 · -18% | +21% · 1.00 · -14% | +34% · 1.76 · -8% | -25% · -1.64 · -28% | +24% · 1.14 · -17% | +13% · 0.89 · -22% | +16% · 0.84 · -28% | +11% · 0.72 · -32% |
| pullback · loose_risk | -3% · -0.47 · -16% | +13% · 1.01 · -15% | +5% · 0.43 · -19% | +19% · 0.99 · -12% | +33% · 1.68 · -11% | -17% · -2.16 · -18% | +7% · 0.56 · -16% | +9% · 0.73 · -19% | +8% · 0.57 · -22% | +7% · 0.59 · -22% |
| pullback · pos5 | -14% · -0.71 · -37% | +20% · 1.10 · -17% | +12% · 0.78 · -18% | +9% · 0.52 · -15% | +8% · 0.50 · -13% | -33% · -2.24 · -35% | +14% · 0.65 · -22% | +16% · 0.94 · -18% | +3% · 0.26 · -44% | +8% · 0.50 · -44% |
| pullback · pos7 | -10% · -0.73 · -30% | +15% · 0.94 · -20% | +11% · 0.75 · -19% | +15% · 0.77 · -14% | +12% · 0.73 · -11% | -30% · -2.01 · -32% | +9% · 0.67 · -18% | +13% · 0.85 · -20% | +3% · 0.27 · -38% | +7% · 0.50 · -38% |
| |  | | | | | | | | | |
| S&P 500 (SPY) | -10% · -0.14 · -52% | +15% · 0.96 · -19% | +12% · 0.88 · -19% | +17% · 0.64 · -34% | +31% · 2.13 · -5% | -19% · -0.74 · -24% | +22% · 1.42 · -19% | +13% · 0.92 · -19% | +15% · 0.81 · -34% | +11% · 0.64 · -52% |
| Hold all the stocks | -4% · 0.05 · -50% | +21% · 1.19 · -21% | +16% · 1.13 · -20% | +21% · 0.72 · -38% | +34% · 2.15 · -6% | -11% · -0.37 · -21% | +27% · 1.36 · -23% | +18% · 1.16 · -21% | +18% · 0.86 · -38% | +15% · 0.77 · -50% |

## Decision table: in-sample 2010-2019 (where settings may change) · out-of-sample 2020-now (only to check)

| Bot · variant | IS yearly | IS Sharpe | IS max drop | IS invested | OOS yearly | OOS Sharpe | OOS max drop | OOS invested |
|---|---|---|---|---|---|---|---|---|
| strong · smart | +15% | 1.04 | -21% | 96% | +7% | 0.44 | -30% | 90% |
| strong · plain | +22% | 1.03 | -30% | 99% | +35% | 1.03 | -41% | 99% |
| strong · no_regime | +17% | 1.08 | -20% | 99% | +4% | 0.28 | -32% | 91% |
| strong · no_score | +13% | 1.05 | -17% | 83% | +7% | 0.45 | -30% | 90% |
| strong · no_selfcheck | +13% | 1.06 | -15% | 84% | +7% | 0.43 | -30% | 90% |
| strong · score_m10 | +15% | 1.01 | -21% | 96% | +7% | 0.46 | -30% | 90% |
| strong · score_p10 | +15% | 1.00 | -23% | 96% | +7% | 0.44 | -31% | 89% |
| strong · first_combo | +12% | 0.97 | -15% | 83% | +6% | 0.40 | -32% | 86% |
| strong · risk_1 | +13% | 1.07 | -15% | 84% | +6% | 0.43 | -30% | 88% |
| strong · loose_risk | +10% | 0.85 | -20% | 78% | +2% | 0.24 | -21% | 71% |
| strong · combo_back | +10% | 0.76 | -23% | 64% | +12% | 0.76 | -23% | 71% |
| strong · pos5 | +12% | 0.75 | -27% | 95% | +9% | 0.54 | -33% | 85% |
| strong · pos7 | +14% | 0.88 | -25% | 97% | +5% | 0.37 | -35% | 84% |
| adaptive · smart | +10% | 0.78 | -18% | 90% | +10% | 0.60 | -30% | 89% |
| adaptive · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| adaptive · no_regime | +11% | 0.74 | -21% | 99% | +11% | 0.60 | -30% | 91% |
| adaptive · no_score | +14% | 0.98 | -18% | 93% | +11% | 0.61 | -30% | 89% |
| adaptive · no_selfcheck | +10% | 0.77 | -18% | 90% | +10% | 0.60 | -30% | 89% |
| adaptive · score_m10 | +14% | 0.98 | -18% | 93% | +11% | 0.61 | -30% | 89% |
| adaptive · score_p10 | +14% | 0.94 | -18% | 98% | +11% | 0.61 | -30% | 89% |
| adaptive · first_combo | +11% | 0.82 | -18% | 94% | +6% | 0.40 | -29% | 93% |
| adaptive · risk_1 | +10% | 0.76 | -18% | 90% | +11% | 0.64 | -29% | 90% |
| adaptive · loose_risk | +7% | 0.62 | -18% | 78% | +13% | 0.74 | -19% | 77% |
| adaptive · pos5 | +9% | 0.60 | -26% | 97% | +12% | 0.64 | -40% | 79% |
| adaptive · pos7 | +10% | 0.65 | -25% | 97% | +16% | 0.75 | -30% | 93% |
| trend · smart | +12% | 0.79 | -21% | 96% | +13% | 0.74 | -30% | 85% |
| trend · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| trend · no_regime | +14% | 0.92 | -18% | 99% | +13% | 0.68 | -30% | 89% |
| trend · no_score | +12% | 0.85 | -17% | 93% | +13% | 0.74 | -30% | 85% |
| trend · no_selfcheck | +12% | 0.79 | -21% | 96% | +13% | 0.74 | -30% | 85% |
| trend · score_m10 | +12% | 0.85 | -17% | 93% | +13% | 0.74 | -30% | 85% |
| trend · score_p10 | +12% | 0.83 | -18% | 92% | +14% | 0.77 | -31% | 87% |
| trend · first_combo | +11% | 0.80 | -24% | 94% | +8% | 0.51 | -32% | 86% |
| trend · risk_1 | +12% | 0.80 | -22% | 96% | +13% | 0.74 | -30% | 85% |
| trend · loose_risk | +11% | 0.88 | -17% | 83% | +14% | 0.80 | -19% | 78% |
| trend · pos5 | +9% | 0.62 | -22% | 93% | +16% | 0.77 | -38% | 77% |
| trend · pos7 | +11% | 0.71 | -22% | 97% | +18% | 0.86 | -35% | 84% |
| momentum · smart | +12% | 0.82 | -20% | 97% | +14% | 0.72 | -30% | 87% |
| momentum · plain | +24% | 1.10 | -31% | 99% | +44% | 1.14 | -45% | 98% |
| momentum · no_regime | +16% | 1.01 | -22% | 98% | +15% | 0.72 | -31% | 88% |
| momentum · no_score | +12% | 0.82 | -20% | 97% | +14% | 0.72 | -30% | 87% |
| momentum · no_selfcheck | +12% | 0.83 | -22% | 93% | +14% | 0.72 | -30% | 87% |
| momentum · score_m10 | +12% | 0.82 | -20% | 97% | +14% | 0.72 | -30% | 87% |
| momentum · score_p10 | +14% | 0.90 | -23% | 98% | +14% | 0.72 | -30% | 87% |
| momentum · first_combo | +14% | 0.93 | -24% | 97% | +10% | 0.60 | -29% | 93% |
| momentum · risk_1 | +12% | 0.83 | -21% | 92% | +11% | 0.62 | -31% | 83% |
| momentum · loose_risk | +9% | 0.69 | -17% | 79% | +20% | 0.97 | -23% | 78% |
| momentum · pos5 | +9% | 0.57 | -28% | 93% | +22% | 0.91 | -29% | 89% |
| momentum · pos7 | +13% | 0.82 | -27% | 97% | +16% | 0.78 | -30% | 90% |
| pullback · smart | +15% | 0.97 | -22% | 97% | +16% | 0.85 | -28% | 91% |
| pullback · plain | +20% | 0.94 | -32% | 99% | +46% | 1.23 | -45% | 98% |
| pullback · no_regime | +14% | 0.94 | -25% | 98% | +17% | 0.83 | -28% | 97% |
| pullback · no_score | +11% | 0.82 | -22% | 85% | +16% | 0.85 | -28% | 91% |
| pullback · no_selfcheck | +12% | 0.87 | -22% | 92% | +16% | 0.85 | -28% | 91% |
| pullback · score_m10 | +10% | 0.83 | -18% | 82% | +16% | 0.85 | -28% | 91% |
| pullback · score_p10 | +10% | 0.75 | -25% | 85% | +16% | 0.85 | -28% | 91% |
| pullback · first_combo | +12% | 0.86 | -21% | 92% | +11% | 0.66 | -28% | 90% |
| pullback · risk_1 | +13% | 0.89 | -22% | 94% | +16% | 0.84 | -28% | 91% |
| pullback · loose_risk | +9% | 0.73 | -19% | 79% | +8% | 0.57 | -22% | 65% |
| pullback · pos5 | +16% | 0.94 | -18% | 97% | +3% | 0.26 | -44% | 85% |
| pullback · pos7 | +13% | 0.85 | -20% | 97% | +3% | 0.27 | -38% | 72% |
| Hold / SPY ins | +18% / +13% | 1.16 / 0.92 | -21% / -19% | | | | | |
| Hold / SPY oos | +18% / +15% | 0.86 / 0.81 | -38% / -34% | | | | | |

## Inside each smart bot

### Strong Stocks on Sale

Sectors (first day, sector): []

Closed trades 2199 · exits {'Signal': 1800, 'Stop Loss': 399} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +9%/yr Sharpe 0.54, neutral 1164 days +28%/yr Sharpe 1.55, bear 607 days -15%/yr Sharpe -0.75, stress 277 days +14%/yr Sharpe 1.12

By strategy: Donchian Breakout (Turtle) 1709 trades +362,134 win 41%, Mean Reversion & Multi-Factor Strategy & Regime-Based Strategy & Portfolio-Level Strategy (4/4) 90 trades +1,388 win 56%, Momentum Strategy & VWAP Mean Reversion & Multi-Factor Strategy (3/3) 47 trades +21,757 win 64%, VWAP Mean Reversion & Multi-Factor Strategy & Momentum Strategy & Portfolio-Level Strategy (4/4) 42 trades +4,002 win 57%, VWAP Mean Reversion & RSI Mean Reversion & Relative Strength Strategy & Portfolio-Level Strategy (3/4) 207 trades +60,961 win 64%, VWAP Mean Reversion & Statistical Arbitrage & Multi-Factor Strategy & Relative Strength Strategy (3/4) 104 trades +664 win 61%

### Adaptive All-Weather

Sectors (first day, sector): []

Closed trades 1763 · exits {'Signal': 1403, 'Stop Loss': 360} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +8%/yr Sharpe 0.50, neutral 1164 days +22%/yr Sharpe 1.30, bear 607 days -11%/yr Sharpe -0.57, stress 277 days +11%/yr Sharpe 0.89

By strategy: Bollinger Breakout 75 trades +1,540 win 44%, Breakout Strategy 116 trades +112,154 win 35%, Donchian Breakout (Turtle) 129 trades +18,001 win 42%, EMA Crossover 23 trades -6,290 win 30%, Golden Cross (50/200) 6 trades +10,375 win 17%, MACD Crossover 99 trades +2,402 win 36%, MFI Money Flow (Volume) 3 trades +6,506 win 67%, Machine Learning Signal Combination 25 trades +2,003 win 32%, Mean Reversion 28 trades +8,334 win 96%, Momentum Strategy 77 trades +15,842 win 42%, Moving Average Crossover 9 trades +10,860 win 56%, Multi-Factor Strategy 44 trades -242 win 27%, OBV Trend (Volume) 97 trades +3,157 win 43%, Pairs Trading 1 trades +433 win 100%, Portfolio-Level Strategy 54 trades +53,439 win 33%, Regime-Based Strategy 66 trades -2,066 win 41%, Relative Strength Strategy 280 trades +102,996 win 46%, SMA Crossover 23 trades -5,484 win 35%, Statistical Arbitrage 7 trades +429 win 57%, Trend Following 60 trades +7,084 win 42%, VWAP Mean Reversion 29 trades +4,258 win 79%, VWAP Reclaim / Pullback 41 trades +4,539 win 34%, VWMA Crossover (Volume) 40 trades -2,222 win 32%, Volatility Breakout 208 trades -23,539 win 39%, Volume Breakout 223 trades -2,498 win 40%

### Trend Rider

Sectors (first day, sector): []

Closed trades 1679 · exits {'Signal': 1315, 'Stop Loss': 364} · sessions blocked {'pause': 0, 'streak': 0, 'day': 0, 'regime': 0} · pauses 0 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +10%/yr Sharpe 0.62, neutral 1164 days +22%/yr Sharpe 1.20, bear 607 days -7%/yr Sharpe -0.34, stress 277 days +17%/yr Sharpe 1.21

By strategy: Bollinger Breakout 64 trades -5,522 win 42%, Breakout Strategy 127 trades +286,091 win 32%, Donchian Breakout (Turtle) 143 trades +30,583 win 43%, EMA Crossover 12 trades -74 win 33%, Golden Cross (50/200) 6 trades +10,627 win 17%, MACD Crossover 96 trades +2,744 win 33%, MFI Money Flow (Volume) 4 trades +1,223 win 50%, Machine Learning Signal Combination 25 trades +216 win 40%, Mean Reversion 23 trades +4,473 win 78%, Momentum Strategy 68 trades +18,150 win 37%, Moving Average Crossover 5 trades +1,543 win 40%, Multi-Factor Strategy 41 trades -5,225 win 24%, OBV Trend (Volume) 79 trades +4,646 win 41%, Pairs Trading 1 trades +3,855 win 100%, Portfolio-Level Strategy 66 trades +61,683 win 33%, RSI Mean Reversion 1 trades +730 win 100%, Regime-Based Strategy 68 trades +1,582 win 46%, Relative Strength Strategy 267 trades +52,978 win 45%, SMA Crossover 17 trades -1,488 win 53%, Statistical Arbitrage 7 trades -1,872 win 57%, Trend Following 60 trades -1,489 win 45%, VWAP Mean Reversion 29 trades +6,811 win 72%, VWAP Reclaim / Pullback 46 trades -4,732 win 26%, VWMA Crossover (Volume) 38 trades -3,066 win 32%, Volatility Breakout 192 trades +28,793 win 38%, Volume Breakout 194 trades +24,374 win 43%

### Momentum Leaders

Sectors (first day, sector): []

Closed trades 1789 · exits {'Signal': 1393, 'Stop Loss': 396} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +11%/yr Sharpe 0.60, neutral 1164 days +25%/yr Sharpe 1.30, bear 607 days -12%/yr Sharpe -0.60, stress 277 days +9%/yr Sharpe 0.63

By strategy: Bollinger Breakout 72 trades -19,309 win 36%, Breakout Strategy 131 trades +136,361 win 34%, Donchian Breakout (Turtle) 167 trades +50,793 win 44%, EMA Crossover 15 trades -908 win 27%, Golden Cross (50/200) 4 trades -2,384 win 0%, MACD Crossover 91 trades -3,535 win 31%, MFI Money Flow (Volume) 3 trades +287 win 33%, Machine Learning Signal Combination 30 trades -10 win 43%, Mean Reversion 26 trades +10,903 win 92%, Momentum Strategy 66 trades +26,399 win 38%, Moving Average Crossover 4 trades +1,315 win 25%, Multi-Factor Strategy 45 trades -3,336 win 27%, OBV Trend (Volume) 89 trades +16,258 win 42%, Portfolio-Level Strategy 59 trades +61,221 win 29%, Regime-Based Strategy 73 trades +8,242 win 59%, Relative Strength Strategy 272 trades +150,246 win 42%, SMA Crossover 24 trades +2,545 win 42%, Statistical Arbitrage 8 trades -393 win 62%, Trend Following 62 trades +10,629 win 47%, VWAP Mean Reversion 27 trades +5,203 win 78%, VWAP Reclaim / Pullback 64 trades +10,848 win 30%, VWMA Crossover (Volume) 44 trades -5,822 win 30%, Volatility Breakout 197 trades +72,908 win 42%, Volume Breakout 216 trades -39,395 win 38%

### Pullback Buyer

Sectors (first day, sector): []

Closed trades 2856 · exits {'Signal': 1515, 'Time Stop': 800, 'Stop Loss': 541} · sessions blocked {'pause': 11, 'streak': 0, 'day': 0, 'regime': 0} · pauses 1 · regime days {'bull': 2916, 'neutral': 1165, 'bear': 607, 'stress': 277} · regime now neutral

By regime (the session before): bull 2916 days +13%/yr Sharpe 0.81, neutral 1164 days +27%/yr Sharpe 1.45, bear 607 days -13%/yr Sharpe -0.65, stress 277 days +11%/yr Sharpe 0.84

By strategy: Bollinger Breakout 145 trades -21,440 win 34%, Breakout Strategy 242 trades +486,063 win 27%, Donchian Breakout (Turtle) 241 trades +108,997 win 38%, EMA Crossover 22 trades +11,761 win 45%, Golden Cross (50/200) 17 trades +31,384 win 18%, MACD Crossover 146 trades +6,742 win 38%, MFI Money Flow (Volume) 2 trades +951 win 50%, Machine Learning Signal Combination 44 trades +2,908 win 23%, Mean Reversion 49 trades -2,998 win 65%, Momentum Strategy 109 trades +9,571 win 22%, Moving Average Crossover 6 trades +5,315 win 33%, Multi-Factor Strategy 81 trades -8,813 win 22%, OBV Trend (Volume) 160 trades -3,051 win 38%, Portfolio-Level Strategy 83 trades +50,782 win 24%, Regime-Based Strategy 101 trades -5,565 win 47%, Relative Strength Strategy 525 trades +112,716 win 33%, SMA Crossover 32 trades -1,777 win 28%, Statistical Arbitrage 19 trades +2,163 win 63%, Trend Following 77 trades +24,024 win 35%, VWAP Mean Reversion 50 trades +22,957 win 68%, VWAP Reclaim / Pullback 75 trades -12,144 win 25%, VWMA Crossover (Volume) 60 trades +21,360 win 35%, Volatility Breakout 270 trades +75,588 win 40%, Volume Breakout 300 trades -58,415 win 31%

