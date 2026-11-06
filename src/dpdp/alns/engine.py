"""Vòng lặp ALNS (mục 2.1) với điều kiện dừng theo thời gian (mục 2.2.5).

Một lần chạy engine = một *chu kỳ tái tối ưu*: nhận một lời giải hiện có,
chạy tối đa `budget` giây (hoặc `max_iterations` vòng lặp) các phép phá huỷ –
sửa chữa với tiêu chuẩn chấp nhận SA, rồi trả về lời giải tốt nhất tìm được.

Cấu trúc một vòng lặp:
    1. chọn toán tử phá huỷ theo trọng số (2.6)
    2. chọn toán tử sửa chữa theo trọng số (2.6)
    3. phá huỷ → sửa chữa → lời giải s′
    4. chấp nhận theo SA (2.8), ghi điểm thưởng (σ_1/σ_2/σ_3)
    5. cuối phân đoạn θ: làm trơn trọng số (2.7)
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from ..solution import Solution
from .acceptance import SimulatedAnnealing
from .config import ALNSConfig
from .operators import DESTROY_OPERATORS, REPAIR_OPERATORS, FreeContext
from .weights import OperatorWeights


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
    """Bộ máy ALNS chạy trên một lời giải cụ thể."""

    def __init__(self, inst, params, config: ALNSConfig | None = None,
                 constraint=None, seed: int | None = None):
        """
        inst, params : thể hiện và tham số hàm mục tiêu.
        config       : cấu hình ALNS (xem `alns/config.py`).
        constraint   : ràng buộc vùng tự do do cơ chế đóng băng cung cấp
                       (mục 2.2.3) — đối tượng có:
                         * ``min_pos_for(sol, k)`` -> int  (vị trí chèn tự do của xe k)
                         * ``free_requests(sol)`` -> list[int] (yêu cầu tự do)
                       Nếu None thì toàn bộ lộ trình là vùng tự do.
        """
        self.inst = inst
        self.params = params
        self.config = config or ALNSConfig()
        self.constraint = constraint
        self.seed = self.config.seed if seed is None else seed
        self.rng = random.Random(self.seed)

    # ------------------------------------------------------------ trợ giúp
    def _context(self, sol: Solution) -> FreeContext:
        """Thu thập thông tin vùng tự do từ ràng buộc đóng băng (nếu có)."""
        if self.constraint is None:
            return FreeContext()
        return self.constraint.context(sol)

    # --------------------------------------------------------------- chạy
    def run(self, initial: Solution) -> tuple[Solution, ALNSStats]:
        """Chạy một chu kỳ tái tối ưu; trả về (lời giải tốt nhất, thống kê)."""
        cfg = self.config
        sol = initial.copy()
        best = sol.copy()
        stats = ALNSStats(initial_cost=sol.cost, best_cost=sol.cost)

        destroy_weights = OperatorWeights(
            names=tuple(cfg.destroy_operators), reaction=cfg.reaction,
            sigma_new_best=cfg.sigma_new_best, sigma_better=cfg.sigma_better,
            sigma_accepted=cfg.sigma_accepted)
        repair_weights = OperatorWeights(
            names=tuple(cfg.repair_operators), reaction=cfg.reaction,
            sigma_new_best=cfg.sigma_new_best, sigma_better=cfg.sigma_better,
            sigma_accepted=cfg.sigma_accepted)

        sa = SimulatedAnnealing(
            initial_cost=max(sol.cost, 1e-9),
            initial_acceptance=cfg.initial_acceptance,
            final_ratio=cfg.final_temperature_ratio,
            budget=cfg.budget)

        t0 = time.perf_counter()
        last_improve = 0
        segment = 0
        segment_len = max(cfg.segment_min, 1)

        while True:
            elapsed = time.perf_counter() - t0
            if elapsed >= cfg.budget:
                break
            if stats.iterations >= cfg.max_iterations:
                break
            if stats.iterations - last_improve >= cfg.stall_iterations:
                break

            # --- 1, 2: chọn cặp toán tử theo trọng số (2.6) ---
            d_name = destroy_weights.select(self.rng)
            r_name = repair_weights.select(self.rng)
            destroy = DESTROY_OPERATORS[d_name]
            repair = REPAIR_OPERATORS[r_name]

            # --- 3: phá huỷ và sửa chữa ---
            cand = sol.copy()
            ctx = self._context(cand)
            removed = destroy(cand, self.rng, cfg, ctx)
            if not removed:
                stats.iterations += 1
                continue
            # loại thật khỏi lời giải rồi sửa chữa sẽ chèn lại
            _remove_requests(cand, removed)
            repair(cand, removed, self.rng, cfg, ctx)

            new_cost = cand.cost

            # --- 4: chấp nhận theo SA (2.8) và ghi điểm thưởng ---
            if new_cost < best.cost - 1e-12:
                kind = "new_best"
            elif new_cost < sol.cost - 1e-12:
                kind = "better"
            else:
                kind = None

            accepted = sa.accept(sol.cost, new_cost, elapsed, self.rng)
            if accepted:
                sol = cand
                stats.accepted += 1
                if kind is not None:
                    stats.improved += 1
                if kind == "new_best":
                    best = cand.copy()
                    stats.new_best += 1
                    last_improve = stats.iterations
                destroy_weights.reward(d_name, kind or "accepted")
                repair_weights.reward(r_name, kind or "accepted")

            stats.iterations += 1

            # --- 5: làm trơn trọng số theo phân đoạn θ (2.7) ---
            segment += 1
            if segment >= segment_len:
                destroy_weights.update()
                repair_weights.update()
                destroy_weights.reset_segment()
                repair_weights.reset_segment()
                segment = 0
                # (2.2.5) kế thừa trọng số giữa các chu kỳ: trọng số đã cập
                # nhật được giữ nguyên trong `self._carry_weights`.

        elapsed = time.perf_counter() - t0
        stats.final_cost = sol.cost
        stats.best_cost = best.cost
        stats.seconds = elapsed
        stats.weights = {**destroy_weights.snapshot(),
                         **{f"repair:{k}": v for k, v in repair_weights.snapshot().items()}}
        stats.average_scores = {**destroy_weights.average_scores,
                                **{f"repair:{k}": v for k, v in repair_weights.average_scores.items()}}
        # kế thừa trọng số cho chu kỳ sau (mục 2.2.5)
        self._carry_weights = (destroy_weights.snapshot(), repair_weights.snapshot())
        return best, stats


def _remove_requests(sol: Solution, requests: list[int]) -> None:
    """Loại các yêu cầu đã cho khỏi lời giải (đưa về trạng thái bị từ chối)."""
    inst = sol.inst
    for p in requests:
        d = inst.delivery_of(p)
        for route in sol.routes:
            if p in route.stops and d in route.stops:
                route.remove_request(p, d)
                break
        sol.unassigned.add(p)
