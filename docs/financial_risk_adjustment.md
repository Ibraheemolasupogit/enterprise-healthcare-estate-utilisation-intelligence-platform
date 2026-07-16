# Financial Risk Adjustment

Financial risk adjustment is transparent and rule-based. It considers data confidence, case evidence, cost-assumption completeness and, most importantly for Milestone 10, simulation resilience.

Where linked simulation cases fail configured operational thresholds, nominal financial calculations are retained for analytical comparison but risk-adjusted realisability is capped. These cases are marked `not_realisable_without_mitigation` and require operational remediation before financial value could be treated as potentially realisable.

The risk adjustment does not hide failed thresholds and does not convert nominal cost reductions into guaranteed savings.
