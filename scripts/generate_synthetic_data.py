"""Script wrapper for deterministic synthetic source-data generation."""

from pathlib import Path

from estate_intelligence.synthetic_data.generator import SyntheticDataConfig, write_datasets


def main() -> None:
    """Generate the committed sample profile."""

    config = SyntheticDataConfig.from_yaml()
    write_datasets(config, Path("data/sample"), overwrite=True)


if __name__ == "__main__":
    main()
