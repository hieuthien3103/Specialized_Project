"""Khung mô phỏng sự kiện rời rạc của DPDP và tái tối ưu theo chu kỳ.

Đây là **phần ghép** giữa khung ALNS (thư viện `alns`, Wouda & Lan [20]) và
bài toán giao nhận hàng động — tức là một trong hai đóng góp còn lại của đề
tài sau khi không viết lại thuật toán đã có.

Kiến trúc tái tối ưu theo chu kỳ (Thuật toán 2.2 của báo cáo, mục 2.2.2):

    ┌─ E_1: yêu cầu mới xuất hiện tại τ_r ─────────────────────────┐
    │   chọn xe rảnh gần nhất; nếu không có xe rảnh → yêu cầu vào  │
    │   hàng đợi chờ (R_pending)                                    │
    │   xe được giao → khởi động chu kỳ tái tối ưu với ngân sách B   │
    └────────────────────────────────────────────────────────────────┘
    ┌─ E_2: phương tiện hoàn thành chặng ──────────────────────────┐
    │   phần lộ trình đã cam kết được tiến lên; lấy yêu cầu đang    │
    │   chờ từ hàng đợi nếu có xe rảnh                             │
    └────────────────────────────────────────────────────────────────┘
    ┌─ E_3: hết ngân sách tái tối ưu ──────────────────────────────┐
    │   chốt lời giải; phần lô trình đã cam kết của mỗi xe được    │
    │   đóng băng (mục 2.2.3)                                        │
    └────────────────────────────────────────────────────────────────┘
    ┌─ E_4: kết thúc mô phỏng (t = T_H) ────────────────────────────┐
    │   trả về lời giải tốt nhất                                     │
    └────────────────────────────────────────────────────────────────┘

Ranh giới trách nhiệm: *ngân sách thời gian* B, *điều kiện dừng* và *tiêu
chuẩn chấp nhận* do thư viện `alns` thực hiện (`MaxRuntime`,
`SimulatedAnnealing`). Bộ điều khiển ở đây chỉ quyết định *khi nào* gọi một
chu kỳ tái tối ưu và *làm gì* với lời giải sau đó.
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass, field

from ..adaptations.freezing import FreezingManager
from ..alns.config import ALNSConfig
from ..alns.engine import ALNSEngine
from ..baselines import greedy_insertion
from ..core.instance import Instance, dynamize
from ..core.route import Params
from ..core.solution import Solution
from .events import EventQueue, EventType


@dataclass
class SimConfig:
    """Cấu hình một lần mô phỏng DPDP."""

    horizon: float = 1000.0        # T_H: chiều dài thời gian mô phỏng
    rho: float = 0.3               # ρ: mức độ động (Định nghĩa 1.3)
    lead_time: float = 0.0         # Λ: thời gian dẫn tối thiểu
    budget: float = 2.0            # B: ngân sách tái tối ưu mỗi chu kỳ (giây)
    max_iterations: int = 10_000   # N_max
    seed: int = 0
    num_vehicles: int | None = None
    #: Có dùng cơ chế đóng băng phần lộ trình đã cam kết (mục 2.2.3) hay không.
    use_freezing: bool = True
    #: Biên an toàn H_0 của chân trời đóng băng.
    freeze_safety: float = 0.0
    #: Có dùng bộ lọc ứng viên (mục 2.2.4) hay không.
    use_filter: bool = False
    filter_kappa: int = 5
    filter_delta_max: float = 0.0
    filter_phi_max: float = 0.0
    filter_radius: float = 0.0
    #: Có chạy ALNS sau mỗi yêu cầu mới xuất hiện hay không.
    reoptimize_on_arrival: bool = True

    def alns_config(self) -> ALNSConfig:
        """Suy ra cấu hình ALNS tương ứng (Bảng 2.4)."""
        return ALNSConfig(
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
        }


@dataclass
class _Vehicle:
    """Trạng thái một phương tiện trong mô phỏng.

    Mỗi xe chạy một *chuyến* gồm nhiều yêu cầu: `stops` là các yêu cầu xe
    đang mang (theo thứ tự thời gian), `committed` là số nút đầu tiên đã
    *thực thi* (không thể thay đổi nữa, Mệnh đề 2.3).
    """

    index: int
    stops: list[int] = field(default_factory=list)
    committed: int = 0
    free_at: float = 0.0
    position: int = 0            # nút hiện tại (0 = kho)

    @property
    def free(self) -> bool:
        return not self.stops


class Simulator:
    """Bộ mô phỏng DPDP với tái tối ưu theo chu kỳ bằng ALNS."""

    def __init__(self, inst: Instance, params: Params,
                 config: SimConfig | None = None):
        self.inst = inst
        self.params = params
        self.config = config or SimConfig()
        self.queue = EventQueue()
        self.vehicles: list[_Vehicle] = []
        self.pending: list[int] = []      # yêu cầu chờ được giao
        #: Yêu cầu đã được phục vụ và hoàn thành trong mô phỏng.
        self.completed: set[int] = set()
        #: Quãng đường đã thực thi (công thức 1.4: tính trên toàn bộ phần
        #: lộ trình đã thực thi của mọi xe).
        self.executed_distance: float = 0.0
        self.solution: Solution | None = None
        self.reoptimizations = 0
        self.route_changes = 0
        self.improved_reoptimizations = 0
        self.freezing = FreezingManager(safety=self.config.freeze_safety)
        #: Số yêu cầu bị từ chối vì không còn xe rảnh.
        #: Yêu cầu từng không tìm được xe nào khả thi (đã bị từ chối).
        self.rejected_for_capacity = 0

    # ------------------------------------------------------------- khởi tạo
    def _setup(self) -> None:
        """Sinh sự kiện E_1 cho các yêu cầu động và tạo đội xe."""
        cfg = self.config
        n_veh = (cfg.num_vehicles if cfg.num_vehicles is not None
                 else self.inst.num_vehicles)
        self.vehicles = [_Vehicle(index=i) for i in range(n_veh)]

        release = dynamize(self.inst, cfg.rho, cfg.lead_time, seed=cfg.seed)
        self.release = release
        for p, tau in release.items():
            if tau > 0.0:
                self.queue.push(tau, EventType.NEW_REQUEST, p)
        self.queue.push(cfg.horizon, EventType.SIMULATION_END)

        # Lời giải khởi đầu chỉ gồm các yêu cầu *tĩnh* (τ_r = 0). Yêu cầu
        # động chưa xuất hiện nên không được phục vụ trước thời điểm τ_r.
        static = [p for p, tau in release.items() if tau <= 0.0]
        self.solution = greedy_insertion(
            self.inst, self.params, requests=static, num_vehicles=n_veh)
        # Yêu cầu động chưa xuất hiện được coi là chưa phục vụ.
        self.solution.unassigned.update(
            p for p, tau in release.items() if tau > 0.0)

        # Đồng bộ trạng thái vận hành của từng xe với lộ trình tĩnh ban đầu:
        # xe nào có lộ trình thì bắt đầu chạy, và lên lịch sự kiện E_2 (xe
        # hoàn thành chặng) tại thời điểm quay về kho.
        for k, route in enumerate(self.solution.routes):
            reqs = [nid for nid in route.stops if self.inst.nodes[nid].is_pickup]
            if not reqs:
                continue
            veh = self.vehicles[k]
            veh.stops = list(reqs)
            self._schedule_finish(veh)

    def _schedule_finish(self, veh: _Vehicle) -> None:
        """Lên lịch sự kiện E_2 khi xe hoàn thành lộ trình hiện tại."""
        if not veh.stops:
            return
        inst = self.inst
        total = 0.0
        prev = 0
        for p in veh.stops:
            d = inst.delivery_of(p)
            total += inst.tt[prev][p] + inst.nodes[p].s + inst.tt[p][d] \
                + inst.nodes[d].s
            prev = d
        total += inst.tt[prev][0]
        self.queue.push(total, EventType.VEHICLE_FREE, veh.index)

    def _trip_distance(self, reqs: list[int]) -> float:
        """Quãng đường của một chuyến theo thứ tự thực thi.

        Chuỗi đi thực tế là: kho → lấy₁ → giao₁ → lấy₂ → giao₂ → … → kho.
        """
        if not reqs:
            return 0.0
        dist = self.inst.dist
        total = 0.0
        prev = 0
        for p in reqs:
            d = self.inst.delivery_of(p)
            total += dist[prev][p] + dist[p][d]
            prev = d
        return total + dist[prev][0]

    # ---------------------------------------------------------------- DES
    def _handle_new_request(self, ev) -> None:
        """E_1: một yêu cầu mới xuất hiện tại thời điểm τ_r."""
        p = ev.payload
        veh = self._free_vehicle()
        if veh is None:
            # Không có xe rảnh: yêu cầu vào hàng đợi chờ (mục 2.2.2).
            # Yêu cầu này *chưa* bị từ chối — nó sẽ được giao khi có xe rảnh.
            self.pending.append(p)
            self.solution.unassigned.add(p)
            return

        self._assign(veh, p)
        if self.config.reoptimize_on_arrival:
            self._reoptimize()

    def _handle_vehicle_free(self, ev) -> None:
        """E_2: một phương tiện hoàn thành chuyến và trở nên rảnh.

        Các yêu cầu xe vừa phục vụ xong được gỡ khỏi lộ trình (chúng không
        còn là "phần lộ trình" của xe nữa) và chuyển sang tập *đã hoàn thành*.
        Quãng đường đã thực thi được tính theo đúng thứ tự đi của xe:
        kho → lấy₁ → giao₁ → lấy₂ → … → kho (công thức 1.4).
        """
        veh = self.vehicles[ev.payload]
        sol = self.solution

        # Quãng đường của chuyến vừa hoàn thành, theo thứ tự thực thi.
        self.executed_distance += self._trip_distance(veh.stops)

        # Gỡ các yêu cầu vừa hoàn thành khỏi lộ trình của xe.
        for p in list(veh.stops):
            d = self.inst.delivery_of(p)
            for k, route in enumerate(sol.routes):
                if p in route.stops and d in route.stops:
                    route.remove_request(p, d)
                    break
            self.completed.add(p)
        veh.committed += len(veh.stops)
        veh.stops.clear()
        veh.position = 0

        if self.pending:
            p = self.pending.pop(0)
            self._assign(veh, p)

    def _handle_optimization_end(self, ev) -> None:
        """E_3: hết ngân sách tái tối ưu của một chu kỳ."""
        # Chu kỳ đã kết thúc trong `_reoptimize`; sự kiện này giữ vai trò mốc
        # thời gian trong hàng đợi, đảm bảo luồng sự kiện rõ ràng.
        pass

    def _handle_simulation_end(self, ev) -> None:
        """E_4: kết thúc mô phỏng."""
        pass

    # -------------------------------------------------------------- trợ giúp
    def _free_vehicle(self) -> _Vehicle | None:
        """Xe rảnh đầu tiên, hoặc None nếu tất cả đang chạy."""
        for veh in self.vehicles:
            if veh.free:
                return veh
        return None

    def _assign(self, veh: _Vehicle, p: int) -> bool:
        """Giao yêu cầu `p` cho phương tiện `veh`; trả về True nếu thành công.

        Sau khi nhận yêu cầu, xe lên lịch sự kiện E_2 (hoàn thành chặng) tại
        thời điểm xe sẽ quay về kho.
        """
        d = self.inst.delivery_of(p)
        sol = self.solution
        sol.unassigned.discard(p)

        # Chèn vào xe `veh`; nếu không khả thi thì thử xe khác.
        for k, route in enumerate(sol.routes):
            if k != veh.index and not self.vehicles[k].free:
                continue
            v = route.best_insertion(p, d)
            if v is not None:
                route.insert(p, d, v[1], v[2])
                # `stops` lưu id *yêu cầu* (nút lấy), không phải nút giao.
                veh.stops.append(p)
                self.freezing.assign(veh.index, p)
                # E_2: xe hoàn thành chặng và trở nên rảnh.
                self._schedule_finish(veh)
                return True

        # Không xe nào khả thi: giữ yêu cầu ở hàng đợi chờ. Nếu đến cuối
        # mô phỏng vẫn chưa được giao thì nó bị từ chối.
        self.pending.insert(0, p)
        sol.unassigned.add(p)
        return False

    def _reoptimize(self) -> None:
        """Chạy một chu kỳ tái tối ưu ALNS trên lời giải hiện tại.

        Nếu bật cơ chế đóng băng (mục 2.2.3), ALNS chỉ được thay đổi phần lộ
        trình *chưa cam kết* của mỗi xe.
        """
        if self.solution is None:
            return
        cfg = self.config

        constraint = None
        if cfg.use_freezing:
            # Chân trời đóng băng: các nút đã cam kết của mỗi xe.
            for veh in self.vehicles:
                if veh.stops:
                    self.freezing.commit(veh.index, veh.committed)
            constraint = self.freezing.constraint(self.solution)

        before_signature = tuple(tuple(route.stops)
                                 for route in self.solution.routes)
        before_cost = self.solution.cost
        engine = ALNSEngine(self.inst, self.params, cfg.alns_config(),
                            constraint=constraint, seed=cfg.seed)
        best, _ = engine.run(self.solution)
        self.solution = best
        self.reoptimizations += 1
        after_signature = tuple(tuple(route.stops)
                                for route in self.solution.routes)
        if after_signature != before_signature:
            self.route_changes += 1
        if self.solution.cost < before_cost - 1e-9:
            self.improved_reoptimizations += 1

        # Đồng bộ trạng thái "yêu cầu đang chạy" của từng xe với lời giải mới:
        # ALNS có thể đã di dời yêu cầu giữa các xe, nên phải xác định lại
        # yêu cầu nào còn nằm trong phần lộ trình *chưa cam kết* của xe.
        for veh in self.vehicles:
            if not veh.stops:
                continue
            still_assigned = []
            for p in veh.stops:
                d = self.inst.delivery_of(p)
                if any(p in r.stops and d in r.stops for r in self.solution.routes):
                    still_assigned.append(p)
                else:
                    # ALNS đã loại yêu cầu này khỏi lời giải: xe không còn
                    # mang nó, nên không được tính quãng đường khi hoàn thành.
                    self.solution.unassigned.add(p)
            veh.stops = still_assigned

    # ----------------------------------------------------------------- chạy
    def run(self) -> SimResult:
        """Chạy mô phỏng đến khi hết thời gian; trả về kết quả."""
        t0 = _time.perf_counter()
        self._setup()

        handlers = {
            EventType.NEW_REQUEST: self._handle_new_request,
            EventType.VEHICLE_FREE: self._handle_vehicle_free,
            EventType.OPTIMIZATION_END: self._handle_optimization_end,
            EventType.SIMULATION_END: self._handle_simulation_end,
        }

        while True:
            ev = self.queue.pop()
            if ev is None:
                break
            handlers[ev.type](ev)
            if ev.type is EventType.SIMULATION_END:
                break

        sol = self.solution
        # Yêu cầu đã hoàn thành không còn nằm trong lộ trình, nên `served`
        # của lời giải không phản ánh đúng tổng số yêu cầu đã phục vụ.
        served = len(self.completed) + sol.n_served
        # Yêu cầu còn nằm trong hàng đợi chờ khi mô phỏng kết thúc cũng bị
        # tính là từ chối (không kịp phục vụ).
        rejected = len(sol.unassigned)
        # Quãng đường (1.4): phần đã thực thi + phần lộ trình còn lại.
        total_distance = self.executed_distance + sol.distance
        return SimResult(
            best_cost=sol.cost,
            served=served,
            rejected=rejected,
            total_distance=total_distance,
            total_lateness=sol.lateness,
            vehicles_used=sol.vehicles_used,
            reoptimizations=self.reoptimizations,
            route_changes=self.route_changes,
            improved_reoptimizations=self.improved_reoptimizations,
            seconds=_time.perf_counter() - t0,
            solution=sol,
        )