"""Engine ALNS-D chạy trên khung ALNS của Wouda & Lan [20].

Từ bước này, toàn bộ phần khung (chọn toán tử theo trọng số, cập nhật trọng
số, tiêu chuẩn chấp nhận, điều kiện dừng, vòng lặp) do thư viện `alns` thực
hiện. Phần của đề tài gồm:

  * các toán tử phá huỷ/sửa chữa (mục 2.1.3 – 2.1.4) trong `operators.py`;
  * bộ chuyển đổi giữa bài toán DPDP và `alns.State` trong `adapter.py`;
  * *cấu hình tham số* theo Bảng 2.4 trong `config.py` — đây là phần
    "đề xuất" của đề tài sau khi không viết lại thuật toán đã có;
  * *cách ghép* chu kỳ tái tối ưu với khung mô phỏng DES (mục 2.2.2).

Ánh xạ tham số Bảng 2.4 → thư viện:

  ┌──────────────────────────┬──────────────────────────────────────────┐
  │ Báo cáo                  │ Thư viện `alns`                          │
  ├──────────────────────────┼──────────────────────────────────────────┤
  │ (2.6) chọn toán tử       │ `RouletteWheel` / `SegmentedRouletteWheel`│
  │ (2.7) cập nhật trọng số  │ `decay = 1 − λ` (tương đương)            │
  │ σ₁,σ₂,σ₃ (Bảng 2.4)     │ `scores = [σ₁, σ₂, σ₃, 0]`              │
  │ (2.8) chấp nhận SA       │ `SimulatedAnnealing`                     │
  │ (2.9) nhiệt độ đầu      │ `SimulatedAnnealing.autofit`             │
  │ (2.24) ngân sách B       │ `MaxRuntime`                            │
  │ (2.25) dừng khi đi lạc   │ `NoImprovement`                          │
  └──────────────────────────┴──────────────────────────────────────────┘
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from alns import ALNS
from alns.accept import AlwaysAccept, HillClimbing, SimulatedAnnealing
from alns.select import RandomSelect, RouletteWheel, SegmentedRouletteWheel
from alns.stop import MaxIterations, MaxRuntime, NoImprovement

from ..core.solution import Solution
from .adapter import DPDPState, make_destroy_operator, make_repair_operator
from .config import ALNSConfig
from .rng import make_rng


@dataclass
class ALNSStats:
    """Thống kê một lần chạy engine (dùng cho báo cáo và ghi log)."""

    iterations: int = 0
    accepted: int = 0
    improved: int = 0
    new_best: int = 0
    initial_cost: float = 0.0
    best_cost: float = 0.0
    final_cost: float = 0.0
    seconds: float = 0.0
    weights: dict[str, float] = field(default_factory=dict)
    average_scores: dict[str, float] = field(default_factory=dict)

    def as_row(self) -> dict:
        return {
            "iterations": self.iterations,
            "accepted": self.accepted,
            "improved": self.improved,
            "new_best": self.new_best,
            "initial_cost": round(self.initial_cost, 4),
            "best_cost": round(self.best_cost, 4),
            "final_cost": round(self.final_cost, 4),
            "seconds": round(self.seconds, 4),
        }


class ALNSEngine:
    """Bộ máy ALNS chạy trên một lời giải cụ thể, dùng khung thư viện `alns`.

    Một lần chạy engine = một *chu kỳ tái tối ưu* (mục 2.2.2): nhận một lời
    giải hiện có, chạy tối đa `budget` giây các phép phá huỷ – sửa chữa với
    tiêu chuẩn chấp nhận SA, rồi trả về lời giải tốt nhất tìm được.
    """

    def __init__(self, inst, params, config: ALNSConfig | None = None,
                 constraint=None, seed: int | None = None):
        """
        inst, params : thể hiện và tham số hàm mục tiêu.
        config       : cấu hình ALNS (xem `alns/config.py`).
        constraint   : ràng buộc vùng tự do do cơ chế đóng băng cung cấp
                       (mục 2.2.3) — đối tượng có phương thức ``context(sol)``
                       trả về `FreeContext`. Nếu None thì toàn bộ lộ trình là
                       vùng tự do.
        """
        self.inst = inst
        self.params = params
        self.config = config or ALNSConfig()
        self.constraint = constraint
        self.seed = self.config.seed if seed is None else seed

    # ------------------------------------------------------------ trợ giúp
    def _context(self, sol: Solution):
        """Thu thập thông tin vùng tự do từ ràng buộc đóng băng (nếu có)."""
        if self.constraint is None:
            return None
        return self.constraint.context(sol)

    def _select_scheme(self, cfg: ALNSConfig):
        """Chọn cách chọn toán tử theo trọng số (2.6).

        `SegmentedRouletteWheel` khớp cơ chế (2.7) của báo cáo: trọng số được
        *cố định* trong một phân đoạn và chỉ cập nhật ở cuối phân đoạn, với
        tổng điểm thưởng của phân đoạn dùng làm điểm tham chiếu.
        """
        n_d, n_r = len(cfg.destroy_operators), len(cfg.repair_operators)
        scores = [cfg.sigma_new_best, cfg.sigma_better, cfg.sigma_accepted, 0.0]
        # decay = 1 − λ: trọng số mới = λ·(điểm thưởng) + (1−λ)·(trọng số cũ)
        decay = 1.0 - cfg.reaction
        if cfg.segment_min > 1:
            return SegmentedRouletteWheel(scores, decay, cfg.segment_min,
                                          n_d, n_r)
        return RouletteWheel(scores, decay, n_d, n_r)

    def _accept_criterion(self, cfg: ALNSConfig, init_cost: float,
                          iters: int):
        """Tiêu chuẩn chấp nhận (2.8).

        Nhiệt độ ban đầu được hiệu chỉnh theo (2.9): lời giải tệ hơn w₀% được
        chấp nhận với xác suất khoảng 0,5 — đúng công thức mà
        `SimulatedAnnealing.autofit` của thư viện cài đặt.
        """
        if cfg.acceptance == "always":
            return AlwaysAccept()
        if cfg.acceptance == "hill_climbing":
            return HillClimbing()
        # `autofit` yêu cầu số vòng lặp để nhiệt độ hạ xuống T_end.
        num_iters = max(1, cfg.max_iterations)
        return SimulatedAnnealing.autofit(
            init_obj=max(init_cost, 1e-9),
            worse=cfg.initial_acceptance,
            accept_prob=0.5,
            num_iters=num_iters,
        )

    def _stopping_criteria(self, cfg: ALNSConfig):
        """Điều kiện dừng (2.24) – (2.26)."""
        criteria = [MaxRuntime(cfg.budget)]
        if cfg.max_iterations < 10**9:
            criteria.append(MaxIterations(cfg.max_iterations))
        if cfg.stall_iterations > 0:
            criteria.append(NoImprovement(cfg.stall_iterations))
        if len(criteria) == 1:
            return criteria[0]
        return _AnyCriterion(criteria)

    # --------------------------------------------------------------- chạy
    def run(self, initial: Solution) -> tuple[Solution, ALNSStats]:
        """Chạy một chu kỳ tái tối ưu; trả về (lời giải tốt nhất, thống kê)."""
        cfg = self.config
        t0 = time.perf_counter()

        sol = initial.copy()
        initial_cost = sol.cost
        stats = ALNSStats(initial_cost=initial_cost, best_cost=initial_cost)

        # RNG của thư viện phải là numpy.Generator; adapter trong `rng.py` cầu
        # nối sang API của các toán tử của đề tài.
        import numpy as np
        np_rng = np.random.default_rng(self.seed)
        rng = make_rng(self.seed)

        ctx = self._context(sol)

        alns = ALNS(np_rng)
        for name in cfg.destroy_operators:
            alns.add_destroy_operator(
                make_destroy_operator(name, cfg, ctx), name=f"destroy_{name}")
        for name in cfg.repair_operators:
            alns.add_repair_operator(
                make_repair_operator(name, cfg, ctx), name=f"repair_{name}")

        scheme = self._select_scheme(cfg)
        accept = self._accept_criterion(cfg, initial_cost, cfg.max_iterations)
        stop = self._stopping_criteria(cfg)

        # Theo dõi kết quả từng vòng lặp qua callback `on_better`/`on_accept`
        counters = {"accepted": 0, "improved": 0, "new_best": 0}

        def _on_best(state, rng_, **kwargs):
            counters["new_best"] += 1
            counters["improved"] += 1

        def _on_better(state, rng_, **kwargs):
            counters["improved"] += 1

        def _on_accept(state, rng_, **kwargs):
            counters["accepted"] += 1

        alns.on_best(_on_best)
        alns.on_better(_on_better)
        alns.on_accept(_on_accept)

        initial_state = DPDPState(
            solution=sol,
            committed=getattr(ctx, "committed", frozenset()),
        )
        result = alns.iterate(initial_state, scheme, accept, stop)

        best_sol = result.best_state.solution
        elapsed = time.perf_counter() - t0

        stats.iterations = len(result.statistics.objectives) - 1
        stats.accepted = counters["accepted"]
        stats.improved = counters["improved"]
        stats.new_best = counters["new_best"]
        stats.final_cost = result.best_state.objective()
        stats.best_cost = stats.final_cost
        stats.seconds = elapsed
        stats.weights = _weights_to_dict(scheme, cfg)
        stats.average_scores = _scores_to_dict(result.statistics, cfg)
        return best_sol, stats


class _AnyCriterion:
    """Dừng khi *bất kỳ* tiêu chí nào nào trong danh sách thỏa mãn."""

    def __init__(self, criteria):
        self._criteria = criteria

    def __call__(self, rng, best, current) -> bool:
        return any(c(rng, best, current) for c in self._criteria)


def _weights_to_dict(scheme, cfg: ALNSConfig) -> dict[str, float]:
    """Trọng số toán tử sau khi chạy, theo đúng thứ tự đăng ký."""
    out: dict[str, float] = {}
    d_w = getattr(scheme, "destroy_weights", None)
    r_w = getattr(scheme, "repair_weights", None)
    if d_w is not None:
        for name, w in zip(cfg.destroy_operators, d_w):
            out[f"destroy:{name}"] = round(float(w), 6)
    if r_w is not None:
        for name, w in zip(cfg.repair_operators, r_w):
            out[f"repair:{name}"] = round(float(w), 6)
    return out


def _scores_to_dict(statistics, cfg: ALNSConfig) -> dict[str, float]:
    """Điểm thưởng tích luỹ của từng toán tử.

    Thư viện `alns` theo dõi *số lần* theo từng kết quả
    (`destroy_operator_counts`), không trực tiếp điểm thưởng. Ta tính điểm
    thưởng tích luỹ theo cùng bộ σ của Bảng 2.4 để báo cáo được.
    """
    out: dict[str, float] = {}
    if statistics is None:
        return out
    scores = [cfg.sigma_new_best, cfg.sigma_better, cfg.sigma_accepted, 0.0]
    for name, c in statistics.destroy_operator_counts.items():
        out[f"destroy:{name}"] = round(
            float(sum(s * n for s, n in zip(scores, c))), 6)
    for name, c in statistics.repair_operator_counts.items():
        out[f"repair:{name}"] = round(
            float(sum(s * n for s, n in zip(scores, c))), 6)
    return out
