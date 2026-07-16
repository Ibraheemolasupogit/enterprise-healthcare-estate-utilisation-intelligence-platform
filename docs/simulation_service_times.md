# Simulation Service Times

Service durations are calibrated from synthetic clinical activity average face-to-face room minutes by service, with
configured triangular distributions and caps. Service room-type overrides support diagnostic, treatment and meeting
style services.

Duration shocks multiply sampled durations for stress experiments. Durations are strictly positive and capped to avoid
pathological synthetic events. These parameters are operational assumptions, not clinical validation.
