# Factor test, S&P 500 (2026-10-18 13:09 UTC)

498 stocks with prices, 498 with SEC facts, 164 month-ends, 78,313 stock-months. Training 2013-01-01 .. 2019-12-31, testing after 2019-12-31 .. 2026-08-31.

**Decision rule (fixed before the run):** For each horizon: candidates are the current V3 blend (four price factors, 35/25/25/15), all seven groups (the four, classic 12-1 momentum, value, quality) equally weighted, and an IC-weighted blend (weights proportional to each group's training-years mean IC, zero when it is not positive). Chosen: the candidate with the highest testing-years mean IC whose testing t-stat is at least 2; if none reaches 2, the highest testing IC, flagged as weak. A group whose training IC is not positive gets no weight.

| horizon | chosen | weak? | testing IC | testing t | weights |
|---|---|---|---|---|---|
| 20 sessions | seven groups, equal | yes | 0.0066 | 0.32 | {'Q Momentum': 0.143, 'Q Trend': 0.143, 'Q Low Risk': 0.143, 'Q Reversal': 0.143, 'Momentum 12-1': 0.143, 'Value (in sector)': 0.143, 'Quality': 0.143} |
| 60 sessions | seven groups, equal | yes | -0.0056 | -0.17 | {'Q Momentum': 0.143, 'Q Trend': 0.143, 'Q Low Risk': 0.143, 'Q Reversal': 0.143, 'Momentum 12-1': 0.143, 'Value (in sector)': 0.143, 'Quality': 0.143} |
| 120 sessions | seven groups, equal | yes | 0.0014 | 0.03 | {'Q Momentum': 0.143, 'Q Trend': 0.143, 'Q Low Risk': 0.143, 'Q Reversal': 0.143, 'Momentum 12-1': 0.143, 'Value (in sector)': 0.143, 'Quality': 0.143} |

# Horizon: 20 sessions

Value as Value (in sector), quality as Quality (picked on the training years).

## Blends · train · 20 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 20 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | -0.0305 | -1.65 | 0.464 | -0.614 | -0.74 | 84 |
| seven groups, equal | -0.0241 | -1.21 | 0.464 | -0.452 | -0.49 | 84 |
| seven groups, IC-weighted | 0.0162 | 1.12 | 0.524 | 0.182 | 0.29 | 84 |
| value + quality only | -0.0098 | -0.85 | 0.429 | -0.294 | -0.53 | 84 |

## Blends · test · 20 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 20 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | 0.0003 | 0.01 | 0.55 | -0.213 | -0.15 | 80 |
| seven groups, equal | 0.0066 | 0.32 | 0.575 | -0.137 | -0.1 | 80 |
| seven groups, IC-weighted | -0.005 | -0.28 | 0.487 | -0.139 | -0.11 | 80 |
| value + quality only | 0.0052 | 0.44 | 0.475 | 0.129 | 0.16 | 80 |

## Factors · train · 20 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 20 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | -0.0296 | -1.74 | 0.464 | -0.484 | -0.65 | 84 |
| Q Trend | -0.0267 | -1.54 | 0.452 | -0.423 | -0.55 | 84 |
| Q Low Risk | -0.0285 | -1.38 | 0.488 | -0.716 | -0.72 | 84 |
| Q Reversal | 0.0147 | 1.03 | 0.56 | 0.137 | 0.22 | 84 |
| Momentum 12-1 | 0.0011 | 0.05 | 0.548 | 0.13 | 0.13 | 84 |
| Value | -0.0194 | -1.09 | 0.417 | -0.493 | -0.61 | 84 |
| Quality | 0.0076 | 0.75 | 0.548 | 0.12 | 0.24 | 84 |
| Value (in sector) | -0.0176 | -1.15 | 0.464 | -0.38 | -0.57 | 84 |
| Quality (in sector) | 0.0007 | 0.08 | 0.464 | 0.024 | 0.05 | 84 |
| f:drawdown_63 | -0.0382 | -2.17 | 0.429 | -0.832 | -1.07 | 84 |
| f:ema_diff | -0.0252 | -1.45 | 0.44 | -0.432 | -0.55 | 84 |
| f:excess_21 | -0.0338 | -2.14 | 0.44 | -0.418 | -0.63 | 84 |
| f:excess_63 | -0.0191 | -1.09 | 0.464 | -0.346 | -0.43 | 84 |
| f:reversal_5 | 0.0147 | 1.03 | 0.56 | 0.137 | 0.22 | 84 |
| f:trend_100 | -0.0272 | -1.58 | 0.44 | -0.396 | -0.51 | 84 |
| f:vol_20 | 0.0123 | 0.61 | 0.464 | 0.476 | 0.51 | 84 |
| f:mom_12_1 | 0.0011 | 0.05 | 0.548 | 0.13 | 0.13 | 84 |
| f:ep | -0.0132 | -0.83 | 0.452 | -0.493 | -0.69 | 84 |
| f:bp | -0.0256 | -1.72 | 0.369 | -0.462 | -0.64 | 84 |
| f:cp | -0.0065 | -0.39 | 0.476 | -0.318 | -0.41 | 84 |
| f:roe | 0.0023 | 0.23 | 0.512 | -0.269 | -0.61 | 84 |
| f:gpa | 0.0212 | 1.77 | 0.548 | 0.34 | 0.57 | 84 |
| f:lev | -0.0119 | -1.32 | 0.417 | -0.123 | -0.26 | 84 |
| f:acc | 0.0134 | 1.35 | 0.571 | 0.277 | 0.59 | 84 |

## Factors · test · 20 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 20 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | 0.0105 | 0.52 | 0.55 | 0.319 | 0.22 | 80 |
| Q Trend | 0.0071 | 0.34 | 0.575 | 0.164 | 0.11 | 80 |
| Q Low Risk | -0.0296 | -1.16 | 0.463 | -1.552 | -0.87 | 80 |
| Q Reversal | -0.0044 | -0.24 | 0.463 | -0.159 | -0.12 | 80 |
| Momentum 12-1 | 0.015 | 0.67 | 0.613 | 0.378 | 0.25 | 80 |
| Value | 0.0113 | 0.53 | 0.525 | -0.046 | -0.03 | 80 |
| Quality | -0.0035 | -0.25 | 0.425 | -0.044 | -0.05 | 80 |
| Value (in sector) | 0.0105 | 0.6 | 0.512 | 0.187 | 0.17 | 80 |
| Quality (in sector) | -0.0093 | -0.82 | 0.4 | -0.364 | -0.48 | 80 |
| f:drawdown_63 | -0.0121 | -0.59 | 0.487 | -0.74 | -0.51 | 80 |
| f:ema_diff | 0.0068 | 0.33 | 0.575 | 0.168 | 0.11 | 80 |
| f:excess_21 | 0.0206 | 1.11 | 0.562 | 0.489 | 0.39 | 80 |
| f:excess_63 | -0.004 | -0.19 | 0.562 | 0.019 | 0.01 | 80 |
| f:reversal_5 | -0.0044 | -0.24 | 0.463 | -0.159 | -0.12 | 80 |
| f:trend_100 | 0.0072 | 0.35 | 0.575 | 0.26 | 0.17 | 80 |
| f:vol_20 | 0.0383 | 1.45 | 0.55 | 1.891 | 1.0 | 80 |
| f:mom_12_1 | 0.015 | 0.67 | 0.613 | 0.378 | 0.25 | 80 |
| f:ep | 0.0128 | 0.83 | 0.512 | -0.348 | -0.31 | 80 |
| f:bp | 0.0024 | 0.13 | 0.5 | 0.216 | 0.19 | 80 |
| f:cp | 0.0144 | 0.71 | 0.475 | 0.145 | 0.1 | 80 |
| f:roe | 0.0065 | 0.6 | 0.487 | -0.45 | -0.59 | 80 |
| f:gpa | 0.0072 | 0.55 | 0.487 | -0.372 | -0.44 | 80 |
| f:lev | -0.0142 | -1.32 | 0.412 | -0.135 | -0.18 | 80 |
| f:acc | -0.001 | -0.12 | 0.5 | 0.388 | 0.64 | 80 |

# Horizon: 60 sessions

Value as Value (in sector), quality as Quality (picked on the training years).

## Blends · train · 60 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 60 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | -0.0232 | -0.82 | 0.464 | -0.925 | -0.41 | 84 |
| seven groups, equal | -0.0255 | -0.89 | 0.452 | -0.815 | -0.35 | 84 |
| seven groups, IC-weighted | 0.0249 | 1.0 | 0.631 | 0.624 | 0.29 | 84 |
| value + quality only | -0.0289 | -1.45 | 0.369 | -1.264 | -0.73 | 84 |

## Blends · test · 60 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 60 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | -0.0155 | -0.44 | 0.474 | -0.978 | -0.24 | 78 |
| seven groups, equal | -0.0056 | -0.17 | 0.526 | -0.64 | -0.17 | 78 |
| seven groups, IC-weighted | -0.0154 | -0.51 | 0.513 | 0.06 | 0.02 | 78 |
| value + quality only | 0.0124 | 0.59 | 0.513 | -0.034 | -0.01 | 78 |

## Factors · train · 60 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 60 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | -0.0216 | -0.82 | 0.429 | -0.761 | -0.36 | 84 |
| Q Trend | -0.0125 | -0.44 | 0.476 | -0.303 | -0.13 | 84 |
| Q Low Risk | -0.0279 | -0.85 | 0.512 | -1.371 | -0.51 | 84 |
| Q Reversal | -0.0013 | -0.06 | 0.512 | -0.091 | -0.05 | 84 |
| Momentum 12-1 | 0.0084 | 0.26 | 0.571 | 0.238 | 0.09 | 84 |
| Value | -0.0628 | -2.03 | 0.321 | -2.211 | -0.77 | 84 |
| Quality | 0.0224 | 1.21 | 0.595 | 0.507 | 0.31 | 84 |
| Value (in sector) | -0.0519 | -1.96 | 0.31 | -1.716 | -0.75 | 84 |
| Quality (in sector) | 0.0106 | 0.63 | 0.56 | 0.176 | 0.11 | 84 |
| f:drawdown_63 | -0.0256 | -0.92 | 0.488 | -1.276 | -0.58 | 84 |
| f:ema_diff | -0.013 | -0.45 | 0.452 | -0.297 | -0.13 | 84 |
| f:excess_21 | -0.0199 | -0.75 | 0.452 | -0.445 | -0.21 | 84 |
| f:excess_63 | -0.0173 | -0.65 | 0.512 | -0.302 | -0.14 | 84 |
| f:reversal_5 | -0.0013 | -0.06 | 0.512 | -0.091 | -0.05 | 84 |
| f:trend_100 | -0.0114 | -0.41 | 0.5 | -0.17 | -0.07 | 84 |
| f:vol_20 | 0.0253 | 0.77 | 0.524 | 1.455 | 0.5 | 84 |
| f:mom_12_1 | 0.0084 | 0.26 | 0.571 | 0.238 | 0.09 | 84 |
| f:ep | -0.0489 | -1.78 | 0.298 | -2.078 | -0.88 | 84 |
| f:bp | -0.0624 | -2.51 | 0.274 | -1.867 | -0.82 | 84 |
| f:cp | -0.0406 | -1.38 | 0.345 | -1.509 | -0.58 | 84 |
| f:roe | -0.0 | -0.0 | 0.5 | -0.792 | -0.56 | 84 |
| f:gpa | 0.042 | 1.81 | 0.619 | 1.063 | 0.48 | 84 |
| f:lev | -0.0049 | -0.33 | 0.464 | -0.225 | -0.15 | 84 |
| f:acc | 0.0291 | 1.94 | 0.619 | 1.069 | 0.76 | 84 |

## Factors · test · 60 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 60 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | -0.0047 | -0.14 | 0.474 | 0.337 | 0.08 | 78 |
| Q Trend | -0.0016 | -0.04 | 0.487 | 0.515 | 0.12 | 78 |
| Q Low Risk | -0.0573 | -1.39 | 0.397 | -4.556 | -0.89 | 78 |
| Q Reversal | 0.011 | 0.38 | 0.513 | -0.089 | -0.02 | 78 |
| Momentum 12-1 | 0.0028 | 0.08 | 0.526 | 1.052 | 0.26 | 78 |
| Value | 0.0291 | 0.72 | 0.551 | -0.011 | -0.0 | 78 |
| Quality | -0.0194 | -0.74 | 0.333 | -0.658 | -0.24 | 78 |
| Value (in sector) | 0.0275 | 0.81 | 0.526 | 0.541 | 0.15 | 78 |
| Quality (in sector) | -0.0271 | -1.31 | 0.321 | -1.405 | -0.57 | 78 |
| f:drawdown_63 | -0.0364 | -1.04 | 0.436 | -2.612 | -0.61 | 78 |
| f:ema_diff | 0.0003 | 0.01 | 0.487 | 0.467 | 0.11 | 78 |
| f:excess_21 | -0.0054 | -0.16 | 0.462 | 0.15 | 0.04 | 78 |
| f:excess_63 | -0.0051 | -0.15 | 0.5 | 0.391 | 0.09 | 78 |
| f:reversal_5 | 0.011 | 0.38 | 0.513 | -0.089 | -0.02 | 78 |
| f:trend_100 | -0.0035 | -0.1 | 0.462 | 0.533 | 0.12 | 78 |
| f:vol_20 | 0.0633 | 1.5 | 0.628 | 5.455 | 1.03 | 78 |
| f:mom_12_1 | 0.0028 | 0.08 | 0.526 | 1.052 | 0.26 | 78 |
| f:ep | 0.0252 | 0.91 | 0.538 | -1.308 | -0.38 | 78 |
| f:bp | 0.0155 | 0.42 | 0.526 | 0.854 | 0.23 | 78 |
| f:cp | 0.0365 | 0.96 | 0.551 | 0.526 | 0.12 | 78 |
| f:roe | 0.0014 | 0.07 | 0.449 | -1.737 | -0.69 | 78 |
| f:gpa | 0.0033 | 0.13 | 0.487 | -1.436 | -0.48 | 78 |
| f:lev | -0.0359 | -1.94 | 0.372 | -0.781 | -0.33 | 78 |
| f:acc | -0.0033 | -0.26 | 0.513 | 1.362 | 0.84 | 78 |

# Horizon: 120 sessions

Value as Value (in sector), quality as Quality (picked on the training years).

## Blends · train · 120 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 120 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | -0.0038 | -0.1 | 0.476 | -0.635 | -0.15 | 84 |
| seven groups, equal | -0.016 | -0.44 | 0.464 | -0.879 | -0.2 | 84 |
| seven groups, IC-weighted | 0.0347 | 0.96 | 0.583 | 1.807 | 0.39 | 84 |
| value + quality only | -0.0377 | -1.48 | 0.369 | -2.686 | -0.79 | 84 |

## Blends · test · 120 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 120 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| current V3 (price only) | -0.0032 | -0.07 | 0.573 | -0.654 | -0.07 | 75 |
| seven groups, equal | 0.0014 | 0.03 | 0.573 | -0.995 | -0.14 | 75 |
| seven groups, IC-weighted | -0.0102 | -0.25 | 0.507 | 0.41 | 0.05 | 75 |
| value + quality only | 0.0172 | 0.54 | 0.573 | -0.492 | -0.1 | 75 |

## Factors · train · 120 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 120 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | 0.0044 | 0.13 | 0.548 | 0.239 | 0.06 | 84 |
| Q Trend | 0.0111 | 0.32 | 0.56 | 0.865 | 0.21 | 84 |
| Q Low Risk | -0.0222 | -0.5 | 0.429 | -2.353 | -0.42 | 84 |
| Q Reversal | -0.0131 | -0.4 | 0.452 | -0.739 | -0.17 | 84 |
| Momentum 12-1 | 0.0037 | 0.08 | 0.476 | 0.569 | 0.11 | 84 |
| Value | -0.0862 | -1.83 | 0.274 | -5.262 | -0.76 | 84 |
| Quality | 0.0363 | 1.18 | 0.56 | 1.769 | 0.44 | 84 |
| Value (in sector) | -0.0723 | -1.86 | 0.31 | -4.075 | -0.76 | 84 |
| Quality (in sector) | 0.0214 | 0.76 | 0.571 | 0.884 | 0.24 | 84 |
| f:drawdown_63 | -0.005 | -0.13 | 0.488 | -1.296 | -0.28 | 84 |
| f:ema_diff | 0.0085 | 0.24 | 0.548 | 0.724 | 0.18 | 84 |
| f:excess_21 | 0.0009 | 0.02 | 0.5 | 0.349 | 0.08 | 84 |
| f:excess_63 | 0.0068 | 0.2 | 0.488 | 0.813 | 0.21 | 84 |
| f:reversal_5 | -0.0131 | -0.4 | 0.452 | -0.739 | -0.17 | 84 |
| f:trend_100 | 0.0139 | 0.4 | 0.548 | 1.089 | 0.27 | 84 |
| f:vol_20 | 0.0361 | 0.82 | 0.631 | 3.456 | 0.59 | 84 |
| f:mom_12_1 | 0.0037 | 0.08 | 0.476 | 0.569 | 0.11 | 84 |
| f:ep | -0.0639 | -1.64 | 0.286 | -4.655 | -0.83 | 84 |
| f:bp | -0.0862 | -2.17 | 0.274 | -4.346 | -0.78 | 84 |
| f:cp | -0.0572 | -1.29 | 0.357 | -3.734 | -0.6 | 84 |
| f:roe | 0.0039 | 0.18 | 0.464 | -1.279 | -0.45 | 84 |
| f:gpa | 0.0617 | 1.56 | 0.619 | 2.502 | 0.47 | 84 |
| f:lev | -0.0034 | -0.16 | 0.536 | 0.238 | 0.07 | 84 |
| f:acc | 0.0411 | 1.77 | 0.643 | 2.367 | 0.72 | 84 |

## Factors · test · 120 sessions

| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / 120 sessions | long-short Sharpe | months |
|---|---|---|---|---|---|---|
| Q Momentum | 0.0217 | 0.5 | 0.627 | 2.868 | 0.32 | 75 |
| Q Trend | 0.0213 | 0.46 | 0.6 | 2.685 | 0.28 | 75 |
| Q Low Risk | -0.0752 | -1.36 | 0.32 | -10.151 | -0.95 | 75 |
| Q Reversal | -0.007 | -0.17 | 0.52 | -1.353 | -0.14 | 75 |
| Momentum 12-1 | 0.0093 | 0.19 | 0.587 | 2.569 | 0.27 | 75 |
| Value | 0.0385 | 0.67 | 0.52 | -0.68 | -0.07 | 75 |
| Quality | -0.0305 | -0.81 | 0.307 | -1.731 | -0.32 | 75 |
| Value (in sector) | 0.0382 | 0.78 | 0.533 | 0.653 | 0.08 | 75 |
| Quality (in sector) | -0.0437 | -1.48 | 0.267 | -3.636 | -0.71 | 75 |
| f:drawdown_63 | -0.0308 | -0.65 | 0.48 | -4.82 | -0.52 | 75 |
| f:ema_diff | 0.0218 | 0.47 | 0.6 | 2.637 | 0.28 | 75 |
| f:excess_21 | 0.0143 | 0.34 | 0.64 | 1.91 | 0.22 | 75 |
| f:excess_63 | 0.0234 | 0.54 | 0.613 | 3.155 | 0.34 | 75 |
| f:reversal_5 | -0.007 | -0.17 | 0.52 | -1.353 | -0.14 | 75 |
| f:trend_100 | 0.0202 | 0.44 | 0.64 | 2.884 | 0.29 | 75 |
| f:vol_20 | 0.1017 | 1.78 | 0.773 | 13.065 | 1.19 | 75 |
| f:mom_12_1 | 0.0093 | 0.19 | 0.587 | 2.569 | 0.27 | 75 |
| f:ep | 0.0322 | 0.89 | 0.613 | -3.899 | -0.57 | 75 |
| f:bp | 0.0184 | 0.34 | 0.48 | 1.823 | 0.21 | 75 |
| f:cp | 0.0507 | 0.95 | 0.6 | -0.082 | -0.01 | 75 |
| f:roe | -0.0003 | -0.01 | 0.467 | -4.641 | -0.77 | 75 |
| f:gpa | -0.0028 | -0.08 | 0.467 | -3.535 | -0.53 | 75 |
| f:lev | -0.0494 | -1.74 | 0.347 | -1.125 | -0.2 | 75 |
| f:acc | -0.0027 | -0.14 | 0.453 | 3.204 | 0.91 | 75 |

## Coverage of the SEC facts (share of stock-months with a value)

| year | earnings yield | ROE |
|---|---|---|
| 2013 | 0.887 | 0.896 |
| 2014 | 0.898 | 0.899 |
| 2015 | 0.898 | 0.899 |
| 2016 | 0.905 | 0.897 |
| 2017 | 0.902 | 0.904 |
| 2018 | 0.901 | 0.907 |
| 2019 | 0.917 | 0.905 |
| 2020 | 0.929 | 0.918 |
| 2021 | 0.939 | 0.921 |
| 2022 | 0.956 | 0.913 |
| 2023 | 0.955 | 0.915 |
| 2024 | 0.961 | 0.925 |
| 2025 | 0.971 | 0.931 |
| 2026 | 0.975 | 0.934 |

Rows starting f: are single inputs as raw percentiles (higher value = higher score), so a negative IC there means lower is better (vol_20: lower volatility).

**Limits:** Today's S&P 500 members only (survivorship bias), no costs, monthly snapshots, Yahoo adjusted prices.
