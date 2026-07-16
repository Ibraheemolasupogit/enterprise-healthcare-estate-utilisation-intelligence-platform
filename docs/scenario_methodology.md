# Scenario Methodology

Milestone 7 compares four deterministic scenario operating models using curated data, data-quality evidence,
utilisation evidence and forecast demand. It is a scenario-analysis framework, not an optimisation engine or decision
recommendation tool.

The engine uses stable heuristic rules: candidate rooms are ranked by utilisation and identifiers, protected capacity
is retained, forecast upper-interval demand is preserved, and constraint failures are written as evidence rather than
forced into a feasible result.

The default planning basis is six months of forecast face-to-face room-hour demand using the upper 80% interval. Point
forecast demand and selected interval demand are both retained.

Scenario outputs separate capacity, workforce, accessibility, descriptive recurring cost, risks and comparison scores.
They do not approve closures, relocations, savings or implementation.

Milestone 8 consumes scenario compatibility, risk and planning-demand evidence but does not overwrite scenario outputs
or convert scenario scores into recommendations.

Milestone 9 consumes the light-consolidation scenario as one operational simulation case without changing scenario
evidence or treating heuristic scores as recommendations.
