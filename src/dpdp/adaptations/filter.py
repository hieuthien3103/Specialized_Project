"""Bộ lọc ứng viên theo độ lệch tuyến và hướng di chuyển (mục 2.2.4).

Khi tìm vị trí chèn cho một yêu cầu, thay vì xét mọi cặp (xe, vị trí chèn)
— phép toán O(m²) với m = số nút của lộ trình — bộ lọc này chỉ xét những
ứng viên *có khả năng* hợp lý, dựa trên:

  * **độ lệch tuyến**: khoảng cách giữa điểm lấy và điểm giao của yêu cầu so
    với đường đi hiện tại của phương tiện, không vượt quá `δ_max`;
  * **hướng di chuyển**: góc giữa vector hướng hiện tại của phương tiện và
    vector tới điểm lấy, không vượt quá `φ_max`.

Mục tiêu của H2 là giảm thời gian tính toán trung bình mỗi quyết định mà
không làm suy giảm đáng kể chất lượng lời giải.

Bộ lọc là *phần thích ứng* của đề tài, được cài trên khung ALNS của thư viện
`alns` (Wouda & Lan [20]) thông qua tham số `min_pos`/`free_map` mà các toán
tử đã hỗ trợ, và thông qua một bộ chèn tùy biến cho `Route.best_insertion`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class FilterConfig:
    """Tham số bộ lọc ứng viên (mục 2.2.4).

    Attributes:
        delta_max: δ_max — ngưỡng độ lệch tuyến tối đa (0 = không lọc).
        phi_max: φ_max — ngưỡng góc hướng tối đa, tính bằng độ (0 = không lọc).
        radius: r_0 — bán kính miễn lọc quanh phương tiện (0 = không miễn).
        kappa: κ — số ứng viên tối đa được xét cho mỗi yêu cầu.
    """

    delta_max: float = 0.0
    phi_max: float = 0.0
    radius: float = 0.0
    kappa: int = 5

    @property
    def active(self) -> bool:
        """Bộ lọc có đang hoạt động hay không."""
        return (self.delta_max > 0.0 or self.phi_max > 0.0
                or self.radius > 0.0)


def _angle_between(u: tuple[float, float], v: tuple[float, float]) -> float:
    """Góc (độ) giữa hai vector 2D, trong [0, 180]."""
    nu = math.hypot(*u)
    nv = math.hypot(*v)
    if nu < 1e-12 or nv < 1e-12:
        return 0.0
    cos = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))


@dataclass
class CandidateFilter:
    """Bộ lọc ứng viên cho thao tác chèn.

    Attributes:
        cfg: tham số bộ lọc.
        nodes: mảng nút của thể hiện (dùng để lấy toạ độ).
        dist: ma trận khoảng cách.
    """

    cfg: FilterConfig
    nodes: list
    dist: list
    #: Số ứng viên đã bị loại và số lần gọi bộ lọc (để báo cáo H2).
    filtered_out: int = 0
    total_checked: int = 0
    _cache: dict = field(default_factory=dict, repr=False)

    # -------------------------------------------------------------- hàm chính
    def accepts(self, vehicle_pos: tuple[float, float],
                heading: tuple[float, float],
                pickup_xy: tuple[float, float],
                delivery_xy: tuple[float, float]) -> bool:
        """Quyết định một ứng viên có được xét hay không.

        Args:
            vehicle_pos: toạ độ hiện tại của phương tiện.
            heading: vector hướng di chuyển hiện tại.
            pickup_xy: toạ độ điểm lấy.
            delivery_xy: toạ độ điểm giao.
        """
        cfg = self.cfg
        if not cfg.active:
            return True

        self.total_checked += 1

        # (1) Miễn lọc trong bán kính r_0 quanh phương tiện.
        if cfg.radius > 0.0:
            if math.dist(vehicle_pos, pickup_xy) <= cfg.radius:
                return True

        # (2) Ngưỡng góc hướng φ_max.
        if cfg.phi_max > 0.0:
            to_pickup = (pickup_xy[0] - vehicle_pos[0],
                         pickup_xy[1] - vehicle_pos[1])
            phi = _angle_between(heading, to_pickup)
            if phi > cfg.phi_max:
                self.filtered_out += 1
                return False

        # (3) Ngưỡng độ lệch tuyến δ_max.
        #
        # Công thức (2.21) định nghĩa độ lệch của một *điểm* u là chi phí
        # vòng tránh nhỏ nhất khi chèn u vào một khe của lộ trình:
        #     δ_ku = min_i ( d_{w_i,u} + d_{u,w_{i+1}} − d_{w_i,w_{i+1}} )
        #
        # Ở đây ta dùng biến thể theo *cặp* điểm lấy–giao của yêu cầu, so với
        # đường đi trực tiếp hiện tại của xe:
        #     detour = d(p_k, u_r) + d(u_r, v_r) − d(p_k, v_r)
        # Cặp nằm sát tuyến thì detour nhỏ; cặp lệch xa thì detour lớn.
        if cfg.delta_max > 0.0:
            detour = self._detour(vehicle_pos, pickup_xy, delivery_xy)
            if detour > cfg.delta_max:
                self.filtered_out += 1
                return False

        return True

    # ------------------------------------------------------------ trợ giúp
    def _detour(self, vehicle_pos, pickup_xy, delivery_xy) -> float:
        """Độ lệch tuyến của cặp điểm lấy–giao so với đường đi trực tiếp.

        `d(p_k, u_r) + d(u_r, v_r) − d(p_k, v_r)` — độ dài thừa do phải rẽ qua
        điểm lấy, so với việc đi thẳng tới điểm giao.
        """
        direct = math.dist(vehicle_pos, delivery_xy)
        via = (math.dist(vehicle_pos, pickup_xy)
               + math.dist(pickup_xy, delivery_xy))
        return via - direct

    def stats(self) -> dict:
        """Thống kê hiệu quả của bộ lọc (dùng cho H2)."""
        checked = max(1, self.total_checked)
        return {
            "checked": self.total_checked,
            "filtered_out": self.filtered_out,
            "keep_ratio": round(1.0 - self.filtered_out / checked, 4),
        }
