# Lab results · market_filter

Run 2026-09-28 20:00 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.9% | 0.84 | -10.2% | 0.22 | 3% | 3.5 | 35% | +10.4% | 0.78 | -21.4% | +14.1% · 1.02 · -20.6% | +17.3% · 1.30 · -16.6% |
| Moving Average Crossover | +5.1% | 0.91 | -9.6% | 0.34 | 7% | 2.4 | 39% | +9.8% | 0.75 | -22.7% | +17.1% · 1.28 · -18.0% | +16.4% · 1.30 · -14.2% |
| Momentum Strategy | +8.3% | 1.12 | -9.2% | 0.43 | 5% | 2.7 | 46% | +12.7% | 0.86 | -24.2% | +17.7% · 1.13 · -21.5% | +16.7% · 1.15 · -18.2% |
| Breakout Strategy | +5.3% | 0.92 | -7.9% | 0.25 | 3% | 2.4 | 43% | +11.0% | 0.80 | -21.3% | +18.6% · 1.13 · -20.4% | +16.3% · 1.16 · -18.2% |
| Volatility Breakout | +3.4% | 0.72 | -9.1% | 0.22 | 3% | 9.4 | 40% | +6.6% | 0.51 | -27.6% | +9.0% · 0.69 · -24.2% | +10.1% · 0.85 · -14.8% |
| Mean Reversion | +3.4% | 1.07 | -3.6% | 0.40 | 11% | 2.5 | 74% | +8.4% | 0.74 | -15.8% | +12.7% · 0.94 · -19.7% | +10.5% · 0.88 · -15.9% |
| VWAP Mean Reversion | +2.5% | 0.98 | -3.4% | 0.32 | 7% | 1.1 | 76% | +8.0% | 0.75 | -15.2% | +21.1% · 1.28 · -18.3% | +16.1% · 1.20 · -13.8% |
| VWAP Reclaim / Pullback | +5.2% | 0.92 | -8.9% | 0.30 | 2% | 4.8 | 33% | +10.5% | 0.77 | -24.2% | +14.7% · 1.05 · -19.4% | +15.4% · 1.19 · -14.6% |
| Relative Strength Strategy | +5.3% | 1.02 | -6.5% | 0.32 | 4% | 2.2 | 48% | +13.4% | 0.90 | -22.6% | +21.9% · 1.21 · -24.6% | +20.9% · 1.28 · -19.4% |
| Pairs Trading | +5.1% | 1.39 | -5.1% | 0.48 | 13% | 1.6 | 78% | +10.2% | 0.73 | -23.8% | +14.4% · 1.03 · -22.8% | +15.0% · 1.15 · -21.1% |
| Statistical Arbitrage | +0.7% | 0.75 | -1.7% | 0.15 | 2% | 1.6 | 60% | +3.1% | 0.40 | -17.0% | +12.0% · 0.96 · -15.3% | +8.8% · 0.88 · -15.3% |
| Multi-Factor Strategy | +6.4% | 1.06 | -10.1% | 0.38 | 5% | 1.3 | 45% | +13.7% | 0.92 | -21.8% | +17.9% · 1.22 · -19.1% | +18.8% · 1.34 · -16.2% |
| Regime-Based Strategy | +2.8% | 0.90 | -4.9% | 0.25 | 4% | 6.1 | 55% | +8.6% | 0.67 | -23.6% | +8.9% · 0.63 · -31.9% | +10.1% · 0.78 · -20.7% |
| Machine Learning Signal Combination | +7.1% | 1.01 | -9.2% | 0.36 | 4% | 7.4 | 37% | +10.4% | 0.73 | -24.9% | +14.3% · 1.01 · -18.6% | +15.6% · 1.19 · -17.6% |
| Portfolio-Level Strategy | +13.6% | 1.20 | -14.2% | 0.56 | 13% | 0.9 | 49% | +17.3% | 0.94 | -29.0% | +24.8% · 1.04 · -36.5% | +23.6% · 1.17 · -32.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.88 | -8.0% | 0.23 | 14% | 2.9 | 36% | +7.4% | 0.44 | -28.5% | +6.5% · 0.42 · -23.0% | +7.8% · 0.51 · -21.5% |
| Moving Average Crossover | +5.1% | 0.79 | -9.9% | 0.16 | 12% | 2.0 | 34% | +7.8% | 0.45 | -28.5% | +7.6% · 0.50 · -33.3% | +9.3% · 0.65 · -21.0% |
| Momentum Strategy | +8.8% | 0.94 | -12.4% | 0.30 | 18% | 2.9 | 43% | +9.1% | 0.50 | -34.4% | +5.8% · 0.37 · -34.4% | +17.2% · 0.82 · -30.0% |
| Breakout Strategy | +7.9% | 0.97 | -9.5% | 0.27 | 14% | 2.2 | 45% | +9.7% | 0.50 | -33.3% | +33.4% · 1.15 · -28.9% | +29.4% · 1.16 · -23.0% |
| Volatility Breakout | +3.6% | 0.55 | -15.0% | 0.17 | 6% | 8.1 | 38% | +5.5% | 0.32 | -32.9% | +23.8% · 1.05 · -27.1% | +17.0% · 0.93 · -20.3% |
| Mean Reversion | +2.5% | 0.54 | -11.4% | 0.19 | 16% | 1.9 | 70% | +2.7% | 0.21 | -38.8% | +6.1% · 0.41 · -33.3% | +8.7% · 0.58 · -33.1% |
| VWAP Mean Reversion | +2.5% | 0.50 | -10.7% | 0.22 | 17% | 1.6 | 70% | +5.4% | 0.37 | -35.1% | +13.7% · 0.69 · -27.3% | +14.1% · 0.78 · -30.3% |
| VWAP Reclaim / Pullback | +7.6% | 1.04 | -7.3% | 0.28 | 8% | 4.6 | 31% | +8.1% | 0.41 | -32.0% | +17.3% · 0.84 · -32.5% | +13.3% · 0.78 · -23.7% |
| Relative Strength Strategy | +6.6% | 0.90 | -11.5% | 0.27 | 7% | 1.9 | 46% | +7.6% | 0.37 | -36.4% | +34.4% · 1.07 · -34.4% | +33.2% · 1.16 · -30.5% |
| Pairs Trading | +3.4% | 0.70 | -9.7% | 0.27 | 20% | 1.6 | 69% | +5.9% | 0.38 | -38.0% | +11.2% · 0.64 · -32.5% | +9.3% · 0.57 · -34.8% |
| Statistical Arbitrage | +0.7% | 0.60 | -2.0% | 0.14 | 7% | 1.4 | 59% | +1.5% | 0.17 | -20.0% | +8.4% · 0.58 · -33.3% | +4.2% · 0.38 · -22.9% |
| Multi-Factor Strategy | +6.8% | 0.99 | -6.7% | 0.35 | 25% | 1.0 | 50% | +8.5% | 0.47 | -32.8% | +3.9% · 0.30 · -28.0% | +8.4% · 0.54 · -26.8% |
| Regime-Based Strategy | +2.4% | 0.68 | -5.2% | 0.15 | 9% | 5.1 | 54% | +5.8% | 0.41 | -28.0% | +16.3% · 0.76 · -31.4% | +12.4% · 0.72 · -25.5% |
| Machine Learning Signal Combination | +5.6% | 0.73 | -10.5% | 0.24 | 10% | 6.6 | 34% | +9.2% | 0.50 | -29.8% | +21.7% · 1.00 · -22.6% | +15.3% · 0.84 · -22.4% |
| Portfolio-Level Strategy | +14.8% | 0.97 | -21.3% | 0.37 | 20% | 1.0 | 43% | +18.2% | 0.62 | -42.7% | +60.0% · 1.26 · -44.8% | +50.0% · 1.23 · -40.1% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

