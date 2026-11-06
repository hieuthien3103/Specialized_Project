"""Bộ kiểm tra lời giải ĐỘC LẬP với Route.

Cố ý không dùng lại mã của route.py để lỗi ở một nơi không che lỗi ở nơi kia.
Kiểm tra các điều kiện tương ứng (2.11)–(2.19) của báo cáo:
  phục vụ & ghép cặp, lấy trước giao, sức chứa, khung thời gian, về kho đúng hạn.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .instance import Instance
from .route import Params

TOL = 1e-6


@dataclass
class Report:
    ok: bool
    errors: list[str] = field(default_factory=list)
    distance: float = 0.0
    lateness: float = 0.0
    served: int = 0
    rejected: int = 0
    vehicles_used: int = 0

    def objective(self, params: Params) -> float:
        return (params.alpha * self.distance + params.gamma * self.lateness
                + params.beta * self.rejected)


def validate(inst: Instance, routes: list[list[int]], params: Params,
             unassigned=()) -> Report:
    errors: list[str] = []
    nodes = inst.nodes
    n = len(nodes)
    seen: dict[int, int] = {}
    total_d = total_l = 0.0
    used = 0

    for ri, stops in enumerate(routes):
        if stops:
            used += 1
        for nid in stops:
            if not (1 <= nid < n):
                errors.append(f"xe {ri}: nút {nid} không hợp lệ")
            elif nid in seen:
                errors.append(f"nút {nid} bị thăm nhiều lần (xe {seen[nid]} và {ri})")
            else:
                seen[nid] = ri
        if errors:
            continue

        # ghép cặp & thứ tự lấy trước giao trong CÙNG một xe
        pos = {nid: k for k, nid in enumerate(stops)}
        for nid in stops:
            nd = nodes[nid]
            if nd.is_pickup:
                if nd.delivery not in pos:
                    errors.append(f"xe {ri}: có điểm lấy {nid} nhưng thiếu điểm giao {nd.delivery}")
                elif pos[nd.delivery] < pos[nid]:
                    errors.append(f"xe {ri}: điểm giao {nd.delivery} đứng trước điểm lấy {nid}")
            else:
                if nd.pickup not in pos:
                    errors.append(f"xe {ri}: có điểm giao {nid} nhưng thiếu điểm lấy {nd.pickup}")

        # mô phỏng thời gian
        prev, t, load = 0, nodes[0].e, 0.0
        for nid in stops:
            nd = nodes[nid]
            arr = max(t + inst.dist[prev][nid] / inst.speed, nd.e)
            load += nd.demand
            if load > inst.capacity + TOL:
                errors.append(f"xe {ri}: quá tải tại nút {nid} ({load:g} > {inst.capacity:g})")
            if load < -TOL:
                errors.append(f"xe {ri}: tải âm tại nút {nid}")
            over = arr - nd.l
            if nd.is_pickup:
                if over > TOL:
                    errors.append(f"xe {ri}: điểm lấy {nid} đến muộn {over:.3f}")
            else:
                if over > params.late_max + TOL:
                    errors.append(f"xe {ri}: điểm giao {nid} trễ {over:.3f} > L̄={params.late_max:g}")
                if over > 0:
                    total_l += over
            total_d += inst.dist[prev][nid]
            t, prev = arr + nd.s, nid
        if stops:
            back = t + inst.dist[prev][0] / inst.speed
            total_d += inst.dist[prev][0]
            if back > nodes[0].l + TOL:
                errors.append(f"xe {ri}: về kho lúc {back:.2f} > {nodes[0].l:g}")

    # mỗi yêu cầu hoặc được phục vụ hoặc bị từ chối, không cả hai / không thiếu
    rejected = set(unassigned)
    for p in inst.requests:
        d = inst.delivery_of(p)
        served = p in seen
        if served and d not in seen:
            errors.append(f"yêu cầu {p}: có điểm lấy mà thiếu điểm giao")
        if served and seen[p] != seen.get(d, -1):
            errors.append(f"yêu cầu {p}: điểm lấy và giao ở hai xe khác nhau")
        if served and p in rejected:
            errors.append(f"yêu cầu {p}: vừa được phục vụ vừa bị từ chối")
        if not served and p not in rejected:
            errors.append(f"yêu cầu {p}: không được phục vụ cũng không ghi nhận từ chối")

    n_served = sum(1 for p in inst.requests if p in seen)
    return Report(ok=not errors, errors=errors, distance=total_d, lateness=total_l,
                  served=n_served, rejected=len(rejected), vehicles_used=used)
