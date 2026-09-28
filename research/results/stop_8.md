# Lab results · stop_8

Run 2026-09-28 20:11 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.80 | -11.4% | 0.27 | 3% | 3.7 | 34% | +11.4% | 0.84 | -22.3% | +13.7% · 0.96 · -17.4% | +14.4% · 1.09 · -16.0% |
| Moving Average Crossover | +5.0% | 0.88 | -10.6% | 0.33 | 6% | 2.5 | 37% | +10.8% | 0.81 | -22.8% | +17.8% · 1.26 · -17.5% | +17.6% · 1.35 · -16.0% |
| Momentum Strategy | +8.6% | 1.18 | -7.6% | 0.44 | 6% | 2.9 | 45% | +14.4% | 0.94 | -23.9% | +26.1% · 1.53 · -23.8% | +20.1% · 1.31 · -21.3% |
| Breakout Strategy | +5.2% | 0.92 | -8.3% | 0.29 | 5% | 2.5 | 43% | +11.3% | 0.82 | -21.0% | +17.0% · 1.11 · -21.7% | +16.5% · 1.19 · -16.4% |
| Volatility Breakout | +4.4% | 0.84 | -9.3% | 0.30 | 4% | 10.2 | 41% | +9.1% | 0.68 | -22.9% | +7.8% · 0.59 · -25.7% | +10.6% · 0.85 · -16.4% |
| Mean Reversion | +2.7% | 0.95 | -3.1% | 0.33 | 11% | 2.7 | 71% | +7.2% | 0.68 | -17.0% | +7.2% · 0.56 · -27.2% | +8.7% · 0.74 · -18.5% |
| VWAP Mean Reversion | +1.7% | 0.82 | -2.3% | 0.29 | 4% | 1.4 | 74% | +6.4% | 0.66 | -16.1% | +15.8% · 1.01 · -25.1% | +11.5% · 0.91 · -17.7% |
| VWAP Reclaim / Pullback | +5.5% | 0.96 | -7.6% | 0.38 | 2% | 5.0 | 33% | +12.1% | 0.85 | -22.2% | +17.7% · 1.18 · -19.6% | +16.2% · 1.19 · -16.3% |
| Relative Strength Strategy | +5.2% | 1.02 | -6.2% | 0.32 | 6% | 2.4 | 48% | +13.6% | 0.91 | -23.3% | +19.1% · 1.10 · -23.0% | +21.0% · 1.30 · -19.6% |
| Pairs Trading | +4.5% | 1.39 | -5.9% | 0.44 | 12% | 2.2 | 67% | +9.5% | 0.68 | -28.2% | +15.4% · 1.04 · -25.4% | +16.4% · 1.16 · -24.7% |
| Statistical Arbitrage | +0.7% | 0.72 | -1.7% | 0.12 | 4% | 1.7 | 60% | +2.9% | 0.38 | -16.4% | +13.1% · 0.99 · -18.7% | +8.6% · 0.85 · -14.3% |
| Multi-Factor Strategy | +6.2% | 1.07 | -8.5% | 0.40 | 4% | 1.4 | 43% | +14.8% | 0.99 | -21.1% | +20.9% · 1.42 · -15.0% | +20.1% · 1.48 · -14.4% |
| Regime-Based Strategy | +2.2% | 0.69 | -5.5% | 0.20 | 4% | 6.7 | 55% | +7.8% | 0.61 | -25.9% | +9.8% · 0.66 · -32.3% | +10.9% · 0.80 · -25.9% |
| Machine Learning Signal Combination | +7.4% | 1.03 | -9.5% | 0.42 | 6% | 8.0 | 37% | +13.2% | 0.86 | -21.1% | +16.5% · 1.12 · -23.0% | +17.8% · 1.29 · -16.5% |
| Portfolio-Level Strategy | +14.3% | 1.28 | -13.1% | 0.63 | 16% | 1.0 | 47% | +16.1% | 0.93 | -26.6% | +20.3% · 0.94 · -29.5% | +23.3% · 1.18 · -31.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +5.9% | 0.86 | -7.4% | 0.26 | 14% | 3.2 | 35% | +7.3% | 0.42 | -30.8% | +6.1% · 0.39 · -33.9% | +4.9% · 0.34 · -30.9% |
| Moving Average Crossover | +5.0% | 0.79 | -8.5% | 0.17 | 9% | 2.2 | 34% | +7.6% | 0.41 | -34.4% | +13.2% · 0.71 · -27.4% | +13.1% · 0.80 · -21.7% |
| Momentum Strategy | +9.1% | 0.99 | -10.5% | 0.31 | 20% | 3.5 | 40% | +14.0% | 0.58 | -32.9% | +14.7% · 0.69 · -35.9% | +15.9% · 0.75 · -28.9% |
| Breakout Strategy | +7.5% | 0.94 | -9.4% | 0.26 | 15% | 2.4 | 42% | +11.5% | 0.51 | -32.7% | +29.0% · 1.05 · -31.0% | +29.8% · 1.19 · -27.3% |
| Volatility Breakout | +4.3% | 0.56 | -16.2% | 0.13 | 9% | 10.2 | 38% | +6.0% | 0.32 | -33.7% | +25.6% · 1.04 · -32.7% | +17.5% · 0.88 · -25.3% |
| Mean Reversion | +2.1% | 0.83 | -4.7% | 0.25 | 19% | 2.3 | 65% | +3.1% | 0.26 | -25.2% | +6.9% · 0.47 · -25.8% | +6.4% · 0.47 · -25.0% |
| VWAP Mean Reversion | +1.7% | 0.60 | -5.4% | 0.17 | 18% | 2.0 | 65% | +3.9% | 0.35 | -24.1% | +8.7% · 0.51 · -30.1% | +8.0% · 0.53 · -24.6% |
| VWAP Reclaim / Pullback | +7.2% | 0.93 | -11.6% | 0.24 | 9% | 5.4 | 30% | +7.3% | 0.38 | -37.8% | +15.4% · 0.76 · -30.9% | +14.6% · 0.81 · -26.9% |
| Relative Strength Strategy | +6.4% | 0.94 | -9.3% | 0.24 | 10% | 2.3 | 43% | +7.6% | 0.39 | -35.8% | +25.5% · 0.92 · -37.6% | +27.8% · 1.03 · -35.3% |
| Pairs Trading | +3.8% | 0.87 | -6.9% | 0.30 | 16% | 2.5 | 54% | +10.3% | 0.55 | -37.8% | +12.6% · 0.64 · -41.7% | +10.8% · 0.59 · -42.2% |
| Statistical Arbitrage | +0.9% | 0.76 | -1.7% | 0.13 | 12% | 1.6 | 60% | +2.7% | 0.29 | -19.8% | +11.3% · 0.71 · -30.3% | +6.8% · 0.57 · -20.4% |
| Multi-Factor Strategy | +7.1% | 1.00 | -7.1% | 0.29 | 24% | 1.3 | 41% | +9.4% | 0.50 | -33.4% | +13.9% · 0.73 · -29.8% | +12.6% · 0.73 · -25.1% |
| Regime-Based Strategy | +2.6% | 0.72 | -6.1% | 0.16 | 12% | 5.8 | 52% | +5.4% | 0.36 | -31.2% | +10.2% · 0.51 · -38.8% | +11.0% · 0.62 · -30.0% |
| Machine Learning Signal Combination | +7.9% | 0.85 | -14.2% | 0.25 | 14% | 8.1 | 35% | +8.5% | 0.43 | -37.0% | +22.6% · 1.01 · -36.5% | +17.2% · 0.87 · -31.0% |
| Portfolio-Level Strategy | +14.7% | 1.07 | -17.0% | 0.38 | 25% | 1.3 | 33% | +19.8% | 0.72 | -37.4% | +47.0% · 1.19 · -45.0% | +46.4% · 1.26 · -39.9% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

