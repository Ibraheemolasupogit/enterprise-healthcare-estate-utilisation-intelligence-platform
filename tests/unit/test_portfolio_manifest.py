from pathlib import Path

from estate_intelligence.portfolio.manifest import build_manifest
from estate_intelligence.portfolio.service import load_portfolio_config

ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_manifest_excludes_json_self_checksum() -> None:
    config = load_portfolio_config()
    assets = build_manifest(
        ROOT,
        [*config.portfolio_assets, *config.handover_assets, *config.diagrams, *config.docs],
        excluded={config.manifest_json, config.manifest_csv},
    )

    paths = {asset.path for asset in assets}

    assert config.manifest_json not in paths
    assert config.manifest_csv not in paths


def test_portfolio_manifest_is_deterministically_ordered() -> None:
    config = load_portfolio_config()
    asset_paths = [*config.handover_assets, *config.portfolio_assets, *config.diagrams]
    assets = build_manifest(ROOT, asset_paths, excluded={config.manifest_json})

    assert [asset.path for asset in assets] == sorted(asset.path for asset in assets)
