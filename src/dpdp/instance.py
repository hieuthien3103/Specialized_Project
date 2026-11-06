"""Dữ liệu bài toán PDPTW / DPDP.

Định dạng file Li & Lim (SINTEF TOP), các trường cách nhau bằng tab/khoảng trắng:

    dòng 1 :  K  Q  S                       (số xe, sức chứa, tốc độ)
    dòng sau: ID X Y DEMAND EARLIEST LATEST SERVICE PICKUP DELIVERY

- Nút 0 là kho.
- Nút lấy hàng: DELIVERY = id của nút giao tương ứng, PICKUP = 0.
- Nút giao hàng: PICKUP = id của nút lấy tương ứng, DELIVERY = 0, DEMAND < 0.
- Khoảng cách Euclid; thời gian di chuyển = khoảng cách / tốc độ.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    id: int
    x: float
    y: float
    demand: float
    e: float          # mở cửa sớm nhất
    l: float          # đóng cửa muộn nhất
    s: float          # thời gian phục vụ
    pickup: int       # với nút giao: id nút lấy tương ứng, ngược lại 0
    delivery: int     # với nút lấy: id nút giao tương ứng, ngược lại 0

    @property
    def is_pickup(self) -> bool:
        return self.delivery != 0

    @property
    def is_delivery(self) -> bool:
        return self.pickup != 0


class Instance:
    """Một thể hiện PDPTW: một kho, đội xe đồng nhất."""

    def __init__(self, name: str, num_vehicles: int, capacity: float,
                 speed: float, nodes: list[Node]):
        if not nodes or nodes[0].id != 0:
            raise ValueError("nodes[0] phải là kho (id = 0)")
        self.name = name
        self.num_vehicles = num_vehicles
        self.capacity = capacity
        self.speed = speed if speed > 0 else 1.0
        self.nodes = nodes
        self.dist = [[math.hypot(a.x - b.x, a.y - b.y) for b in nodes] for a in nodes]
        self.tt = [[d / self.speed for d in row] for row in self.dist]
        # mỗi yêu cầu được định danh bằng id nút lấy hàng
        self.requests: list[int] = [n.id for n in nodes if n.is_pickup]
        self._check()

    def delivery_of(self, p: int) -> int:
        return self.nodes[p].delivery

    @property
    def n_requests(self) -> int:
        return len(self.requests)

    def _check(self) -> None:
        for n in self.nodes[1:]:
            if n.is_pickup == n.is_delivery:
                raise ValueError(f"nút {n.id} vừa là/không là lấy và giao")
            if n.is_pickup:
                d = self.nodes[n.delivery]
                if d.pickup != n.id:
                    raise ValueError(f"cặp lấy–giao không khớp tại nút {n.id}")


# ----------------------------------------------------------------- đọc / ghi
def parse_lilim(path: str | Path, name: str | None = None) -> Instance:
    path = Path(path)
    rows = [ln.split() for ln in path.read_text().splitlines() if ln.strip()]
    k, q, s = int(rows[0][0]), float(rows[0][1]), float(rows[0][2])
    nodes: list[Node] = []
    for idx, r in enumerate(rows[1:]):
        if len(r) != 9:
            raise ValueError(f"dòng {idx + 2}: cần 9 trường, gặp {len(r)}")
        if int(r[0]) != idx:
            raise ValueError(f"dòng {idx + 2}: id {r[0]} không liên tục")
        x, y, dem, e, l, sv = map(float, r[1:7])
        nodes.append(Node(idx, x, y, dem, e, l, sv, int(r[7]), int(r[8])))
    return Instance(name or path.stem, k, q, s, nodes)


def write_lilim(inst: Instance, path: str | Path) -> None:
    lines = [f"{inst.num_vehicles}\t{inst.capacity:g}\t{inst.speed:g}"]
    for n in inst.nodes:
        lines.append("\t".join(str(v) for v in (
            n.id, n.x, n.y, n.demand, n.e, n.l, n.s, n.pickup, n.delivery)))
    Path(path).write_text("\n".join(lines) + "\n")


# ------------------------------------------------------ dữ liệu thử nghiệm
def generate_synthetic(n_requests: int, seed: int = 0, num_vehicles: int = 25,
                       capacity: float = 200.0, name: str | None = None) -> Instance:
    """Sinh thể hiện cùng định dạng Li & Lim để kiểm thử khi chưa có file thật.

    Mỗi yêu cầu đều khả thi khi đứng riêng (một xe phục vụ một mình).
    KHÔNG dùng để báo cáo kết quả; chỉ để gỡ lỗi.
    """
    rng = random.Random(seed)
    horizon = 2000.0
    service = 10.0
    nodes = [Node(0, 50.0, 50.0, 0.0, 0.0, horizon, 0.0, 0, 0)]

    def tt(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    depot = (50.0, 50.0)
    for r in range(1, n_requests + 1):
        p_xy = (rng.uniform(0, 100), rng.uniform(0, 100))
        q = float(rng.choice([10, 20, 30]))
        e_p = rng.uniform(0, 600)
        l_p = max(e_p + rng.uniform(60, 150), tt(depot, p_xy) + 1)
        nodes.append(Node(r, *p_xy, q, round(e_p, 2), round(l_p, 2), service,
                          0, n_requests + r))
    for r in range(1, n_requests + 1):
        p = nodes[r]
        d_xy = (rng.uniform(0, 100), rng.uniform(0, 100))
        e_d = p.e + service + tt((p.x, p.y), d_xy)
        l_d = max(e_d + rng.uniform(80, 200), p.l + service + tt((p.x, p.y), d_xy))
        nodes.append(Node(n_requests + r, *d_xy, -p.demand, round(e_d, 2),
                          round(l_d, 2), service, r, 0))
    return Instance(name or f"synth{n_requests}_s{seed}", num_vehicles, capacity, 1.0, nodes)


# ----------------------------------------------------------- động hoá (1.3.1)
def dynamize(inst: Instance, rho: float, lead_time: float = 0.0,
             seed: int = 0) -> dict[int, float]:
    """Gán thời điểm xuất hiện τ_r cho từng yêu cầu (khoá = id nút lấy).

    Một tỷ lệ ρ yêu cầu được chọn ngẫu nhiên làm yêu cầu động, τ_r được rút
    đều trong [0, l_p − t(0,p) − Λ]; số còn lại có τ_r = 0.
    LƯU Ý: hãy đối chiếu công thức này với công thức ở mục 1.3.1 của báo cáo
    và sửa cho khớp nếu khác.
    """
    rng = random.Random(seed)
    reqs = inst.requests
    chosen = set(rng.sample(range(len(reqs)), round(rho * len(reqs))))
    release: dict[int, float] = {}
    for idx, p in enumerate(reqs):
        if idx in chosen:
            hi = inst.nodes[p].l - inst.tt[0][p] - lead_time
            release[p] = rng.uniform(0.0, hi) if hi > 0 else 0.0
        else:
            release[p] = 0.0
    return release


def degree_of_dynamism(release: dict[int, float]) -> float:
    """ρ thực tế = tỷ lệ yêu cầu có τ_r > 0 (Định nghĩa 1.3)."""
    return sum(1 for v in release.values() if v > 0) / max(1, len(release))
