"""Tiêu chuẩn chấp nhận luyện kim mô phỏng (mục 2.1.6 của báo cáo).

Lời giải mới s′ được chấp nhận với xác suất (2.8):
    P_chấp nhận(s′) = min{1, exp(−(f(s′) − f(s)) / Θ)}

Nhiệt độ ban đầu được chọn sao cho một lời giải tệ hơn lời giải khởi tạo
w_0 phần trăm được chấp nhận với xác suất 0,5 (2.9):
    Θ_0 = w_0 · f(s_0) / ln 2

Với mục 2.2.5, nhiệt độ làm lạnh theo *thời gian* đã trôi qua (2.25):
    Θ_t = Θ_0 · (Θ_f / Θ_0)^(t / B_h)
Nhờ vậy nhiệt độ luôn đạt đúng Θ_f tại thời điểm hết ngân sách bất kể máy
tính chạy nhanh hay chậm.
"""
from __future__ import annotations

import math
import random


class SimulatedAnnealing:
    """Tiêu chuẫn chấp nhận SA với làm lạnh theo thời gian."""

    def __init__(self, initial_cost: float, initial_acceptance: float = 0.05,
                 final_ratio: float = 0.05, budget: float = 1.0):
        """initial_cost: f(s_0) — chi phí của lời giải khởi tạo."""
        if initial_cost <= 0:
            # tránh nhiệt độ bằng 0; dùng một giá trị lớn để chấp nhận rộng
            initial_cost = 1.0
        self.theta0 = initial_acceptance * initial_cost / math.log(2.0)
        self.theta_final = self.theta0 * final_ratio
        self.budget = max(budget, 1e-9)
        self.final_ratio = final_ratio

    def temperature(self, elapsed: float) -> float:
        """Nhiệt độ tại thời điểm đã trôi qua `elapsed` giây (2.25)."""
        frac = min(1.0, max(0.0, elapsed / self.budget))
        return self.theta0 * (self.final_ratio ** frac)

    def accept(self, current_cost: float, new_cost: float,
               elapsed: float, rng: random.Random) -> bool:
        """Quyết định có chấp nhận lời giải mới hay không (2.8)."""
        if new_cost <= current_cost:
            return True
        theta = self.temperature(elapsed)
        if theta <= 0:
            return False
        prob = math.exp(-(new_cost - current_cost) / theta)
        return rng.random() < prob


class AlwaysAccept:
    """Chấp nhận mọi lời giải mới — biến thể đối chứng cho thực nghiệm."""

    def temperature(self, elapsed: float) -> float:
        return 0.0

    def accept(self, current_cost: float, new_cost: float,
               elapsed: float, rng: random.Random) -> bool:
        return True


class HillClimbing:
    """Chỉ chấp nhận lời giải tốt hơn — biến thể đối chứng cho thực nghiệm."""

    def temperature(self, elapsed: float) -> float:
        return 0.0

    def accept(self, current_cost: float, new_cost: float,
               elapsed: float, rng: random.Random) -> bool:
        return new_cost <= current_cost


ACCEPTANCE_CRITERIA = {
    "sa": SimulatedAnnealing,
    "always": AlwaysAccept,
    "hill_climbing": HillClimbing,
}
