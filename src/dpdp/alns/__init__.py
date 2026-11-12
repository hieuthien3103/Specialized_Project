"""Engine ALNS-D của đề tài, chạy trên khung ALNS của Wouda & Lan [20].

Sau khi không viết lại thuật toán đã có, khung ALNS được lấy nguyên văn từ
thư viện `alns` (mã nguồn mở, JOSS 2023). Phần của đề tài gồm:

    2.1.3 nhóm toán tử phá huỷ      -> operators.py (destroy_*)
    2.1.4 nhóm toán tử sửa chữa      -> operators.py (repair_*)
    2.1.5 cơ chế cập nhật trọng số   -> thư viện `alns` (RouletteWheel)
    2.1.6 tiêu chuẩn chấp nhận        -> thư viện `alns` (SimulatedAnnealing)
    2.2.5 ngân sách thời gian (2.24)–(2.26) -> thư viện `alns` (MaxRuntime)
    Bảng 2.4 cấu hình tham số        -> config.py   ← *đóng góp của đề tài*
    ghép tái tối ưu theo sự kiện với DES -> engine.py ← *đóng góp của đề tài*

`weights.py` và `acceptance.py` là các implementation độc lập để đối chiếu.
Engine thực nghiệm vẫn dùng các thành phần tương ứng từ thư viện `alns`.
"""
from .acceptance import (ACCEPTANCE_CRITERIA, AlwaysAccept, HillClimbing,
                         SimulatedAnnealing)
from .adapter import DPDPState, make_destroy_operator, make_repair_operator
from .config import ALNSConfig
from .engine import ALNSEngine, ALNSStats
from .operators import (DESTROY_OPERATORS, REPAIR_OPERATORS, FreeContext,
                         destroy_random, destroy_related, destroy_worst,
                         repair_greedy, repair_greedy_noise, repair_regret)
from .weights import OperatorWeights

__all__ = [
    "ALNSConfig", "ALNSEngine", "ALNSStats",
    "OperatorWeights", "SimulatedAnnealing", "AlwaysAccept", "HillClimbing",
    "ACCEPTANCE_CRITERIA",
    "FreeContext", "DPDPState",
    "make_destroy_operator", "make_repair_operator",
    "DESTROY_OPERATORS", "REPAIR_OPERATORS",
    "destroy_random", "destroy_worst", "destroy_related",
    "repair_greedy", "repair_regret", "repair_greedy_noise",
]
