# Forecasting Methodology

Milestone 6 implements deterministic monthly demand forecasting over synthetic curated activity, workforce and
Milestone 5 utilisation evidence. It forecasts demand only; it does not create consolidation scenarios, optimise room
allocation or recommend estate changes.

## Targets

The framework forecasts estate-wide scheduled contacts, completed contacts, face-to-face contacts, remote contacts,
face-to-face room-hour demand and total room-hour demand. It also forecasts service-level scheduled contacts,
completed contacts, face-to-face contacts, face-to-face room-hours, available FTE and session capacity.

## Aggregation

Clinical activity is aggregated once at monthly grain from quality-gated curated activity records. Service identifiers
are retained for service-level series. Room-hour demand is derived as `face_to_face_contacts * average duration / 60`.
Workforce series are aligned to their native monthly records.

## Model Catalogue

The configured catalogue is deliberately small: naive, seasonal naive, moving average, drift, simple exponential
smoothing, Holt trend and additive Holt-Winters. These are pure-Python deterministic implementations with fixed
parameters from configuration; no external forecasting API is used.

## Determinism

Run identity is derived from source run IDs, the framework version, forecast config checksum, model catalogue checksum
and series catalogue checksum. No runtime timestamp is used.

## Boundaries

Forecast outputs are demand estimates with uncertainty intervals. Milestone 7 consumes those forecasts as scenario
planning demand, but forecasts remain separate from estate closure, relocation, consolidation, savings or payback
recommendations.
