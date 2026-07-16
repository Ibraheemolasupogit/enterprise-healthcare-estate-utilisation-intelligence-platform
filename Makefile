PYTHON ?= python3
PYTHONPATH ?= src

.PHONY: install lint format format-check typecheck test coverage validate-repository validate-config validate-sql validate-docs scan-secrets validate-structure generate-data generate-sample-data verify-synthetic-data test-synthetic-data initialise-database ingest-data link-entities build-curated-database verify-database export-ingestion-evidence run-data-quality verify-data-quality export-data-quality-evidence calculate-utilisation verify-utilisation export-utilisation-evidence run-forecasting verify-forecasting export-forecast-evidence run-scenarios verify-scenarios export-scenario-evidence run-optimisation verify-optimisation export-optimisation-evidence run-simulation verify-simulation export-simulation-evidence run-financial-analysis verify-financial-analysis export-financial-evidence dashboard dashboard-check dashboard-check-fast test-dashboard generate-communication-evidence verify-communication-evidence export-communication-evidence test-communication communication-check-fast run-assurance verify-assurance export-assurance-evidence assurance-check-fast assurance-fast assurance-full assurance-report release-evidence verify-release-evidence portfolio-check handover-check final-audit portfolio-package final-quality ci test-ingestion test-linking test-data-quality test-utilisation test-forecasting test-scenarios test-optimisation test-simulation test-financial quality clean

install:
	$(PYTHON) -m pip install -e ".[dev]" || $(PYTHON) -m pip install -e . -r requirements-dev.txt

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy src dashboard tests

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=estate_intelligence --cov-report=term-missing

validate-config:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli validate-config
	$(PYTHON) -m pytest --no-cov tests/contract/test_configuration_contracts.py

validate-repository:
	$(PYTHON) -m pytest --no-cov tests/unit/test_repository_structure.py tests/contract/test_assurance_contracts.py

validate-sql:
	$(PYTHON) -m pytest --no-cov tests/contract/test_database_contracts.py tests/unit/test_assurance_checks.py

validate-docs:
	$(PYTHON) -m pytest --no-cov tests/unit/test_documentation_checks.py

scan-secrets:
	$(PYTHON) -m pytest --no-cov tests/unit/test_security_scan.py

validate-structure:
	$(PYTHON) -m pytest --no-cov tests/unit/test_repository_structure.py

generate-data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli generate-data --output-dir data/raw --overwrite

generate-sample-data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli generate-data --sample --output-dir data/sample --overwrite

verify-synthetic-data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-synthetic-data --output-dir data/sample

test-synthetic-data:
	$(PYTHON) -m pytest tests/unit/test_synthetic_models.py tests/integration/test_synthetic_generation.py tests/contract/test_sample_data_contracts.py tests/end_to_end/test_generate_sample_data.py

initialise-database:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli initialise-database --database data/processed/estate_intelligence.db --rebuild

ingest-data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli ingest-data --input-dir data/sample --database data/processed/estate_intelligence.db --rebuild

link-entities:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli link-entities --input-dir data/sample --database data/processed/estate_intelligence.db --rebuild

build-curated-database:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli build-curated-database --input-dir data/sample --database data/processed/estate_intelligence.db --export-dir outputs/ingestion --rebuild

verify-database:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-database --database data/processed/estate_intelligence.db

export-ingestion-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-ingestion-evidence --database data/processed/estate_intelligence.db --export-dir outputs/ingestion

run-data-quality:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-data-quality --database data/processed/estate_intelligence.db --export-dir outputs/data_quality --rebuild

verify-data-quality:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-data-quality --database data/processed/estate_intelligence.db

export-data-quality-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-data-quality-evidence --database data/processed/estate_intelligence.db --export-dir outputs/data_quality

calculate-utilisation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli calculate-utilisation --database data/processed/estate_intelligence.db --output-dir outputs/utilisation --rebuild

verify-utilisation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-utilisation --database data/processed/estate_intelligence.db

export-utilisation-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-utilisation-evidence --database data/processed/estate_intelligence.db --output-dir outputs/utilisation

run-forecasting:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-forecasting --database data/processed/estate_intelligence.db --output-dir outputs/forecasting --rebuild

verify-forecasting:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-forecasting --database data/processed/estate_intelligence.db

export-forecast-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-forecast-evidence --database data/processed/estate_intelligence.db --output-dir outputs/forecasting

run-scenarios:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-scenarios --database data/processed/estate_intelligence.db --output-dir outputs/scenarios --rebuild

verify-scenarios:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-scenarios --database data/processed/estate_intelligence.db

export-scenario-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-scenario-evidence --database data/processed/estate_intelligence.db --output-dir outputs/scenarios

run-optimisation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-optimisation --database data/processed/estate_intelligence.db --output-dir outputs/optimisation --rebuild

verify-optimisation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-optimisation --database data/processed/estate_intelligence.db

export-optimisation-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-optimisation-evidence --database data/processed/estate_intelligence.db --output-dir outputs/optimisation

run-simulation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-simulation --database data/processed/estate_intelligence.db --output-dir outputs/simulation --rebuild

verify-simulation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-simulation --database data/processed/estate_intelligence.db

export-simulation-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-simulation-evidence --database data/processed/estate_intelligence.db --output-dir outputs/simulation

run-financial-analysis:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli run-financial-analysis --database data/processed/estate_intelligence.db --output-dir outputs/financial --rebuild

verify-financial-analysis:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli verify-financial-analysis --database data/processed/estate_intelligence.db

export-financial-evidence:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m estate_intelligence.cli export-financial-evidence --database data/processed/estate_intelligence.db --output-dir outputs/financial

dashboard:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m streamlit run dashboard/streamlit_app.py --server.headless true --server.address 127.0.0.1

dashboard-check:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli dashboard-check --database data/processed/estate_intelligence.db

dashboard-check-fast:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m pytest --no-cov tests/unit/test_dashboard_formatting.py tests/unit/test_dashboard_queries.py tests/unit/test_dashboard_services.py tests/unit/test_dashboard_filters.py tests/unit/test_dashboard_alerts.py tests/unit/test_makefile_dashboard_fast.py tests/integration/test_dashboard_data_access.py tests/integration/test_dashboard_pages.py tests/contract/test_dashboard_contracts.py

test-dashboard:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m pytest --no-cov tests/unit/test_dashboard_formatting.py tests/unit/test_dashboard_queries.py tests/unit/test_dashboard_services.py tests/unit/test_dashboard_filters.py tests/unit/test_dashboard_alerts.py tests/integration/test_dashboard_data_access.py tests/integration/test_dashboard_pages.py tests/contract/test_dashboard_contracts.py tests/end_to_end/test_dashboard_smoke.py

generate-communication-evidence:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli generate-communication-evidence --database data/processed/estate_intelligence.db --config config/communication.yaml --output-dir outputs/communication --rebuild

verify-communication-evidence:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli verify-communication-evidence --database data/processed/estate_intelligence.db --output-dir outputs/communication

export-communication-evidence:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli export-communication-evidence --database data/processed/estate_intelligence.db --output-dir outputs/communication

test-communication:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m pytest --no-cov tests/unit/test_communication_models.py tests/unit/test_audience_rendering.py tests/unit/test_option_catalogue.py tests/unit/test_challenge_response.py tests/unit/test_revision_logic.py tests/unit/test_decision_record.py tests/unit/test_claim_mapping.py tests/unit/test_language_controls.py tests/integration/test_communication_pipeline.py tests/integration/test_communication_evidence_database.py tests/contract/test_communication_contracts.py tests/end_to_end/test_generate_communication_evidence.py

communication-check-fast:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m pytest --no-cov tests/unit/test_communication_models.py tests/unit/test_audience_rendering.py tests/unit/test_challenge_response.py tests/unit/test_revision_logic.py tests/unit/test_decision_record.py tests/unit/test_language_controls.py tests/contract/test_communication_contracts.py

run-assurance:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli run-assurance --database data/processed/estate_intelligence.db --config config/assurance.yaml --output-dir outputs/assurance --profile canonical --rebuild

verify-assurance:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli verify-assurance --database data/processed/estate_intelligence.db --output-dir outputs/assurance

export-assurance-evidence:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli export-assurance-evidence --database data/processed/estate_intelligence.db --output-dir outputs/assurance

assurance-check-fast:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m pytest --no-cov tests/unit/test_assurance_catalogue.py tests/unit/test_assurance_models.py tests/unit/test_assurance_checks.py tests/unit/test_release_gates.py tests/unit/test_reproducibility_assurance.py tests/unit/test_security_scan.py tests/contract/test_assurance_contracts.py

assurance-fast: lint format-check typecheck validate-repository validate-config validate-sql validate-docs scan-secrets dashboard-check-fast communication-check-fast assurance-check-fast

assurance-full: generate-sample-data verify-synthetic-data build-curated-database verify-database export-ingestion-evidence run-data-quality verify-data-quality export-data-quality-evidence calculate-utilisation verify-utilisation export-utilisation-evidence run-forecasting verify-forecasting export-forecast-evidence run-scenarios verify-scenarios export-scenario-evidence run-optimisation verify-optimisation export-optimisation-evidence run-simulation verify-simulation export-simulation-evidence run-financial-analysis verify-financial-analysis export-financial-evidence dashboard-check generate-communication-evidence verify-communication-evidence export-communication-evidence run-assurance verify-assurance

assurance-report: verify-assurance
	@printf '%s\n' outputs/assurance/assurance_report.md

release-evidence: run-assurance export-assurance-evidence

verify-release-evidence: verify-assurance

portfolio-check:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli portfolio-check --config config/portfolio.yaml

handover-check:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli handover-check --config config/portfolio.yaml

final-audit:
	PYTHONPATH=$(PYTHONPATH):. $(PYTHON) -m estate_intelligence.cli final-audit --config config/portfolio.yaml

portfolio-package: portfolio-check handover-check final-audit
	@printf '%s\n' portfolio/manifests/portfolio_manifest.json

final-quality: quality assurance-full assurance-report release-evidence verify-release-evidence dashboard-check portfolio-check handover-check final-audit portfolio-package
	git diff --check

ci: assurance-fast test

test-ingestion:
	$(PYTHON) -m pytest tests/unit/test_database.py tests/integration/test_ingestion_pipeline.py tests/contract/test_database_contracts.py

test-linking:
	$(PYTHON) -m pytest tests/unit/test_normalisation.py tests/unit/test_duplicate_detector.py tests/unit/test_linkage_quality.py tests/integration/test_entity_linking_pipeline.py

test-data-quality:
	$(PYTHON) -m pytest tests/unit/test_quality_models.py tests/unit/test_quality_rules.py tests/unit/test_quality_scoring.py tests/unit/test_completeness_checks.py tests/unit/test_validity_checks.py tests/unit/test_consistency_checks.py tests/unit/test_uniqueness_checks.py tests/unit/test_timeliness_checks.py tests/unit/test_reconciliation.py tests/integration/test_data_quality_pipeline.py tests/integration/test_quality_evidence_database.py tests/contract/test_data_quality_contracts.py tests/end_to_end/test_run_data_quality.py

test-utilisation:
	$(PYTHON) -m pytest tests/unit/test_availability_metrics.py tests/unit/test_booking_utilisation.py tests/unit/test_activity_metrics.py tests/unit/test_effective_utilisation.py tests/unit/test_time_bands.py tests/unit/test_workforce_metrics.py tests/unit/test_unit_cost_metrics.py tests/unit/test_underutilisation.py tests/unit/test_utilisation_models.py tests/integration/test_utilisation_pipeline.py tests/integration/test_utilisation_evidence_database.py tests/contract/test_utilisation_contracts.py tests/end_to_end/test_calculate_utilisation.py

test-forecasting:
	$(PYTHON) -m pytest tests/unit/test_forecast_series.py tests/unit/test_forecast_eligibility.py tests/unit/test_forecast_baselines.py tests/unit/test_forecast_backtesting.py tests/unit/test_forecast_evaluation.py tests/unit/test_forecast_selection.py tests/unit/test_forecast_intervals.py tests/unit/test_exponential_smoothing.py tests/integration/test_forecasting_pipeline.py tests/integration/test_forecasting_evidence_database.py tests/contract/test_forecasting_contracts.py tests/end_to_end/test_run_forecasting.py

test-scenarios:
	$(PYTHON) -m pytest tests/unit/test_scenario_models.py tests/unit/test_scenario_constraints.py tests/unit/test_scenario_capacity.py tests/unit/test_baseline_scenario.py tests/unit/test_light_consolidation.py tests/unit/test_site_consolidation.py tests/unit/test_hybrid_redesign.py tests/unit/test_scenario_scoring.py tests/unit/test_scenario_uncertainty.py tests/integration/test_scenario_pipeline.py tests/integration/test_scenario_evidence_database.py tests/contract/test_scenario_contracts.py tests/end_to_end/test_run_scenarios.py

test-optimisation:
	$(PYTHON) -m pytest tests/unit/test_optimisation_models.py tests/unit/test_optimisation_candidates.py tests/unit/test_optimisation_variables.py tests/unit/test_optimisation_constraints.py tests/unit/test_optimisation_objective.py tests/unit/test_optimisation_solver.py tests/unit/test_optimisation_diagnostics.py tests/integration/test_optimisation_pipeline.py tests/integration/test_optimisation_evidence_database.py tests/contract/test_optimisation_contracts.py tests/end_to_end/test_run_optimisation.py

test-simulation:
	$(PYTHON) -m pytest --no-cov tests/unit/test_simulation_models.py tests/unit/test_simulation_seeds.py tests/unit/test_simulation_arrivals.py tests/unit/test_simulation_service_times.py tests/unit/test_simulation_resources.py tests/unit/test_simulation_events.py tests/unit/test_simulation_metrics.py tests/unit/test_simulation_thresholds.py tests/unit/test_simulation_confidence_intervals.py tests/integration/test_simulation_pipeline.py tests/integration/test_simulation_evidence_database.py tests/contract/test_simulation_contracts.py tests/end_to_end/test_run_simulation.py

test-financial:
	$(PYTHON) -m pytest --no-cov tests/unit/test_financial_models.py tests/unit/test_financial_costs.py tests/unit/test_financial_cashflows.py tests/unit/test_financial_payback.py tests/unit/test_financial_npv.py tests/unit/test_financial_sensitivity.py tests/unit/test_financial_risk_adjustment.py tests/unit/test_financial_break_even.py tests/integration/test_financial_pipeline.py tests/integration/test_financial_evidence_database.py tests/contract/test_financial_contracts.py tests/end_to_end/test_run_financial_analysis.py

quality: lint format-check typecheck test validate-config validate-structure verify-synthetic-data dashboard-check test-dashboard verify-communication-evidence test-communication verify-assurance
	git diff --check

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist htmlcov *.egg-info data/processed/estate_intelligence.db data/processed/estate_intelligence.db-wal data/processed/estate_intelligence.db-shm outputs/ingestion
