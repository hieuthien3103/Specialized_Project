"""Adapter nối bài toán DPDP của đề tài với khung ALNS của Wouda & Lan [20].

Kiến trúc sau khi tách khung ALNS ra thư viện:

    khung ALNS (thư viện `alns`)          phần riêng của đề tài
    ─────────────────────────────          ─────────────────────────
    chọn toán tử theo trọng số (2.6)   ←    (dùng `RouletteWheel` của thư viện)
    cập nhật trọng số (2.7)           ←    (dùng `SegmentedRouletteWheel`)
    tiêu chuẩn chấp nhận SA (2.8),(2.9)←   (dùng `SimulatedAnnealing.autofit`)
    điều kiện dừng theo ngân sách B   ←    (dùng `MaxRuntime`)
    vòng lặp, đánh giá kết quả        ←    (dùng `ALNS.iterate`)
                                     ←    toán tử phá huỷ/sửa chữa (2.1.3–2.1.4)
                                     ←    cấu hình tham số (Bảng 2.4)
                                     ←    ghép với khung mô phỏng DES (mục 2.2.2)

Như vậy phần "đề xuất" của đề tài được thu hẹp còn: *cấu hình tham số* và
*cách ghép với DES*, đúng theo hướng đã thống nhất — không viết lại thuật
toán đã có, mà nghiên cứu và cấu hình trên nền tảng đã được công bố.

Thư viện `alns` yêu cầu:
  * toán tử phá huỷ: ``op(sol, rng, **kwargs) -> State`` — nhận lời giải *hiện
    tại* và trả về lời giải đã phá huỷ;
  * toán tử sửa chữa: ``op(sol, rng, **kwargs) -> State`` — nhận lời giải đã
    phá huỷ và trả về lời giải ứng viên;
  * ``State`` chỉ cần có phương thức ``objective() -> float``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.solution import Solution
from .config import ALNSConfig
from .operators import (DESTROY_OPERATORS, REPAIR_OPERATORS, FreeContext,
                         remove_requests)
from .rng import RNGAdapter

#: Thứ tự kết quả mà thư viện `alns` dùng cho điểm thưởng:
#: (mới tối ưu toàn cục, tốt hơn hiện tại, được chấp nhận, bị từ chối).
OUTCOME_ORDER = ("new_best", "better", "accepted", "rejected")


@dataclass
class DPDPState:
    """Bọc `Solution` của đề tài thành `State` của thư viện `alns`.

    `alns.State` chỉ đòi hỏi phương thức `objective()`. Ta bổ sung tham chiếu
    tới lời giải gốc để các toán tử và bộ đếm thống kê truy cập được.
    """

    solution: Solution
    #: Danh sách yêu cầu bị loại trong vòng lặp hiện tại (do toán tử phá huỷ
    #: ghi vào) — dùng để truyền sang toán tử sửa chữa.
    removed: list[int] = field(default_factory=list)

    def objective(self) -> float:
        """Giá trị hàm mục tiêu (công thức 2.1)."""
        return self.solution.cost


def _state_of(sol: Solution) -> DPDPState:
    return DPDPState(solution=sol)


def _unwrap(state) -> Solution:
    """Lấy `Solution` từ một state của thư viện `alns` (chấp nhận cả kiểu thô)."""
    return state.solution if isinstance(state, DPDPState) else state


def make_destroy_operator(name: str, config: ALNSConfig, ctx=None):
    """Tạo toán tử phá huỷ tương thích khung `alns`.

    Toán tử nhận lời giải hiện tại, **sao chép** nó, loại các yêu cầu theo
    nguyên lý của toán tử, rồi trả về state đã phá huỷ (kèm danh sách yêu cầu
    bị loại để toán tử sửa chữa dùng lại).

    Thư viện `alns` truyền `numpy.random.Generator`; các toán tử của đề tài
    viết theo API `random.Random`, nên ta bọc RNG bằng `RNGAdapter`.
    """
    fn = DESTROY_OPERATORS[name]

    def operator(state, rng, **kwargs):
        sol = _unwrap(state).copy()
        removed = fn(sol, RNGAdapter(rng), config, ctx)
        if not removed:
            # Không loại được gì: trả về chính lời giải (vô hiệu) để vòng lặp
            # vẫn tiến hóa, tránh kẹt.
            return _state_of(sol)
        # phá huỷ thực sự: loại các yêu cầu khỏi lộ trình
        remove_requests(sol, removed)
        out = _state_of(sol)
        out.removed = list(removed)
        return out

    operator.__name__ = f"destroy_{name}"
    return operator


def make_repair_operator(name: str, config: ALNSConfig, ctx=None):
    """Tạo toán tử sửa chữa tương thích khung `alns`.

    Toán tử nhận state đã phá huỷ, chèn lại các yêu cầu bị loại theo nguyên
    lý của toán tử, rồi trả về state ứng viên.
    """
    fn = REPAIR_OPERATORS[name]

    def operator(state, rng, **kwargs):
        sol = _unwrap(state)
        removed = list(getattr(state, "removed", []) or [])
        if removed:
            fn(sol, removed, RNGAdapter(rng), config, ctx)
        out = _state_of(sol)
        out.removed = []
        return out

    operator.__name__ = f"repair_{name}"
    return operator
