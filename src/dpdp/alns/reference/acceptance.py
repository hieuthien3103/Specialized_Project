"""Import tương thích cho ``dpdp.alns.acceptance``."""

from ..acceptance import (ACCEPTANCE_CRITERIA, AlwaysAccept, HillClimbing,
                          SimulatedAnnealing)

__all__ = [
    "ACCEPTANCE_CRITERIA", "AlwaysAccept", "HillClimbing", "SimulatedAnnealing",
]