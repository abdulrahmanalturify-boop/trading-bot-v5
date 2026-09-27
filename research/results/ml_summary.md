# AI bots · with and without the model

Trained on signals of 2012-01-03..2019-12-31; tested from 2020-01-02 (never seen).

| Bot | Keeps | Test AUC | Test win % kept / dropped | Test avg trade kept / dropped | Bot 2020-now plain: Sharpe (CAGR, max DD) | Bot 2020-now AI |
|---|---|---|---|---|---|---|
| ai_sma | 100% | 0.54 | 39% / — | 3.41% / —% | 1.19 (+35%, -33%) | 1.29 (+26%, -22%) |
| ai_donchian | 100% | 0.52 | 41% / — | 1.21% / —% | 1.17 (+30%, -26%) | 0.71 (+11%, -18%) |
| ai_volume | 100% | 0.51 | 41% / — | 1.40% / —% | 1.27 (+29%, -24%) | 1.05 (+20%, -21%) |
| ai_vwma | 100% | 0.54 | 31% / — | 0.39% / —% | 1.03 (+22%, -24%) | 0.65 (+10%, -32%) |
| ai_setups | 100% | 0.54 | 40% / — | 0.48% / —% | 0.94 (+13%, -20%) | 1.14 (+15%, -20%) |

In-sample (2012-2019, the model was trained here, so the AI numbers are optimistic):

| Bot | plain | AI |
|---|---|---|
| ai_sma | 1.00 (+14%, -21%) | 1.27 (+18%, -16%) |
| ai_donchian | 1.14 (+17%, -15%) | 1.72 (+20%, -11%) |
| ai_volume | 1.20 (+15%, -14%) | 1.59 (+19%, -14%) |
| ai_vwma | 0.83 (+11%, -15%) | 1.85 (+25%, -9%) |
| ai_setups | 1.06 (+11%, -14%) | 1.72 (+19%, -11%) |
