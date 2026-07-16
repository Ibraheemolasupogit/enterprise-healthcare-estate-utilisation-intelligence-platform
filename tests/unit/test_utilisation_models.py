from pathlib import Path

import pytest
from pydantic import ValidationError

from estate_intelligence.metrics.models import UtilisationConfig


def test_utilisation_config_loads_and_weights_sum_to_one() -> None:
    config = UtilisationConfig.from_yaml(Path("config/utilisation.yaml"))

    assert config.framework_version == "m5-v1"
    assert round(sum(config.formula_weights.values()), 8) == 1.0


def test_utilisation_config_rejects_bad_weights() -> None:
    config = UtilisationConfig.from_yaml(Path("config/utilisation.yaml"))
    payload = config.model_dump()
    payload["formula_weights"]["actual_occupied_utilisation"] = 0.99

    with pytest.raises(ValidationError):
        UtilisationConfig.model_validate(payload)
