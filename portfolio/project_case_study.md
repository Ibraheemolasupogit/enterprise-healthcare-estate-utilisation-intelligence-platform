# Project Case Study

## Problem

Healthcare estates teams need to understand how rooms, services, demand, workforce, resilience, and cost interact before any site or room consolidation concept can be discussed responsibly. This synthetic project models that decision environment without using real patient, staff, or estate data.

## Approach

The repository builds a deterministic evidence chain. Synthetic CSV sources are loaded into SQLite, linked into curated entities, checked for quality issues, and transformed into utilisation, forecasting, scenario, optimisation, simulation, financial, communication, and assurance outputs.

## Outcome

The final evidence position is conditional. Analytical components run and are reproducible, but simulation evidence shows resilience concerns. The communication layer therefore keeps the decision at `awaiting_governance_decision`, records approval as `not_approved`, and frames financial values as planning evidence rather than realised benefit.

## What This Demonstrates

The project demonstrates data engineering, analytics engineering, reproducibility controls, stakeholder communication, and governance-aware delivery. It also demonstrates restraint: the synthetic evidence is sufficient for portfolio demonstration and method review, not for real estate action.
