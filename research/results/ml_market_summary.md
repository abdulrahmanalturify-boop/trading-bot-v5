# AI bots, round 3 · the market model

Trained on 2012-01-03..2019-12-31; tested from 2020-01-02 (never seen). Calls the 0% least promising days risky (chosen on 2017-2019). AUC 2017-2019 0.54, 2020-now 0.43 (0.5 = a coin flip).

Choice on 2017-2019: 0% risky -> Sharpe 1.37, 10% risky -> Sharpe 1.30, 20% risky -> Sharpe 1.22, 30% risky -> Sharpe 1.43

The stocks 2020-now, held always: 0.87 (+17%, -38%); held only on the days the model allows: 0.87 (+17%, -38%) (risky days 0%).

| Bot | 2020-now as it is | 2020-now with the model | 2012-2019 as it is | 2012-2019 with the model (trained here) |
|---|---|---|---|---|
| ai_sma | 1.18 (+35%, -33%) | 1.18 (+35%, -33%) | 1.00 (+14%, -21%) | 1.00 (+14%, -21%) |
| ai_donchian | 1.18 (+31%, -25%) | 1.18 (+31%, -25%) | 1.17 (+18%, -14%) | 1.17 (+18%, -14%) |
| ai_volume | 1.25 (+29%, -23%) | 1.25 (+29%, -23%) | 1.19 (+15%, -14%) | 1.19 (+15%, -14%) |
| ai_vwma | 1.03 (+22%, -24%) | 1.03 (+22%, -24%) | 0.83 (+11%, -15%) | 0.83 (+11%, -15%) |
| ai_setups | 0.91 (+12%, -20%) | 0.91 (+12%, -20%) | 1.06 (+11%, -14%) | 1.06 (+11%, -14%) |
