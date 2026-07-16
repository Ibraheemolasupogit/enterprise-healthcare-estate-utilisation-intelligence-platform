# Forecast Model Selection

The primary selection metric is WAPE where defined. Secondary metrics include MAE, RMSE, bias, signed percentage bias,
sMAPE and MASE where the denominator is valid.

Selection is deterministic. The lowest primary metric wins; if models are within tolerance, the simpler model is
preferred. The naive model is the primary baseline and is allowed to win.

Model failures and model ineligibility are recorded separately. A model is not selected merely because another model
failed; the selected model must have evaluated evidence.
