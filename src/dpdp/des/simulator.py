"""Khung mô phỏng sự kiện rời rạc của DPDP và tái tối ưu theo sự kiện.

Đây là **phần ghép** giữa khung ALNS (thư viện `alns`, Wouda & Lan [20]) và
bài toán giao nhận hàng động — tức là một trong hai đóng góp còn lại của đề
tài sau khi không viết lại thuật toán đã có.

Luồng sự kiện được cài đặt:

    E_1: yêu cầu xuất hiện tại τ_r; chèn và tái tối ưu ALNS ngay tại sự kiện.
    E_4: kết thúc mô phỏng tại T_H.

Mô phỏng này đánh giá kế hoạch lộ trình theo release time; nó không mô phỏng
xe chạy vật lý hay sự kiện xe quay về kho.

Ngân sách B là thời gian CPU tối đa cho từng lần tái tối ưu. Hệ số ς chỉ được
dùng để tính chân trời đóng băng H=ςB+H₀; ALNS chưa làm đồng hồ mô phỏng tiến.
Điều kiện dừng và tiêu chuẩn chấp nhận do thư viện `alns` thực hiện.
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass, field

from ..adaptations.freezing import FreezingConstraint
from ..alns.config import ALNSConfig
from ..alns.engine import ALNSEngine
from ..baselines import greedy_insertion, regret_insertion
from ..core.instance import Instance, dynamize
from ..core.route import Params
from ..core.solution import Solution
from .events import EventQueue, EventType


@dataclass
class SimConfig:
    """Cấu hình một lần mô phỏng DPDP."""

    horizon: float | None = None   # None = giờ đóng cửa kho của thể hiện
    rho: float = 0.3               # ρ: mức độ động (Định nghĩa 1.3)
    lead_time: float = 0.0         # Λ: thời gian dẫn tối thiểu
    budget: float = 2.0            # B: ngân sách CPU mỗi lần tái tối ưu (giây)
    max_iterations: int = 10_000   # N_max
    seed: int = 0
    num_vehicles: int | None = None
    #: Có dùng cơ chế đóng băng phần lộ trình đã cam kết (mục 2.2.3) hay không.
    use_freezing: bool = True
    #: Biên an toàn H_0 của chân trời đóng băng.
    freeze_safety: float = 0.0
    freeze_horizon: float = 0.0   # H_0 theo đơn vị thời gian của instance
    time_scale: float = 1.0       # ς: thời gian mô phỏng / giây CPU
    #: Có dùng bộ lọc ứng viên (mục 2.2.4) hay không.
    use_filter: bool = False
    filter_kappa: int = 5
    filter_delta_max: float = 0.0
    filter_phi_max: float = 0.0
    filter_radius: float = 0.0
    #: Có chạy ALNS sau mỗi yêu cầu mới xuất hiện hay không.
    reoptimize_on_arrival: bool = True
    #: Heuristic xây dựng lời giải ban đầu: ``greedy`` hoặc ``regret2``.
    #: Giá trị này tạo hai đối chứng chèn trong cùng một simulator.
    construction: str = "greedy"
    #: Giá trị ALNS ghi đè cho thí nghiệm hiệu chỉnh tham số. Chỉ chấp nhận
    #: trường hợp lệ của ``ALNSConfig`` để tránh cấu hình im lặng bị bỏ qua.
    alns_overrides: dict[str, object] = field(default_factory=dict)
    #: Kịch bản release đã sinh sẵn. Dùng để mọi thuật toán chạy đúng cùng
    #: một kịch bản thay vì tự động hoá lại trong từng lần chạy.
    release_times: dict[int, float] | None = None

    def alns_config(self) -> ALNSConfig:
        """Suy ra cấu hình ALNS tương ứng (Bảng 2.4)."""
        config = ALNSConfig(
            budget=self.budget,
            max_iterations=self.max_iterations,
            seed=self.seed,
            use_freezing=self.use_freezing,
            freeze_safety=self.freeze_safety,
            use_filter=self.use_filter,
            filter_kappa=self.filter_kappa,
            filter_delta_max=self.filter_delta_max,
            filter_phi_max=self.filter_phi_max,
            filter_radius=self.filter_radius,
        )
        unknown = set(self.alns_overrides) - set(ALNSConfig.__dataclass_fields__)
        if unknown:
            raise ValueError(f"alns_overrides không hợp lệ: {sorted(unknown)}")
        for key, value in self.alns_overrides.items():
            setattr(config, key, value)
        return config


@dataclass
class SimResult:
    """Kết quả một lần mô phỏng."""

    best_cost: float = 0.0
    served: int = 0
    rejected: int = 0
    total_distance: float = 0.0
    total_lateness: float = 0.0
    vehicles_used: int = 0
    reoptimizations: int = 0
    route_changes: int = 0
    improved_reoptimizations: int = 0
    seconds: float = 0.0
    decision_seconds: list[float] = field(default_factory=list)
    solution: Solution | None = None

    def as_row(self) -> dict:
        return {
            "best_cost": round(self.best_cost, 4),
            "served": self.served,
            "rejected": self.rejected,
            "total_distance": round(self.total_distance, 4),
            "total_lateness": round(self.total_lateness, 4),
            "vehicles_used": self.vehicles_used,
            "reoptimizations": self.reoptimizations,
            "route_changes": self.route_changes,
            "improved_reoptimizations": self.improved_reoptimizations,
            "seconds": round(self.seconds, 4),
            "decision_count": len(self.decision_seconds),
            "decision_seconds_mean": round(
                sum(self.decision_seconds) / len(self.decision_seconds), 4)
            if self.decision_seconds else 0.0,
            "decision_seconds_max": round(max(self.decision_seconds), 4)
            if self.decision_seconds else 0.0,
        }


class Simulator:
    """Bộ mô phỏng DPDP, tái tối ưu ngay khi mỗi yêu cầu động xuất hiện."""

    def __init__(self, inst: Instance, params: Params,
                 config: SimConfig | None = None):
        self.inst = inst
        self.params = params
        self.config = config or SimConfig()
        self.queue = EventQueue()
        self.completed: set[int] = set()
        self.now: float = 0.0
        self.solution: Solution | None = None
        self.release_original: dict[int, float] = {}
        self.release: dict[int, float] = self.release_original
        self.reoptimizations = 0
        self.route_changes = 0
        self.improved_reoptimizations = 0
        self.decision_seconds: list[float] = []
        #: Ràng buộc đã dùng ở chu kỳ gần nhất; phục vụ kiểm thử/audit thí nghiệm.
        self.last_freezing_constraint = None

    # ------------------------------------------------------------- khởi tạo
    def _setup(self) -> None:
        """Sinh sự kiện xuất hiện yêu cầu và tạo lời giải tĩnh ban đầu."""
        cfg = self.config
        n_veh = (cfg.num_vehicles if cfg.num_vehicles is not None
                 else self.inst.num_vehicles)

        release = (dict(cfg.release_times) if cfg.release_times is not None
                   else dynamize(self.inst, cfg.rho, cfg.lead_time,
                                 seed=cfg.seed))
        if set(release) != set(self.inst.requests):
            raise ValueError("release_times phải có đúng một thời điểm cho mỗi yêu cầu")
        if any(t < 0.0 for t in release.values()):
            raise ValueError("release_times không được âm")
        self.release_original = release
        self.release = self.release_original
        self.inst.release.clear()
        for p, tau in release.items():
            if tau > 0.0:
                self.queue.push(tau, EventType.NEW_REQUEST, p)
        self.horizon = (self.inst.nodes[0].l if cfg.horizon is None
                        else cfg.horizon)
        self.queue.push(self.horizon, EventType.SIMULATION_END)

        # Lời giải khởi đầu chỉ gồm các yêu cầu *tĩnh* (τ_r = 0). Yêu cầu
        # động chưa xuất hiện nên không được phục vụ trước thời điểm τ_r.
        static = [p for p, tau in release.items() if tau <= 0.0]
        constructors = {"greedy": greedy_insertion, "regret2": regret_insertion}
        try:
            construct = constructors[cfg.construction]
        except KeyError as exc:
            raise ValueError("construction phải là 'greedy' hoặc 'regret2'") from exc
        self.solution = construct(self.inst, self.params, requests=static,
                                  num_vehicles=n_veh)
        # Yêu cầu động chưa xuất hiện được coi là chưa phục vụ.
        self.solution.unassigned.update(
            p for p, tau in release.items() if tau > 0.0)

    # ---------------------------------------------------------------- DES
    def _horizon_H(self) -> float:
        """Chân trời cam kết theo đơn vị thời gian của instance: H=ςB+H₀."""
        cfg = self.config
        if not cfg.use_freezing:
            return 0.0
        return cfg.time_scale * cfg.budget + cfg.freeze_horizon

    def _frozen_prefix(self, route) -> int:
        nodes, now, horizon = self.inst.nodes, self.now, self._horizon_H()
        frozen = 0
        for j, nid in enumerate(route.stops):
            start = route.dep[j] - nodes[nid].s
            en_route = j > 0 and route.dep[j - 1] <= now
            if start <= now + horizon or en_route:
                frozen = j + 1
            else:
                break
        return frozen

    def _advance_release(self) -> None:
        """Không cho các điểm lấy còn tự do được lên lịch trước thời điểm hiện tại."""
        for route in self.solution.routes:
            frozen = self._frozen_prefix(route)
            for nid in route.stops[frozen:]:
                if self.inst.nodes[nid].is_pickup:
                    self.inst.release[nid] = max(
                        self.inst.release.get(nid, 0.0), self.now)

    def _constraint(self) -> FreezingConstraint:
        min_pos, free_map = {}, {}
        for k, route in enumerate(self.solution.routes):
            frozen = self._frozen_prefix(route)
            min_pos[k] = frozen
            free_map[k] = set(route.stops[frozen:])
        return FreezingConstraint(
            min_pos=min_pos,
            free_map=free_map,
            safety=self.config.freeze_safety,
            committed=frozenset(self.solution.served_requests),
        )

    def _handle_new_request(self, ev) -> None:
        """E_1: thêm yêu cầu mới tại thời điểm xuất hiện."""
        p = ev.payload
        self._advance_release()
        self.inst.release[p] = self.now
        d = self.inst.delivery_of(p)
        best = None
        for k, route in enumerate(self.solution.routes):
            candidate = route.best_insertion(
                p, d, min_pos=self._frozen_prefix(route))
            if candidate is not None and (
                    best is None or candidate[0] < best[0]):
                best = (candidate[0], k, candidate[1], candidate[2])

        if best is None:
            return
        _, k, i, j = best
        self.solution.routes[k].insert(p, d, i, j)
        self.solution.unassigned.discard(p)
        if self.config.reoptimize_on_arrival:
            self._reoptimize()

    def _handle_optimization_end(self, _ev) -> None:
        """E_3: mốc kết thúc chu kỳ tái tối ưu."""
        if _ev.type is not EventType.OPTIMIZATION_END:
            raise ValueError("sự kiện không phải OPTIMIZATION_END")

    def _handle_simulation_end(self, _ev) -> None:
        """E_4: kết thúc mô phỏng."""
        if _ev.type is not EventType.SIMULATION_END:
            raise ValueError("sự kiện không phải SIMULATION_END")

    def _reoptimize(self) -> None:
        """Tối ưu ngay tại sự kiện đến; CPU time chưa làm tiến đồng hồ mô phỏng."""
        if self.solution is None:
            return
        self._advance_release()
        constraint = self._constraint()
        self.last_freezing_constraint = constraint
        before_signature = tuple(tuple(route.stops)
                                 for route in self.solution.routes)
        before_cost = self.solution.cost
        cfg = self.config
        engine = ALNSEngine(
            self.inst, self.params, cfg.alns_config(),
            constraint=constraint, seed=cfg.seed)
        best, stats = engine.run(self.solution)
        self.decision_seconds.append(stats.seconds)
        self.solution = best
        self.reoptimizations += 1
        after_signature = tuple(tuple(route.stops)
                                for route in self.solution.routes)
        if after_signature != before_signature:
            self.route_changes += 1
        if self.solution.cost < before_cost - 1e-9:
            self.improved_reoptimizations += 1

    # ----------------------------------------------------------------- chạy
    def run(self) -> SimResult:
        """Chạy mô phỏng đến khi hết thời gian."""
        t0 = _time.perf_counter()
        self._setup()
        handlers = {
            EventType.NEW_REQUEST: self._handle_new_request,
            EventType.OPTIMIZATION_END: self._handle_optimization_end,
            EventType.SIMULATION_END: self._handle_simulation_end,
        }

        while True:
            ev = self.queue.pop()
            if ev is None:
                break
            if ev.time < self.now - 1e-9:
                raise RuntimeError("DES phát hiện sự kiện đi lùi thời gian")
            self.now = ev.time
            handlers[ev.type](ev)
            if ev.type is EventType.SIMULATION_END:
                break

        sol = self.solution
        return SimResult(
            best_cost=sol.cost,
            served=sol.n_served,
            rejected=len(sol.unassigned),
            total_distance=sol.distance,
            total_lateness=sol.lateness,
            vehicles_used=sol.vehicles_used,
            reoptimizations=self.reoptimizations,
            route_changes=self.route_changes,
            improved_reoptimizations=self.improved_reoptimizations,
            seconds=_time.perf_counter() - t0,
            decision_seconds=list(self.decision_seconds),
            solution=sol,
        )
