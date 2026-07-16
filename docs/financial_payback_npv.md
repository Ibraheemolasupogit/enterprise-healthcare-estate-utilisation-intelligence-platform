# Financial Payback and NPV

Simple payback is the first analysis year where cumulative net financial effect becomes non-negative. Discounted payback uses discounted annual cash flows. If payback is not reached in the configured horizon, the result is recorded as `not_reached`.

NPV is calculated as the sum of annual cash flows discounted by the configured end-of-year discount convention. Positive NPV is financial evidence only and does not imply approval, delivery confidence or implementation recommendation.

The implementation supports positive, negative and zero NPV cases and keeps transition costs explicit in year 1 cash flows.
