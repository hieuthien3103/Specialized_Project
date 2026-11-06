"""Engine ALNS: toán tử phá huỷ/sửa chữa, trọng số, tiêu chuẩn chấp nhận.

Ánh xạ báo cáo:
    2.1.3 nhóm toán tử phá huỷ      -> operators.py (destroy_*)
    2.1.4 nhóm toán tử sửa chữa      -> operators.py (repair_*)
    2.1.5 cơ chế cập nhật trọng số   -> weights.py
    2.1.6 tiêu chuẩn chấp nhận        -> acceptance.py
    2.2.5 ngân sách thời gian (2.24)–(2.26) -> engine.py
"""
from .acceptance import (ACCEPTANCE_CRITERIA, AlwaysAccept, HillClimbing,
                         SimulatedAnnealing)
from .config import ALNSConfig
from .engine import ALNSEngine, ALNSStats
from .operators import (DESTROY_OPERATORS, REPAIR_OPERATORS, FreeContext,
                         destroy_random, destroy_related, destroy_worst,
                         repair_greedy, repair_greedy_noise, repair_regret)
from .weights import OperatorWeights

__all__ = [
    "ALNSConfig", "ALNSEngine", "ALNSStats", "OperatorWeights",
    "SimulatedAnnealing", "AlwaysAccept", "HillClimbing",
    "ACCEPTANCE_CRITERIA", "FreeContext",
    "DESTROY_OPERATORS", "REPAIR_OPERATORS",
    "destroy_random", "destroy_worst", "destroy_related",
    "repair_greedy", "repair_regret", "repair_greedy_noise",
]
