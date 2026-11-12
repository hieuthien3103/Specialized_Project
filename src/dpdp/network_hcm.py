"""Nạp bộ yêu cầu mô phỏng trên mạng đường đô thị TP.HCM.

Nguồn vào là cặp tệp do ``prepare_hcm_osm.py`` sinh: ma trận đường đi ngắn
nhất ``.npz`` (km/phút) và danh sách yêu cầu ``.csv``. Hàm nạp giữ nguyên ma
trận mạng thay vì thay bằng khoảng cách Euclid, nhờ đó dữ liệu HCM có thể dùng
trực tiếp bởi cùng ALNS/DES với Li & Lim.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .core.instance import Instance, Node


def load_hcm_instance(matrix_file: str | Path, requests_file: str | Path,
                      *, name: str | None = None, num_vehicles: int = 10,
                      capacity: float = 200.0, horizon: float = 480.0
                      ) -> tuple[Instance, dict[int, float]]:
    """Nạp một thể hiện HCM và release scenario đi kèm.

    ``tau_r`` trong CSV trở thành release time của điểm lấy tương ứng. Đơn vị
    khoảng cách là km, thời gian là phút; service/time-window vì vậy đều giữ
    nguyên đơn vị phút.
    """
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - numpy đi cùng alns
        raise RuntimeError("Cần numpy để nạp dữ liệu mạng HCM") from exc

    matrix_path, request_path = Path(matrix_file), Path(requests_file)
    with np.load(matrix_path) as matrices:
        dist = matrices["dist_km"]
        travel_time = matrices["time_min"]
        coords = matrices["coords_lat_lon"]
    if dist.ndim != 2 or dist.shape != travel_time.shape or dist.shape[0] != dist.shape[1]:
        raise ValueError("ma trận HCM phải vuông và có cùng kích thước")
    if len(coords) != dist.shape[0]:
        raise ValueError("số toạ độ không khớp ma trận HCM")

    with request_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("CSV yêu cầu HCM rỗng")
    required = {"req_id", "pickup_matrix_idx", "delivery_matrix_idx", "demand",
                "service_time", "e_pickup", "l_pickup", "e_delivery",
                "l_delivery", "tau_r"}
    if required - set(rows[0]):
        raise ValueError(f"CSV HCM thiếu cột: {sorted(required - set(rows[0]))}")

    n = dist.shape[0]
    nodes: list[Node | None] = [None] * n
    lat0, lon0 = coords[0]
    nodes[0] = Node(0, float(lon0), float(lat0), 0.0, 0.0, horizon, 0.0, 0, 0)
    release: dict[int, float] = {}
    seen_pickups: set[int] = set()
    for row in rows:
        request_id = int(row["req_id"])
        p, d = int(row["pickup_matrix_idx"]), int(row["delivery_matrix_idx"])
        if not (0 < p < n and 0 < d < n) or p == d:
            raise ValueError(f"request {request_id}: chỉ số ma trận không hợp lệ")
        if p in seen_pickups or nodes[p] is not None or nodes[d] is not None:
            raise ValueError(f"request {request_id}: trùng nút lấy/giao")
        seen_pickups.add(p)
        plat, plon = coords[p]
        dlat, dlon = coords[d]
        demand, service = float(row["demand"]), float(row["service_time"])
        nodes[p] = Node(p, float(plon), float(plat), demand,
                        float(row["e_pickup"]), float(row["l_pickup"]), service,
                        0, d)
        nodes[d] = Node(d, float(dlon), float(dlat), -demand,
                        float(row["e_delivery"]), float(row["l_delivery"]), service,
                        p, 0)
        release[p] = float(row["tau_r"])
    if any(node is None for node in nodes):
        raise ValueError("CSV yêu cầu không phủ hết các nút của ma trận HCM")

    instance = Instance(name or matrix_path.stem, num_vehicles, capacity, 1.0,
                        nodes, distance_matrix=dist.tolist(),
                        travel_time_matrix=travel_time.tolist())
    return instance, release
