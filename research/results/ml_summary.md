# AI bots · with and without the model

Trained on signals of 2012-01-03..2019-12-31; tested from 2020-01-02 (never seen).

Pooled model: 224949 signals of 15 strategies; AUC 2017-2019 0.525 (model of 2012-2016), AUC 2020-now 0.544 on 199202 signals (0.5 = a coin flip).

| Bot | Keeps | Test AUC | Test win % kept / dropped | Test avg trade kept / dropped | Bot 2020-now plain: Sharpe (CAGR, max DD) | Bot 2020-now AI |
|---|---|---|---|---|---|---|
| ai_sma | 100% | 0.53 | 39% / — | 3.41% / —% | 1.19 (+35%, -33%) | 1.19 (+35%, -33%) |
| ai_donchian | 100% | 0.51 | 41% / — | 1.21% / —% | 1.17 (+30%, -26%) | 1.17 (+30%, -26%) |
| ai_volume | 80% | 0.51 | 41% / 41% | 1.37% / 1.45% | 1.27 (+29%, -24%) | 1.14 (+22%, -21%) |
| ai_vwma | 100% | 0.53 | 31% / — | 0.39% / —% | 1.03 (+22%, -24%) | 1.03 (+22%, -24%) |
| ai_setups | 80% | 0.53 | 41% / 39% | 0.54% / 0.41% | 0.94 (+13%, -20%) | 0.90 (+10%, -18%) |

In-sample (2012-2019, the model was trained here, so the AI numbers are optimistic):

| Bot | plain | AI |
|---|---|---|
| ai_sma | 1.00 (+14%, -21%) | 1.00 (+14%, -21%) |
| ai_donchian | 1.14 (+17%, -15%) | 1.14 (+17%, -15%) |
| ai_volume | 1.20 (+15%, -14%) | 1.45 (+19%, -14%) |
| ai_vwma | 0.83 (+11%, -15%) | 0.83 (+11%, -15%) |
| ai_setups | 1.06 (+11%, -14%) | 1.41 (+14%, -11%) |
