"""Typer command line interface for foundation checks."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from estate_intelligence import __version__
from estate_intelligence.financial.engine import (
    export_existing_financial_evidence as export_financial_evidence_service,
)
from estate_intelligence.financial.engine import (
    run_financial_analysis as run_financial_analysis_service,
)
from estate_intelligence.financial.engine import (
    verify_financial_analysis as verify_financial_analysis_service,
)
from estate_intelligence.forecasting.engine import (
    export_existing_forecast_evidence as export_forecast_evidence_service,
)
from estate_intelligence.forecasting.engine import (
    run_forecasting as run_forecasting_service,
)
from estate_intelligence.forecasting.engine import (
    verify_forecasting as verify_forecasting_service,
)
from estate_intelligence.ingestion.database import load_database_path
from estate_intelligence.ingestion.loader import (
    build_curated_database as build_curated_database_service,
)
from estate_intelligence.ingestion.loader import (
    export_database_evidence,
)
from estate_intelligence.ingestion.loader import (
    verify_database as verify_database_service,
)
from estate_intelligence.metrics.engine import (
    calculate_utilisation as calculate_utilisation_service,
)
from estate_intelligence.metrics.engine import (
    export_existing_utilisation_evidence as export_utilisation_evidence_service,
)
from estate_intelligence.metrics.engine import (
    verify_utilisation as verify_utilisation_service,
)
from estate_intelligence.optimisation.engine import (
    export_existing_optimisation_evidence as export_optimisation_evidence_service,
)
from estate_intelligence.optimisation.engine import (
    run_optimisation as run_optimisation_service,
)
from estate_intelligence.optimisation.engine import (
    verify_optimisation as verify_optimisation_service,
)
from estate_intelligence.scenarios.engine import (
    export_existing_scenario_evidence as export_scenario_evidence_service,
)
from estate_intelligence.scenarios.engine import run_scenarios as run_scenarios_service
from estate_intelligence.scenarios.engine import verify_scenarios as verify_scenarios_service
from estate_intelligence.settings import load_settings
from estate_intelligence.simulation.engine import (
    export_existing_simulation_evidence as export_simulation_evidence_service,
)
from estate_intelligence.simulation.engine import run_simulation as run_simulation_service
from estate_intelligence.simulation.engine import verify_simulation as verify_simulation_service
from estate_intelligence.synthetic_data.generator import (
    SyntheticDataConfig,
    verify_output,
    write_datasets,
)
from estate_intelligence.validation.engine import (
    export_data_quality_evidence as export_data_quality_evidence_service,
)
from estate_intelligence.validation.engine import (
    run_data_quality as run_data_quality_service,
)
from estate_intelligence.validation.engine import (
    verify_data_quality as verify_data_quality_service,
)

app = typer.Typer(
    name="estate-intelligence",
    help="Foundation commands for the estate intelligence repository.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the package version."""

    typer.echo(__version__)


@app.command()
def info() -> None:
    """Display non-sensitive package and environment information."""

    try:
        settings = load_settings()
    except ValidationError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    payload: dict[str, object] = {"package_version": __version__, **settings.public_summary()}
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("dashboard-info")
def dashboard_info(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Display read-only dashboard evidence lineage without starting Streamlit."""

    try:
        from dashboard.data.services import DashboardService

        database_path = database or load_database_path()
        summary = DashboardService(database_path).validate()
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        typer.echo(f"Dashboard info failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "database": summary.database,
                "ok": summary.ok,
                "run_lineage": summary.run_lineage,
                "warnings": summary.warnings,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("dashboard-check")
def dashboard_check(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Validate read-only dashboard imports, evidence tables and no-write access."""

    try:
        from dashboard.data.services import DashboardService

        database_path = database or load_database_path()
        service = DashboardService(database_path)
        summary = service.validate()
        read_only = service.assert_read_only()
        executive = service.get_executive_summary()
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        typer.echo(f"Dashboard check failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if not summary.ok:
        typer.echo(
            f"Dashboard check failed: missing evidence {list(summary.missing_tables)}",
            err=True,
        )
        raise typer.Exit(code=2)
    if not read_only:
        typer.echo("Dashboard check failed: read-only write probe was not blocked.", err=True)
        raise typer.Exit(code=2)

    typer.echo("Dashboard check passed.")
    typer.echo(f"database: {summary.database}")
    typer.echo(f"runs: {json.dumps(summary.run_lineage, sort_keys=True)}")
    typer.echo(f"simulation_readiness: {executive['simulation_readiness']}")
    typer.echo(f"financial_readiness: {executive['financial_readiness']}")


@app.command("validate-config")
def validate_config() -> None:
    """Validate foundation runtime settings without running analytics."""

    try:
        settings = load_settings()
    except ValidationError as exc:
        typer.echo(f"Configuration invalid: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        f"Configuration valid for {settings.environment} "
        f"({settings.project_name}, log level {settings.log_level})."
    )


@app.command("generate-data")
def generate_data(
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Synthetic data YAML config."),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Output directory."),
    ] = None,
    seed: Annotated[int | None, typer.Option("--seed", help="Override master seed.")] = None,
    sample: Annotated[
        bool,
        typer.Option("--sample/--runtime", help="Generate the small sample profile."),
    ] = True,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Overwrite existing generated files."),
    ] = False,
) -> None:
    """Generate deterministic synthetic source CSV and metadata files."""

    try:
        base_config = SyntheticDataConfig.from_yaml(config)
        generator_config = base_config.with_overrides(
            seed=seed,
            output_dir=output_dir,
            sample=sample,
        )
        target_dir = (
            generator_config.sample_output_dir if sample else generator_config.runtime_output_dir
        )
        metadata = write_datasets(generator_config, target_dir, overwrite=overwrite)
    except (FileExistsError, ValueError, OSError) as exc:
        typer.echo(f"Synthetic data generation failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Synthetic data written to {target_dir}")
    for dataset_name, count in metadata["record_counts"].items():
        typer.echo(f"{dataset_name}: {count}")


@app.command("verify-synthetic-data")
def verify_synthetic_data(
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Generated data directory."),
    ] = Path("data/sample"),
) -> None:
    """Verify generated synthetic source data files and checksums."""

    try:
        metadata = verify_output(output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Synthetic data verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Synthetic data verification passed "
        f"({sum(metadata['record_counts'].values())} records, "
        f"{metadata['intentional_quality_issue_count']} intentional issues)."
    )


@app.command("initialise-database")
def initialise_database(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild an existing database.")
    ] = False,
) -> None:
    """Initialise the local SQLite database by building the curated sample database."""

    build_curated_database(database=database, rebuild=rebuild)


@app.command("build-curated-database")
def build_curated_database(
    input_dir: Annotated[
        Path,
        typer.Option("--input-dir", help="Synthetic source data directory."),
    ] = Path("data/sample"),
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    export_dir: Annotated[
        Path | None,
        typer.Option("--export-dir", help="Evidence export directory."),
    ] = None,
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild an existing database.")
    ] = False,
) -> None:
    """Build source, staging, curated and evidence layers from synthetic data."""

    try:
        database_path = database or load_database_path()
        summary = build_curated_database_service(
            input_dir=input_dir,
            database_path=database_path,
            export_dir=export_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Curated database build failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Curated database built: {summary['database']}")
    typer.echo(f"ingestion_run_id: {summary['ingestion_run_id']}")
    for dataset, count in summary["source_rows"].items():
        typer.echo(f"{dataset}: {count}")


@app.command("verify-database")
def verify_database(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify a built local SQLite database."""

    try:
        database_path = database or load_database_path()
        summary = verify_database_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Database verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Database verification passed "
        f"({summary['tables']} tables, {summary['views']} views, "
        f"{summary['detected_issues']} intentional issues detected)."
    )


@app.command("export-ingestion-evidence")
def export_ingestion_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    export_dir: Annotated[
        Path,
        typer.Option("--export-dir", help="Evidence export directory."),
    ] = Path("outputs/ingestion"),
) -> None:
    """Export deterministic ingestion and linkage evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_database_evidence(database_path, export_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Evidence exported to {export_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-data-quality")
def run_data_quality(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Data-quality YAML config."),
    ] = Path("config/data_quality.yaml"),
    export_dir: Annotated[
        Path | None,
        typer.Option("--export-dir", help="Quality evidence export directory."),
    ] = Path("outputs/data_quality"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing quality evidence.")
    ] = False,
) -> None:
    """Run deterministic data-quality and reconciliation checks."""

    try:
        database_path = database or load_database_path()
        summary = run_data_quality_service(
            database_path=database_path,
            config_path=config,
            output_dir=export_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Data-quality run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Data-quality run complete: {summary['quality_run_id']}")
    typer.echo(f"overall_status: {summary['overall_status']}")
    typer.echo(f"overall_score: {summary['overall_score']}")
    typer.echo(f"record_issues: {summary['issue_count']}")
    typer.echo(f"manual_review_items: {summary['manual_review_count']}")


@app.command("verify-data-quality")
def verify_data_quality(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted data-quality evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_data_quality_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Data-quality verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Data-quality verification passed "
        f"({summary['overall_status']}, score {summary['overall_score']}, "
        f"{summary['issue_count']} record issues)."
    )


@app.command("export-data-quality-evidence")
def export_data_quality_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    export_dir: Annotated[
        Path,
        typer.Option("--export-dir", help="Quality evidence export directory."),
    ] = Path("outputs/data_quality"),
) -> None:
    """Export deterministic data-quality evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_data_quality_evidence_service(database_path, export_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Data-quality evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Data-quality evidence exported to {export_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("calculate-utilisation")
def calculate_utilisation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Utilisation YAML config."),
    ] = Path("config/utilisation.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Utilisation evidence export directory."),
    ] = Path("outputs/utilisation"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing utilisation evidence.")
    ] = False,
) -> None:
    """Calculate deterministic estate-utilisation analytics."""

    try:
        database_path = database or load_database_path()
        summary = calculate_utilisation_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Utilisation calculation failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    metrics = summary["summary"]
    typer.echo(f"Utilisation calculation complete: {summary['utilisation_run_id']}")
    typer.echo(f"available_hours: {metrics['available_hours']}")
    typer.echo(f"booked_utilisation: {metrics['booked_utilisation']}")
    typer.echo(f"actual_utilisation: {metrics['actual_utilisation']}")
    typer.echo(f"effective_utilisation: {metrics['effective_utilisation']}")


@app.command("verify-utilisation")
def verify_utilisation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted utilisation evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_utilisation_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Utilisation verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Utilisation verification passed "
        f"({summary['readiness_status']}, "
        f"{summary['room_count']} rooms, {summary['exclusion_count']} exclusions)."
    )


@app.command("export-utilisation-evidence")
def export_utilisation_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Utilisation evidence export directory."),
    ] = Path("outputs/utilisation"),
) -> None:
    """Export deterministic utilisation evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_utilisation_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Utilisation evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Utilisation evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-forecasting")
def run_forecasting(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Forecasting YAML config."),
    ] = Path("config/forecasting.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Forecasting evidence export directory."),
    ] = Path("outputs/forecasting"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing forecasting evidence.")
    ] = False,
) -> None:
    """Run deterministic demand forecasting."""

    try:
        database_path = database or load_database_path()
        summary = run_forecasting_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Forecasting run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Forecasting run complete: {summary['forecast_run_id']}")
    typer.echo(f"series: {summary['series_count']}")
    typer.echo(f"selections: {summary['selection_count']}")


@app.command("verify-forecasting")
def verify_forecasting(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted forecasting evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_forecasting_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Forecasting verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Forecasting verification passed "
        f"({summary['readiness_status']}, {summary['series_count']} series, "
        f"{summary['forecast_value_count']} forecast values)."
    )


@app.command("export-forecast-evidence")
def export_forecast_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Forecasting evidence export directory."),
    ] = Path("outputs/forecasting"),
) -> None:
    """Export deterministic forecasting evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_forecast_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Forecasting evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Forecasting evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-scenarios")
def run_scenarios(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Scenario YAML config."),
    ] = Path("config/scenarios.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Scenario evidence export directory."),
    ] = Path("outputs/scenarios"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing scenario evidence.")
    ] = False,
) -> None:
    """Run deterministic scenario analysis."""

    try:
        database_path = database or load_database_path()
        summary = run_scenarios_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Scenario run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Scenario run complete: {summary['scenario_run_id']}")
    typer.echo(f"scenarios: {summary['scenario_count']}")
    typer.echo(f"readiness_status: {summary['readiness_status']}")


@app.command("verify-scenarios")
def verify_scenarios(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted scenario evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_scenarios_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Scenario verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Scenario verification passed "
        f"({summary['readiness_status']}, {summary['scenario_count']} scenarios, "
        f"{summary['constraint_count']} constraints)."
    )


@app.command("export-scenario-evidence")
def export_scenario_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Scenario evidence export directory."),
    ] = Path("outputs/scenarios"),
) -> None:
    """Export deterministic scenario evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_scenario_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Scenario evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Scenario evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-optimisation")
def run_optimisation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Optimisation YAML config."),
    ] = Path("config/optimisation.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Optimisation evidence export directory."),
    ] = Path("outputs/optimisation"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing optimisation evidence.")
    ] = False,
) -> None:
    """Run deterministic constrained estate allocation optimisation."""

    try:
        database_path = database or load_database_path()
        summary = run_optimisation_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Optimisation run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Optimisation run complete: {summary['optimisation_run_id']}")
    typer.echo(f"cases: {summary['case_count']}")
    typer.echo(f"candidates: {summary['candidate_count']}")
    typer.echo(f"readiness_status: {summary['readiness_status']}")


@app.command("verify-optimisation")
def verify_optimisation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted optimisation evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_optimisation_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Optimisation verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Optimisation verification passed "
        f"({summary['readiness_status']}, {summary['case_count']} cases, "
        f"{summary['candidate_count']} candidates, "
        f"{summary['unmet_demand_hours']} unmet demand hours)."
    )


@app.command("export-optimisation-evidence")
def export_optimisation_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Optimisation evidence export directory."),
    ] = Path("outputs/optimisation"),
) -> None:
    """Export deterministic optimisation evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_optimisation_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Optimisation evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Optimisation evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-simulation")
def run_simulation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Simulation YAML config."),
    ] = Path("config/simulation.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Simulation evidence export directory."),
    ] = Path("outputs/simulation"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing simulation evidence.")
    ] = False,
) -> None:
    """Run deterministic operational room-flow simulation."""

    try:
        database_path = database or load_database_path()
        summary = run_simulation_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Simulation run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Simulation run complete: {summary['simulation_run_id']}")
    typer.echo(f"cases: {summary['case_count']}")
    typer.echo(f"experiments: {summary['experiment_count']}")
    typer.echo(f"replications: {summary['replications']}")
    typer.echo(f"readiness_status: {summary['readiness_status']}")


@app.command("verify-simulation")
def verify_simulation(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted simulation evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_simulation_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Simulation verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Simulation verification passed "
        f"({summary['readiness_status']}, {summary['case_count']} cases, "
        f"{summary['experiment_count']} experiments, "
        f"{summary['replication_rows']} replication rows)."
    )


@app.command("export-simulation-evidence")
def export_simulation_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Simulation evidence export directory."),
    ] = Path("outputs/simulation"),
) -> None:
    """Export deterministic simulation evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_simulation_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Simulation evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Simulation evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("run-financial-analysis")
def run_financial_analysis(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Finance YAML config."),
    ] = Path("config/finance.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Financial evidence export directory."),
    ] = Path("outputs/financial"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing financial evidence.")
    ] = False,
) -> None:
    """Run deterministic financial and sensitivity analysis."""

    try:
        database_path = database or load_database_path()
        summary = run_financial_analysis_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Financial analysis run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Financial analysis run complete: {summary['financial_run_id']}")
    typer.echo(f"cases: {summary['case_count']}")
    typer.echo(f"readiness_status: {summary['readiness_status']}")


@app.command("verify-financial-analysis")
def verify_financial_analysis(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
) -> None:
    """Verify persisted financial evidence."""

    try:
        database_path = database or load_database_path()
        summary = verify_financial_analysis_service(database_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Financial analysis verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Financial analysis verification passed "
        f"({summary['readiness_status']}, {summary['case_count']} cases, "
        f"{summary['comparison_rows']} comparison rows, "
        f"{summary['cashflow_rows']} cash-flow rows)."
    )


@app.command("export-financial-evidence")
def export_financial_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Financial evidence export directory."),
    ] = Path("outputs/financial"),
) -> None:
    """Export deterministic financial evidence from SQLite."""

    try:
        database_path = database or load_database_path()
        written = export_financial_evidence_service(database_path, output_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(f"Financial evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Financial evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("generate-communication-evidence")
def generate_communication_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Communication YAML config."),
    ] = Path("config/communication.yaml"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Communication evidence output directory."),
    ] = Path("outputs/communication"),
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing communication evidence.")
    ] = False,
) -> None:
    """Generate deterministic stakeholder communication and governance evidence."""

    try:
        from estate_intelligence.reporting.service import (
            generate_communication_evidence as generate_communication_evidence_service,
        )

        database_path = database or load_database_path()
        summary = generate_communication_evidence_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Communication evidence generation failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Communication evidence generated: {summary['communication_run_id']}")
    typer.echo(f"decision_status: {summary['decision_status']}")
    typer.echo(f"approval_status: {summary['approval_status']}")
    typer.echo(f"claim_count: {summary['claim_count']}")


@app.command("verify-communication-evidence")
def verify_communication_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Communication evidence output directory."),
    ] = Path("outputs/communication"),
) -> None:
    """Verify deterministic communication evidence and language controls."""

    try:
        from estate_intelligence.reporting.service import (
            verify_communication_evidence as verify_communication_evidence_service,
        )

        database_path = database or load_database_path()
        summary = verify_communication_evidence_service(database_path, output_dir=output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Communication evidence verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Communication evidence verification passed "
        f"({summary['communication_run_id']}, {summary['claim_count']} claims, "
        f"{summary['revision_count']} revisions)."
    )


@app.command("export-communication-evidence")
def export_communication_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Communication evidence output directory."),
    ] = Path("outputs/communication"),
) -> None:
    """Verify and list deterministic communication evidence exports."""

    try:
        from estate_intelligence.reporting.service import (
            export_existing_communication_evidence as export_communication_evidence_service,
        )

        database_path = database or load_database_path()
        written = export_communication_evidence_service(database_path, output_dir=output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Communication evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Communication evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("ingest-data")
def ingest_data(
    input_dir: Annotated[
        Path,
        typer.Option("--input-dir", help="Synthetic source data directory."),
    ] = Path("data/sample"),
    database: Annotated[Path | None, typer.Option("--database")] = None,
    rebuild: Annotated[bool, typer.Option("--rebuild")] = False,
) -> None:
    """Compatibility command for the Milestone 3 ingestion step."""

    build_curated_database(input_dir=input_dir, database=database, rebuild=rebuild)


@app.command("link-entities")
def link_entities(
    input_dir: Annotated[
        Path,
        typer.Option("--input-dir", help="Synthetic source data directory."),
    ] = Path("data/sample"),
    database: Annotated[Path | None, typer.Option("--database")] = None,
    rebuild: Annotated[bool, typer.Option("--rebuild")] = False,
) -> None:
    """Compatibility command for deterministic entity linking."""

    build_curated_database(input_dir=input_dir, database=database, rebuild=rebuild)


@app.command("run-assurance")
def run_assurance(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Assurance YAML config."),
    ] = Path("config/assurance.yaml"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Assurance evidence output directory."),
    ] = Path("outputs/assurance"),
    profile: Annotated[
        str,
        typer.Option("--profile", help="Assurance profile: ci_fast, ci_full or canonical."),
    ] = "canonical",
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Rebuild existing assurance evidence.")
    ] = False,
) -> None:
    """Run deterministic automated assurance and release-gate evidence."""

    try:
        from estate_intelligence.assurance.pipeline import run_assurance as run_assurance_service

        database_path = database or load_database_path()
        summary = run_assurance_service(
            database_path=database_path,
            config_path=config,
            output_dir=output_dir,
            profile=profile,
            rebuild=rebuild,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Assurance run failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if summary["required_failures"]:
        typer.echo(f"Assurance run failed required checks: {summary}", err=True)
        raise typer.Exit(code=2)
    typer.echo(f"Assurance run complete: {summary['assurance_run_id']}")
    typer.echo(f"profile: {summary['profile']}")
    typer.echo(f"release_readiness_status: {summary['release_readiness_status']}")
    typer.echo(f"checks: {summary['check_count']}")
    typer.echo(f"warnings: {summary['warning_count']}")


@app.command("verify-assurance")
def verify_assurance(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Assurance evidence output directory."),
    ] = Path("outputs/assurance"),
) -> None:
    """Verify deterministic assurance evidence and release gates."""

    try:
        from estate_intelligence.assurance.pipeline import (
            verify_assurance as verify_assurance_service,
        )

        database_path = database or load_database_path()
        summary = verify_assurance_service(database_path=database_path, output_dir=output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Assurance verification failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        "Assurance verification passed "
        f"({summary['assurance_run_id']}, {summary['gate_count']} gates, "
        f"{summary['output_count']} outputs)."
    )


@app.command("export-assurance-evidence")
def export_assurance_evidence(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Assurance evidence output directory."),
    ] = Path("outputs/assurance"),
) -> None:
    """Verify and list deterministic assurance evidence exports."""

    try:
        from estate_intelligence.assurance.pipeline import (
            export_assurance_evidence as export_assurance_evidence_service,
        )

        database_path = database or load_database_path()
        written = export_assurance_evidence_service(
            database_path=database_path, output_dir=output_dir
        )
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Assurance evidence export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Assurance evidence exported to {output_dir}")
    for name in sorted(written):
        typer.echo(name)


@app.command("release-readiness")
def release_readiness(
    database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Assurance evidence output directory."),
    ] = Path("outputs/assurance"),
) -> None:
    """Display engineering release readiness without implying governance approval."""

    verify_assurance(database=database, output_dir=output_dir)
    readiness_path = output_dir / "release_readiness.json"
    typer.echo(readiness_path.read_text(encoding="utf-8"))


@app.command("project-summary")
def project_summary() -> None:
    """Display final project lineage and governance status without running analytics."""

    try:
        from estate_intelligence.portfolio.service import project_summary as project_summary_service

        payload = project_summary_service()
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Project summary failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("portfolio-check")
def portfolio_check(
    config: Annotated[
        Path,
        typer.Option("--config", help="Portfolio YAML config."),
    ] = Path("config/portfolio.yaml"),
) -> None:
    """Validate and refresh the final portfolio manifest."""

    try:
        from estate_intelligence.portfolio.service import portfolio_check as portfolio_check_service

        result = portfolio_check_service(config_path=config, refresh_manifest=True)
        result.raise_for_failures()
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Portfolio check failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Portfolio check passed ({result.checked} assets checked).")


@app.command("handover-check")
def handover_check(
    config: Annotated[
        Path,
        typer.Option("--config", help="Portfolio YAML config."),
    ] = Path("config/portfolio.yaml"),
) -> None:
    """Validate final handover documentation."""

    try:
        from estate_intelligence.portfolio.service import handover_check as handover_check_service

        result = handover_check_service(config_path=config)
        result.raise_for_failures()
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Handover check failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Handover check passed ({result.checked} assets checked).")


@app.command("final-audit")
def final_audit(
    config: Annotated[
        Path,
        typer.Option("--config", help="Portfolio YAML config."),
    ] = Path("config/portfolio.yaml"),
) -> None:
    """Validate final milestone audit status and coverage."""

    try:
        from estate_intelligence.portfolio.service import final_audit as final_audit_service

        result = final_audit_service(config_path=config)
        result.raise_for_failures()
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        typer.echo(f"Final audit failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Final audit passed ({result.checked} milestones checked).")


if __name__ == "__main__":  # pragma: no cover
    app()
