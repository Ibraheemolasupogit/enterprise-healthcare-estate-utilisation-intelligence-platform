# Forecast Uncertainty

Forecast intervals use deterministic empirical absolute residual widths from validation errors. Configured interval
levels are 80% and 95%.

Demand lower bounds are clipped at zero. Interval coverage is measured in backtesting where validation actuals exist.
Intervals should be read as conservative synthetic uncertainty ranges, not as clinically validated probabilistic
guarantees.
