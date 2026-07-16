# Optimisation Objective

The objective minimises configured synthetic components:

- retained recurring estate cost;
- room activation cost;
- service relocation cost;
- synthetic travel penalty;
- operational disruption penalty;
- under-utilisation penalty;
- unmet-demand penalty;
- workforce warning penalty;
- accessibility warning penalty;
- deterministic tie-breaker.

Coefficients are configured in `config/optimisation.yaml`. Components are not audited costs or guaranteed savings.
The unmet-demand penalty is intentionally dominant so demand is not left unmet for discretionary cost reasons. The
canonical configuration permits unmet demand as a diagnostic slack variable; controlled validation can disable that
slack to prove infeasibility handling.

Objective components are exported separately for auditability. Transition, exit, relocation and disruption exposure are
not treated as recurring savings.
## Milestone 10 Handoff

Optimisation objective values are not financial recommendations. Milestone 10 uses building-status evidence to test financial-release conditions and then adds transition, mitigation and risk-adjustment evidence.
