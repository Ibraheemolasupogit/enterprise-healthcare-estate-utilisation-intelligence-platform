# Time Series Validation

Milestone 6 uses expanding-window chronological validation. The default monthly design uses 15 initial training
periods, a 3-month validation horizon and a 3-month rolling step, which creates conservative folds for the 24-month
synthetic history.

Training windows always end before validation windows begin. The same folds are reused across candidate models for a
series. Models that cannot be fitted within a fold's available training history are marked ineligible or failed rather
than being forced.

After model selection, the selected model is fitted to all historical observations and forecasts the configured future
horizon. Future actuals are not fabricated.
