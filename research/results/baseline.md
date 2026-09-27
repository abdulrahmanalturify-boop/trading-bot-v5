# Lab results · baseline

Run 2026-09-27 11:00 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 0.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| SMA Crossover | +10.8% | 1.12 | -10.7% | 0.57 | 12% | 2.6 | 50% | +12.9% | 0.88 | -23.0% |
| EMA Crossover | +10.8% | 1.22 | -11.7% | 0.51 | 7% | 5.3 | 39% | +12.7% | 0.87 | -22.7% |
| Golden Cross (50/200) | +14.1% | 1.21 | -14.9% | 0.62 | 14% | 0.6 | 58% | +16.7% | 0.98 | -24.8% |
| RSI Mean Reversion | +1.3% | 0.76 | -2.9% | 0.28 | 5% | 0.5 | 81% | +6.0% | 0.63 | -16.1% |
| MACD Crossover | +7.7% | 1.08 | -12.7% | 0.45 | 7% | 10.1 | 43% | +9.4% | 0.69 | -23.1% |
| Bollinger Breakout | +4.3% | 0.96 | -8.1% | 0.32 | 5% | 4.9 | 43% | +9.2% | 0.72 | -22.0% |
| Donchian Breakout (Turtle) | +7.1% | 1.09 | -9.3% | 0.39 | 4% | 4.3 | 46% | +12.0% | 0.84 | -23.2% |
| OBV Trend (Volume) | +4.1% | 0.90 | -7.1% | 0.21 | 5% | 11.3 | 36% | +8.7% | 0.65 | -25.0% |
| Volume Breakout | +4.2% | 0.97 | -5.7% | 0.22 | 3% | 2.6 | 45% | +11.1% | 0.83 | -21.0% |
| VWMA Crossover (Volume) | +8.4% | 1.05 | -14.5% | 0.45 | 4% | 15.0 | 34% | +10.6% | 0.76 | -23.9% |
| MFI Money Flow (Volume) | +1.8% | 1.18 | -2.3% | 0.31 | 11% | 0.5 | 78% | +9.0% | 0.87 | -16.1% |
| Trend Pullback | +0.2% | 0.29 | -1.9% | 0.00 | 3% | 0.5 | 42% | +2.3% | 0.46 | -10.0% |
| Breakout & Retest | +0.4% | 0.70 | -1.0% | 0.07 | 6% | 1.5 | 42% | +1.2% | 0.22 | -11.9% |
| Squeeze Breakout | +1.3% | 1.07 | -1.7% | 0.22 | 7% | 1.2 | 43% | +3.0% | 0.37 | -17.1% |
| Range Reversion | +0.2% | 0.59 | -0.3% | 0.00 | 4% | 0.2 | 46% | +1.4% | 0.44 | -6.4% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| SMA Crossover | +12.2% | 1.01 | -19.5% | 0.37 | 20% | 2.7 | 45% | +8.3% | 0.46 | -34.3% |
| EMA Crossover | +13.3% | 1.09 | -17.6% | 0.45 | 25% | 5.4 | 36% | +12.1% | 0.57 | -36.1% |
| Golden Cross (50/200) | +17.1% | 1.24 | -20.5% | 0.52 | 36% | 0.6 | 54% | +9.1% | 0.49 | -37.8% |
| RSI Mean Reversion | +1.4% | 0.34 | -10.2% | 0.19 | 13% | 0.4 | 75% | +2.5% | 0.23 | -36.7% |
| MACD Crossover | +9.2% | 0.84 | -18.4% | 0.40 | 20% | 10.0 | 40% | +11.5% | 0.51 | -32.4% |
| Bollinger Breakout | +7.6% | 1.05 | -8.5% | 0.30 | 20% | 4.7 | 43% | +8.0% | 0.42 | -35.5% |
| Donchian Breakout (Turtle) | +8.8% | 0.95 | -12.5% | 0.36 | 20% | 4.2 | 45% | +11.9% | 0.53 | -36.2% |
| OBV Trend (Volume) | +3.8% | 0.59 | -11.5% | 0.13 | 8% | 10.6 | 36% | +4.1% | 0.26 | -38.5% |
| Volume Breakout | +4.8% | 0.83 | -5.9% | 0.20 | 11% | 2.4 | 44% | +10.0% | 0.50 | -31.0% |
| VWMA Crossover (Volume) | +9.7% | 0.85 | -16.8% | 0.31 | 17% | 14.9 | 33% | +7.9% | 0.38 | -37.2% |
| MFI Money Flow (Volume) | +1.9% | 0.72 | -4.8% | 0.28 | 18% | 0.5 | 72% | +6.5% | 0.50 | -27.0% |
| Trend Pullback | +0.4% | 0.60 | -0.9% | -0.00 | 8% | 0.4 | 41% | +2.4% | 0.25 | -12.5% |
| Breakout & Retest | +0.1% | 0.17 | -1.2% | 0.03 | 7% | 1.0 | 39% | +0.8% | 0.17 | -14.7% |
| Squeeze Breakout | +0.5% | 0.39 | -2.7% | 0.01 | 9% | 1.0 | 39% | +3.7% | 0.31 | -19.4% |
| Range Reversion | +0.1% | 0.33 | -0.6% | 0.00 | 10% | 0.2 | 34% | +0.5% | 0.18 | -8.5% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | |

