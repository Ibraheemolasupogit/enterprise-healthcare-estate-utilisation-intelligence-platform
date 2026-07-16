"""Deterministic seed derivation for simulation random streams."""

from __future__ import annotations

import hashlib
import random

SEED_STRATEGY_VERSION = "m9-stable-sha256-v1"


def stable_seed(master_seed: int, *parts: object) -> int:
    payload = "|".join([str(master_seed), *(str(part) for part in parts)])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2**31 - 1)


def random_stream(master_seed: int, *parts: object) -> random.Random:
    return random.Random(stable_seed(master_seed, *parts))
