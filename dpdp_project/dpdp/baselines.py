"""Lời giải và các thuật toán chèn đối chứng (bước 3 trong kế hoạch).

- greedy_insertion : mỗi bước chọn cặp (yêu cầu, xe, vị trí) có Δ chi phí nhỏ nhất.
- regret_insertion : mỗi bước chèn yêu cầu có "hối tiếc bậc g" lớn nhất (g = 2 mặc định);
                     yêu cầu chỉ chèn được vào ít hơn g xe được ưu tiên (Ropke & Pisinger [8]).
- insert_request   : chèn MỘT yêu cầu mới vào lời giải hiện có; dùng lại ở
                     bước mô phỏng động và làm toán tử sửa chữa của ALNS.

Hiệu năng: lưu đệm Δ tốt nhất theo (yêu cầu, xe); sau mỗi lần chèn chỉ tính lại
cho đúng xe vừa thay đổi.
"""
from __future__ import annotations

from .instance import Instance
from .route import INF, Params, Route


class Solution:
    def __init__(self, inst: Instance, params: Params, num_vehicles: int | None = None):
        self.inst = inst
        self.params = params
        k = inst.num_vehicles if num_vehicles is None else num_vehicles
        self.routes = [Route(inst, params) for _ in range(k)]
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
        p = self.params
        return (p.alpha * self.distance + p.gamma * self.lateness
                + p.beta * len(self.unassigned))

    def as_lists(self) -> list[list[int]]:
        return [list(r.stops) for r in self.routes]

    def copy(self) -> "Solution":
        s = Solution.__new__(Solution)
        s.inst, s.params = self.inst, self.params
        s.routes = [r.copy() for r in self.routes]
        s.unassigned = set(self.unassigned)
        return s


def insert_request(sol: Solution, p: int):
    """Chèn yêu cầu p vào vị trí rẻ nhất trong mọi xe. Trả về (k, Δ) hoặc None."""
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


def _sequential_insertion(sol: Solution, pending: list[int], select) -> Solution:
    inst = sol.inst
    cache: dict[tuple[int, int], tuple | None] = {}

    def refresh(k: int, reqs: list[int]) -> None:
        route = sol.routes[k]
        for r in reqs:
            cache[(r, k)] = route.best_insertion(r, inst.delivery_of(r))

    for k in range(len(sol.routes)):
        refresh(k, pending)

    n_routes = len(sol.routes)
    while pending:
        choice = select(pending, cache, n_routes)
        if choice is None:
            break
        r, k, i, j = choice
        sol.routes[k].insert(r, inst.delivery_of(r), i, j)
        pending.remove(r)
        for kk in range(n_routes):            # bỏ đệm của yêu cầu đã chèn
            cache.pop((r, kk), None)
        refresh(k, pending)
    sol.unassigned |= set(pending)
    return sol


def _select_greedy(pending, cache, n_routes):
    best = None
    for r in pending:
        for k in range(n_routes):
            v = cache[(r, k)]
            if v is not None and (best is None or v[0] < best[0]):
                best = (v[0], r, k, v[1], v[2])
    return None if best is None else best[1:]


def _make_select_regret(g: int):
    def select(pending, cache, n_routes):
        pick, pick_key = None, None
        for r in pending:
            costs = sorted((cache[(r, k)][0], k) for k in range(n_routes)
                           if cache[(r, k)] is not None)
            if not costs:
                continue
            # thiếu lựa chọn -> coi chi phí còn thiếu là vô hạn (ưu tiên chèn trước)
            regret = sum((costs[x][0] if x < len(costs) else INF) - costs[0][0]
                         for x in range(1, g))
            key = (regret, -costs[0][0])
            if pick_key is None or key > pick_key:
                _, k = costs[0]
                _, i, j = cache[(r, k)]
                pick, pick_key = (r, k, i, j), key
        return pick
    return select


def greedy_insertion(inst: Instance, params: Params, requests=None,
                     solution: Solution | None = None,
                     num_vehicles: int | None = None) -> Solution:
    sol = solution or Solution(inst, params, num_vehicles)
    pending = list(inst.requests if requests is None else requests)
    return _sequential_insertion(sol, pending, _select_greedy)


def regret_insertion(inst: Instance, params: Params, requests=None,
                     solution: Solution | None = None,
                     num_vehicles: int | None = None, g: int = 2) -> Solution:
    sol = solution or Solution(inst, params, num_vehicles)
    pending = list(inst.requests if requests is None else requests)
    return _sequential_insertion(sol, pending, _make_select_regret(g))
