"""Cơ chế cập nhật trọng số thích nghi (mục 2.1.5 của báo cáo).

Chọn toán tử theo xác suất tỷ lệ với trọng số (2.6):
    P_i = w_i / Σ_j w_j

Sau mỗi vòng lặp, cặp toán tử vừa dùng nhận điểm thưởng:
    σ_1 nếu s′ là lời giải tốt nhất mới;
    σ_2 nếu s′ tốt hơn s và chưa từng được thăm;
    σ_3 nếu s′ được chấp nhận dù không tốt hơn s và chưa từng được thăm.

Sau mỗi phân đoạn θ vòng lặp, trọng số được làm trơn (2.7):
    w_{i,k+1} = (1 − λ)·w_{i,k} + λ·π_i/n_i

Theo Mệnh đề 2.1, w_{i,k} − π̄_i = (1−λ)^k (w_{i,0} − π̄_i): trọng số hội tụ
hình học về điểm thưởng trung bình với tỷ số 1−λ.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class OperatorWeights:
    """Quản lý trọng số và điểm thưởng cho một tập toán tử."""

    names: tuple[str, ...]
    reaction: float = 0.1          # λ
    sigma_new_best: float = 33.0   # σ_1
    sigma_better: float = 9.0      # σ_2
    sigma_accepted: float = 13.0   # σ_3
    weights: dict[str, float] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    uses: dict[str, int] = field(default_factory=dict)
    total_scores: dict[str, float] = field(default_factory=dict)
    total_uses: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.names:
            raise ValueError("cần ít nhất một toán tử")
        for name in self.names:
            self.weights.setdefault(name, 1.0)
            self.scores.setdefault(name, 0.0)
            self.uses.setdefault(name, 0)
            self.total_scores.setdefault(name, 0.0)
            self.total_uses.setdefault(name, 0)

    # ------------------------------------------------------------ chọn toán tử
    def select(self, rng: random.Random) -> str:
        """Chọn một toán tử theo xác suất tỷ lệ với trọng số (2.6)."""
        total = sum(self.weights[n] for n in self.names)
        if total <= 0:
            return rng.choice(list(self.names))
        x = rng.random() * total
        acc = 0.0
        for name in self.names:
            acc += self.weights[name]
            if x <= acc:
                return name
        return self.names[-1]

    # ------------------------------------------------------------ điểm thưởng
    def reward(self, name: str, kind: str) -> None:
        """Ghi nhận điểm thưởng cho toán tử vừa dùng.

        kind ∈ {"new_best", "better", "accepted"}.
        """
        if kind == "new_best":
            pts = self.sigma_new_best
        elif kind == "better":
            pts = self.sigma_better
        elif kind == "accepted":
            pts = self.sigma_accepted
        else:
            raise ValueError(f"loại điểm thưởng không hợp lệ: {kind}")
        self.scores[name] += pts
        self.uses[name] += 1
        self.total_scores[name] += pts
        self.total_uses[name] += 1

    def reset_segment(self) -> None:
        """Đặt lại bộ đếm của phân đoạn.

        Theo (2.7), π_i là *tổng điểm thưởng trong phân đoạn* và n_i là số lần
        dùng trong phân đoạn, nên cả hai phải được đặt lại cùng lúc. Các bộ
        đếm tích luỹ (`total_*`) được giữ lại để báo cáo.
        """
        for name in self.names:
            self.uses[name] = 0
            self.scores[name] = 0.0

    # ------------------------------------------------------- cập nhật trọng số
    def update(self) -> None:
        """Làm trơn trọng số theo (2.7). Nếu n_i = 0 thì w_i giữ nguyên."""
        for name in self.names:
            n = self.uses[name]
            if n == 0:
                continue
            pi_bar = self.scores[name] / n
            self.weights[name] = ((1.0 - self.reaction) * self.weights[name]
                                   + self.reaction * pi_bar)

    # --------------------------------------------------------------- truy vấn
    @property
    def average_scores(self) -> dict[str, float]:
        """π̄_i = π_i / n_i — điểm thưởng trung bình mỗi lần dùng."""
        return {n: (self.scores[n] / self.uses[n] if self.uses[n] else 0.0)
                for n in self.names}

    def snapshot(self) -> dict[str, float]:
        return dict(self.weights)

    def restore(self, snapshot: dict[str, float]) -> None:
        self.weights.update({k: v for k, v in snapshot.items() if k in self.weights})
