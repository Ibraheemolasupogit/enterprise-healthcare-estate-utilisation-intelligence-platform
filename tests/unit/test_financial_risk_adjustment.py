from pathlib import Path

from estate_intelligence.financial.models import FinanceConfig
from estate_intelligence.financial.risk_adjustment import (
    confidence_status,
    readiness_status,
    realisability_cap,
)


def test_operational_failure_caps_realisability() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))

    assert realisability_cap(config, "fail") == 0.0
    assert readiness_status(1000.0, "fail", True) == "not_realisable_without_mitigation"
    assert confidence_status(0.9, config, "fail") == "not_realisable_without_mitigation"
