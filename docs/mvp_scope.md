# MVP Scope

Milestone 11 adds a local read-only Streamlit dashboard over existing synthetic evidence. It is included in the MVP as a demonstration and review surface only. It excludes final recommendations, stakeholder communication evidence, authentication, Power BI artefacts, cloud deployment and real patient or organisation data.

Milestone 12 adds synthetic stakeholder communication and governance evidence to the MVP. It remains non-approving and excludes email sending, workflow automation, cloud deployment and release assurance.

Milestone 13 adds local automated assurance and release evidence. It excludes deployment, publishing and final portfolio packaging.

The MVP uses deterministic synthetic buildings, rooms, services, bookings, clinical activity, workforce, finance and
accessibility source datasets as its input boundary. The local SQLite ingestion/linking layer now creates source,
staging, curated and evidence tables. The data-quality layer now creates rule, issue, score, reconciliation and
manual-review evidence over those synthetic inputs. The utilisation layer now creates descriptive metrics over a
quality-gated analytical population. The forecasting layer now creates monthly demand forecasts with time-aware
validation. The scenario layer now creates deterministic option-appraisal evidence over a fixed catalogue. The
optimisation layer now creates constrained mathematical allocation candidates. Later milestones will demonstrate
operational simulation now tests those allocations under synthetic stress. Later milestones will demonstrate
finance/risk analysis and stakeholder-ready reporting on synthetic evidence only.

Exclusions include real patient data, real organisational data, live system integration, production deployment, clinical
decision support, NPV/payback analysis and approved estate recommendations.

Success criteria include reproducible synthetic inputs, traceable assumptions, tested calculations, clear limitations,
audience-specific outputs and transparent decision criteria.
## Milestone 10 Scope

The MVP now includes synthetic financial and sensitivity analysis evidence for planning comparison. Dashboards, implementation approval, live finance data and final recommendations remain out of scope.
