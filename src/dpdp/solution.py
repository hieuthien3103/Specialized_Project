"""Lời giải của bài toán DPDP: tập lộ trình của các xe + tập yêu cầu bị từ chối.

Đây là lớp dữ liệu trung tâm dùng chung cho:
  - các thuật toán chèn đối chứng (`baselines.py`),
  - engine ALNS (`alns/engine.py`),
  - khung mô phỏng sự kiện rời rạc (`des/simulator.py`).

Tách riêng khỏi `baselines.py` để mã lõi ALNS không phụ thuộc vào mã đối chứng.
"""
from __future__ import annotations

from .instance import Instance
from .route import Params, Route


class Solution:
    """Một lời giải: `num_vehicles` lộ trình + tập yêu cầu bị từ chối.

    Quy ước:
      - `routes[k].stops` là chuỗi nút đã phục vụ của xe k, theo thứ tự thời gian;
      - `unassigned` chứa id của nút LẤY của các yêu cầu bị từ chối;
      - mỗi yêu cầu phải thuộc đúng một trong hai trạng thái: đã phục vụ hoặc bị từ chối.
    """

    def __init__(self, inst: Instance, params: Params, num_vehicles: int | None = None):
        self.inst = inst
        self.params = params
        k = inst.num_vehicles if num_vehicles is None else num_vehicles
        self.num_vehicles = k
        self.routes: list[Route] = [Route(inst, params) for _ in range(k)]
        self.unassigned: set[int] = set()     # id nút lấy của yêu cầu bị từ chối

    # --- chỉ số ---
    @property
    def distance(self) -> float:
        return sum(r.total_dist for r in self.routes)

    @property
    def lateness(self) -> float:
        return sum(r.total_late for r in self.routes)

    @property
    def vehicles_used(self) -> int:
        return sum(1 for r in self.routes if r.stops)

    @property
    def n_served(self) -> int:
        return sum(len(r.stops) for r in self.routes) // 2

    @property
    def cost(self) -> float:
        """Hàm mục tiêu (công thức 2.1): α·quãng đường + γ·độ trễ + β·số yêu cầu từ chối."""
        p = self.params
        return (p.alpha * self.distance + p.gamma * self.lateness
                + p.beta * len(self.unassigned))

    @property
    def served_requests(self) -> set[int]:
        """Tập id nút lấy của các yêu cầu đang được phục vụ."""
        return {nid for r in self.routes for nid in r.stops
                if self.inst.nodes[nid].is_pickup}

    def as_lists(self) -> list[list[int]]:
        return [list(r.stops) for r in self.routes]

    def copy(self) -> "Solution":
        s = Solution.__new__(Solution)
        s.inst, s.params = self.inst, self.params
        s.num_vehicles = self.num_vehicles
        s.routes = [r.copy() for r in self.routes]
        s.unassigned = set(self.unassigned)
        return s

    def __repr__(self) -> str:  # pragma: no cover - phục vụ ghi log
        return (f"<Solution served={self.n_served} rejected={len(self.unassigned)} "
                f"vehicles={self.vehicles_used} dist={self.distance:.2f} "
                f"cost={self.cost:.2f}>")


def insert_request(sol: Solution, p: int):
    """Chèn yêu cầu p vào vị trí rẻ nhất trong mọi xe.

    Trả về (k, Δ chi phí) nếu chèn được, None nếu không xe nào khả thi.
    """
    d = sol.inst.delivery_of(p)
    best = None
    for k, route in enumerate(sol.routes):
        v = route.best_insertion(p, d)
        if v is not None and (best is None or v[0] < best[0]):
            best = (v[0], k, v[1], v[2])
    if best is None:
        return None
    delta, k, i, j = best
    sol.routes[k].insert(p, d, i, j)
    sol.unassigned.discard(p)
    return k, delta
