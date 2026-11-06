"""Toán tử phá huỷ và sửa chữa của ALNS (mục 2.1.3 – 2.1.4 của báo cáo).

Phá huỷ (Bảng 2.1):
    random   – loại ngẫu nhiên ν yêu cầu (chi phí O(ν))
    worst    – loại yêu cầu có mức tiết kiệm chi phí lớn nhất (2.2)
    related  – loại yêu cầu liên quan cao nhất với tập đã loại (Shaw, 2.3)

Sửa chữa (Bảng 2.2):
    greedy      – chèn tham lam theo Δ f nhỏ nhất
    regret2     – chèn theo tiêu chí hối tiếc bậc g (2.4)
    greedy_noise– chèn tham lam có nhiễu (2.5)

Mọi toán tử đều tôn trọng vùng tự do: `Route.best_insertion(min_pos=...)` khoá
phần lộ trình đã đóng băng, và `remove_request` chỉ được gọi với yêu cầu nằm
trọn trong vùng tự do (theo Mệnh đề 2.3).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from ..instance import Instance
from ..solution import Solution

# --------------------------------------------------------------- phá huỷ
DestroyFn = Callable[[Solution, random.Random, "ALNSConfig", "FreeContext"], list[int]]
#: Trả về danh sách id nút lấy của các yêu cầu bị loại khỏi lời giải.


@dataclass
class FreeContext:
    """Thông tin về vùng tự do do cơ chế đóng băng (mục 2.2.3) cung cấp.

    Attributes:
        min_pos: map {xe k -> số nút tiền tố đã đóng băng}. Chèn vào vị trí i
            với i < min_pos[k] là vi phạm cam kết, nên toán tử sửa chữa bị chặn.
        free_map: map {xe k -> tập nút thuộc vùng tự do}. Rỗng nghĩa là không
            có ràng buộc đóng băng (toàn bộ lộ trình tự do).
    """

    min_pos: dict[int, int] = field(default_factory=dict)
    free_map: dict[int, set[int]] = field(default_factory=dict)

    @property
    def constrained(self) -> bool:
        return bool(self.free_map)

    def min_pos_for(self, k: int) -> int:
        return self.min_pos.get(k, 0)

    def free_requests(self, sol: Solution) -> list[int]:
        """Yêu cầu có CẢ điểm lấy và điểm giao đều nằm trong vùng tự do.

        Theo mục 2.2.3: "Đơn vị bị loại trong toán tử phá huỷ là yêu cầu tự do
        R_free, gồm các yêu cầu mà cả điểm lấy và điểm giao đều nằm trong
        phần tự do."
        """
        out = []
        for p in sorted(sol.served_requests):
            d = sol.inst.delivery_of(p)
            for k, stops in self.free_map.items():
                if p in stops and d in stops:
                    out.append(p)
                    break
        return out



def destroy_random(sol: Solution, rng: random.Random,
                   config=None, ctx: "FreeContext | None" = None) -> list[int]:
    """Loại ngẫu nhiên ν yêu cầu (chi phí O(ν))."""
    candidates = (ctx.free_requests(sol) if ctx is not None and ctx.constrained
                  else sorted(sol.served_requests))
    if not candidates:
        return []
    xi = config.destroy_fraction if config else 0.4
    cap = config.max_destroy if config else 100
    n_max = min(cap, int(math.floor(xi * len(sol.inst.requests))))
    n_max = max(1, min(n_max, len(candidates)))
    nu = rng.randint(1, n_max)
    return rng.sample(candidates, nu)


def destroy_worst(sol: Solution, rng: random.Random,
                  config=None, ctx: "FreeContext | None" = None) -> list[int]:
    """Loại yêu cầu có mức tiết kiệm chi phí lớn nhất (công thức 2.2).

    Δf_r^- = f(s) − f(s \\ r).  Yêu cầu có Δf_r^- lớn là "đắt" nhất nên bị loại
    trước.  Để tránh luôn chọn cùng một tập, phần tử ở vị trí ⌊y·p·|L|⌋ của
    danh sách đã sắp xếp được chọn, với y ~ U[0,1) và p = 3 theo [8].
    """
    candidates = (ctx.free_requests(sol) if ctx is not None and ctx.constrained
                  else sorted(sol.served_requests))
    if not candidates:
        return []

    xi = config.destroy_fraction if config else 0.4
    cap = config.max_destroy if config else 100
    p = config.p_worst if config else 3
    n_max = max(1, min(cap, int(math.floor(xi * len(sol.inst.requests)))))

    savings: list[tuple[float, int]] = []
    for p_id in candidates:
        d = sol.inst.delivery_of(p_id)
        before = sol.cost
        removed = _remove_temporarily(sol, p_id, d)
        if removed is None:
            continue
        after = sol.cost
        _restore_temporarily(sol, removed)
        savings.append((before - after, p_id))
    if not savings:
        return []

    savings.sort(key=lambda x: -x[0])          # tiết kiệm lớn trước
    nu = min(n_max, len(savings))
    removed: list[int] = []
    while len(removed) < nu and savings:
        y = rng.random()
        idx = min(len(savings) - 1, int(y * p * len(savings)))
        _, p_id = savings.pop(idx)
        removed.append(p_id)
    return removed


def destroy_related(sol: Solution, rng: random.Random,
                     config=None, ctx: "FreeContext | None" = None) -> list[int]:
    """Loại liên quan (Shaw): chọn hạt giống rồi loại các yêu cầu liên quan nhất.

    Độ liên quan (công thức 2.3):
        R_{r,r'} = ω_1·d_{r,r'} + ω_2·|T_r − T_{r'}| + ω_3·|q_r − q_{r'}|
                   + ω_4·(1 − |K_r ∩ K_{r'}| / min(|K_r|, |K_{r'}|))
    Các thành phần được chuẩn hoá về [0,1]; (ω_1..ω_4) = (9,3,2,5) theo [8].
    """
    candidates = (ctx.free_requests(sol) if ctx is not None and ctx.constrained
                  else sorted(sol.served_requests))
    if not candidates:
        return []

    xi = config.destroy_fraction if config else 0.4
    cap = config.max_destroy if config else 100
    p = config.p_related if config else 6
    n_max = max(1, min(cap, int(math.floor(xi * len(sol.inst.requests)))))

    w1 = config.omega_distance if config else 9.0
    w2 = config.omega_time if config else 3.0
    w3 = config.omega_demand if config else 2.0
    w4 = config.omega_vehicle if config else 5.0

    seed_req = rng.choice(candidates)
    related = [seed_req]
    remaining = [x for x in candidates if x != seed_req]
    # K_r (tập xe có thể phục vụ r) là thành phần ω_4 của (2.3). Chỉ tính khi
    # thật sự cần (lazy) vì best_insertion/can_serve không rẻ.
    vehicles: dict[int, set[int]] = {}
    norms = _normalizers(sol.inst)
    while remaining and len(related) < n_max:
        y = rng.random()
        idx = min(len(remaining) - 1, int(y * p * len(remaining)))
        # chọn phần tử liên quan nhất với tập đã loại
        best_i, best_r = 0, float("inf")
        for i, cand in enumerate(remaining):
            rel = _relatedness(sol, cand, related, w1, w2, w3, w4, vehicles, norms)
            if rel < best_r:
                best_r, best_i = rel, i
        related.append(remaining.pop(best_i))
    return related[:n_max]


def _normalizers(inst: Instance) -> dict[str, float]:
    """Các đại lượng chuẩn hoá của (2.3), tính một lần cho cả thể hiện."""
    nodes = inst.nodes
    return {
        "dmax": max(1.0, _max_distance(inst)),
        "tmax": max(1.0, nodes[0].l),
        "qmax": max(1.0, max(abs(n.demand) for n in nodes)),
    }


def _relatedness(sol: Solution, r: int, ref: list[int],
                 w1: float, w2: float, w3: float, w4: float,
                 vehicles: dict[int, set[int]] | None = None,
                 norms: dict[str, float] | None = None) -> float:
    """Độ liên quan giữa yêu cầu r và tập tham chiếu (công thức 2.3)."""
    inst = sol.inst
    node = inst.nodes
    n_r, id_r = node[r], inst.delivery_of(r)
    n_d = node[id_r]
    if norms is None:
        norms = _normalizers(inst)
    dmax, tmax, qmax = norms["dmax"], norms["tmax"], norms["qmax"]

    total = 0.0
    for r2 in ref:
        id_d2 = inst.delivery_of(r2)
        n_r2, n_d2 = node[r2], node[id_d2]
        dist = math.dist((n_r.x, n_r.y), (n_d.x, n_d.y))
        time_diff = abs(n_r.e - n_r2.e) + abs(n_d.e - n_d2.e)
        dem_diff = abs(abs(n_r.demand) - abs(n_d2.demand))
        if vehicles is None:
            kr = _candidate_vehicles(sol, r)
            kr2 = _candidate_vehicles(sol, r2)
        else:
            if r not in vehicles:
                vehicles[r] = _candidate_vehicles(sol, r)
            if r2 not in vehicles:
                vehicles[r2] = _candidate_vehicles(sol, r2)
            kr, kr2 = vehicles[r], vehicles[r2]
        if kr and kr2:
            overlap = len(kr & kr2) / min(len(kr), len(kr2))
        else:
            overlap = 1.0
        total += (w1 * dist / dmax + w2 * time_diff / tmax
                  + w3 * dem_diff / qmax + w4 * (1.0 - overlap))
    return total / max(1, len(ref))


def _max_distance(inst: Instance) -> float:
    return max((max(row) for row in inst.dist), default=1.0)


def _candidate_vehicles(sol: Solution, p: int) -> set[int]:
    """Tập xe K_r có thể phục vụ r (dùng cho thành phần ω_4 của (2.3)).

    Dùng `Route.can_serve` — điều kiện khả thi sơ bộ O(1) — thay vì
    `best_insertion` (O(m²)), vì K_r chỉ cần là *superset* của tập xe thực sự
    khả thi: nó đóng vai trò trọng số tương đối trong độ liên quan.
    """
    d = sol.inst.delivery_of(p)
    return {k for k, route in enumerate(sol.routes) if route.can_serve(p, d)}


# ------------------------------------------------------- trợ giúp loại tạm
def _remove_temporarily(sol: Solution, p: int, d: int):
    """Loại yêu cầu rồi trả về thông tin để khôi phục. None nếu không loại được."""
    for k, route in enumerate(sol.routes):
        if p in route.stops and d in route.stops:
            idx_p = route.stops.index(p)
            idx_d = route.stops.index(d)
            before = list(route.stops)
            route.remove_request(p, d)
            return (k, before, route)
    return None


def _restore_temporarily(sol: Solution, info) -> None:
    k, before, route = info
    route.stops = before
    route._refresh()


# --------------------------------------------------------------- sửa chữa
def repair_greedy(sol: Solution, removed: list[int], rng: random.Random,
                  config=None, ctx: "FreeContext | None" = None) -> None:
    """Chèn tham lam: mỗi bước chọn cặp (r, k, ϖ) có Δ f nhỏ nhất.

    Yêu cầu không chèn được vào bất kỳ xe nào nào bị để lại ở trạng thái chưa
    phục vụ và bị phạt β trong hàm mục tiêu ("ngân hàng yêu cầu" theo [8]).
    """
    _repair(sol, removed, rng, config, ctx, regret_k=0, noise=0.0)


def repair_regret(sol: Solution, removed: list[int], rng: random.Random,
                  config=None, ctx: "FreeContext | None" = None) -> None:
    """Chèn theo tiêu chí hối tiếc bậc g (công thức 2.4)."""
    g = config.regret_k if config else 2
    _repair(sol, removed, rng, config, ctx, regret_k=g, noise=0.0)


def repair_greedy_noise(sol: Solution, removed: list[int], rng: random.Random,
                        config=None, ctx: "FreeContext | None" = None) -> None:
    """Chèn tham lam có nhiễu (công thức 2.5)."""
    eta = config.noise if config else 0.025
    _repair(sol, removed, rng, config, ctx, regret_k=0, noise=eta)


def _repair(sol: Solution, removed: list[int], rng: random.Random, config,
            ctx: "FreeContext | None", regret_k: int, noise: float) -> None:
    inst = sol.inst
    dmax = _max_distance(inst)
    pending = list(removed)

    def min_pos_for(k: int) -> int:
        return ctx.min_pos_for(k) if ctx is not None else 0

    while pending:
        best_pick = None      # (khóa chọn, p, k, i, j)
        if regret_k > 0:
            # hối tiếc: chọn yêu cầu có hối tiếc lớn nhất
            best_key = None
            for p in pending:
                d = inst.delivery_of(p)
                costs = []
                for k, route in enumerate(sol.routes):
                    v = route.best_insertion(p, d, min_pos=min_pos_for(k),
                                             noise=noise, rng=rng, dmax=dmax)
                    if v is not None:
                        costs.append((v[0], k, v[1], v[2]))
                if not costs:
                    continue
                costs.sort()
                regret = sum((costs[x][0] if x < len(costs) else math.inf)
                             - costs[0][0] for x in range(1, regret_k))
                key = (regret, -costs[0][0])
                if best_key is None or key > best_key:
                    best_key = key
                    best_pick = (p, costs[0][1], costs[0][2], costs[0][3])
        else:
            # tham lam: cặp (r, k, ϖ) có Δ f nhỏ nhất
            best_delta = math.inf
            for p in pending:
                d = inst.delivery_of(p)
                for k, route in enumerate(sol.routes):
                    v = route.best_insertion(p, d, min_pos=min_pos_for(k),
                                             noise=noise, rng=rng, dmax=dmax)
                    if v is not None and v[0] < best_delta:
                        best_delta = v[0]
                        best_pick = (p, k, v[1], v[2])

        if best_pick is None:
            break                       # không còn chỗ: giữ nguyên là bị từ chối
        p, k, i, j = best_pick
        d = inst.delivery_of(p)
        sol.routes[k].insert(p, d, i, j)
        sol.unassigned.discard(p)
        pending.remove(p)


# --------------------------------------------------------------- đăng ký
DESTROY_OPERATORS: dict[str, DestroyFn] = {
    "random": destroy_random,
    "worst": destroy_worst,
    "related": destroy_related,
}

REPAIR_OPERATORS: dict[str, Callable] = {
    "greedy": repair_greedy,
    "regret2": repair_regret,
    "greedy_noise": repair_greedy_noise,
}
