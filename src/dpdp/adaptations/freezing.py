"""Cơ chế đóng băng phần lộ trình đã cam kết (mục 2.2.3).

Khi một yêu cầu mới xuất hiện và được giao cho một phương tiện, phần lộ trình
mà xe đã cam kết thực hiện (những điểm đã "dứt" khỏi tay) **không được**
thay đổi trong chu kỳ tái tối ưu — nếu không thì cam kết với khách hàng
về thời gian phục vụ sẽ bị vi phạm.

Cơ chế này là một trong hai đóng góp còn lại của đề tài (đóng góp còn lại là
*cấu hình tham số* và *cách ghép với DES*). Nó được cài đặt trên trên khung
ALNS của thư viện `alns` (Wouda & Lan [20]) thông qua cơ chế `min_pos` mà
`Route.best_insertion` đã hỗ trợ.

Nguyên lý:

  * mỗi phương tiện k có một *chân trời đóng băng* `horizon[k]` — số nút đầu
    tiên của lộ trình đã cam kết;
  * toán tử sửa chữa chỉ được chèn ở vị trí `i ≥ horizon[k]`;
  * toán tử phá huỷ chỉ được loại những yêu cầu mà **cả** điểm lấy và điểm
    giao đều nằm sau chân trời (Mệnh đề 2.3).

Biên an toàn `H_0` (mục 2.2.3) cho phép mở băng sớm hơn một chút khi phần
lộ trình còn lại quá ngắn, tránh tình huống không còn vùng tự do để tối ưu.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..alns.operators import FreeContext
from ..core.solution import Solution


@dataclass
class FreezingConstraint:
    """Ràng buộc vùng tự do cho ALNS, sinh từ trạng thái cam kết của DES.

    Attributes:
        min_pos: map {xe k -> số nút tiền tố đã đóng băng} của xe k.
        free_map: map {xe k -> tập nút thuộc vùng tự do} của xe k.
        safety: H_0 — biên an toàn của chân trời đóng băng.
    """

    min_pos: dict[int, int] = field(default_factory=dict)
    free_map: dict[int, set[int]] = field(default_factory=dict)
    safety: float = 0.0

    def context(self, sol: Solution) -> FreeContext:
        """Sinh `FreeContext` mà các toán tử của ALNS dùng."""
        return FreeContext(min_pos=dict(self.min_pos),
                           free_map={k: set(v) for k, v in self.free_map.items()})

    def is_constrained(self) -> bool:
        return bool(self.min_pos)


@dataclass
class VehicleCommitment:
    """Trạng thái cam kết của một phương tiện trong mô phỏng."""

    index: int
    #: Các yêu cầu đã giao cho xe (theo thứ tự thời gian).
    assigned: list[int] = field(default_factory=list)
    #: Số nút đầu tiên của lộ trình đã cam kết (chân trời đóng băng).
    horizon: int = 0
    #: Số nút cam kết tính từ đầu lộ trình — dùng để tính lại chân trời.
    committed_stops: int = 0


class FreezingManager:
    """Theo dõi phần lộ trình đã cam kết và sinh ràng buộc cho ALNS.

    Mỗi lần một phương tiện hoàn thành một chặng (hoặc được giao yêu cầu mới
    và đã rời kho), phần lộ trình đã cam kết của xe được đánh dấu bằng cách
    tăng `horizon`. Các toán tử ALNS sau đó chỉ được thay đổi phần còn lại.
    """

    def __init__(self, safety: float = 0.0):
        self.safety = safety
        self.vehicles: dict[int, VehicleCommitment] = {}

    def register(self, index: int) -> VehicleCommitment:
        """Đăng ký một phương tiện."""
        vc = self.vehicles.setdefault(index, VehicleCommitment(index=index))
        return vc

    def commit(self, index: int, num_stops: int) -> None:
        """Đóng băng `num_stops` nút đầu tiên của lộ trình xe `index`."""
        vc = self.register(index)
        vc.committed_stops = max(vc.committed_stops, num_stops)
        vc.horizon = vc.committed_stops

    def assign(self, index: int, request: int) -> None:
        """Ghi nhận xe `index` được giao yêu cầu `request`."""
        vc = self.register(index)
        vc.assigned.append(request)

    def constraint(self, sol: Solution) -> FreezingConstraint:
        """Sinh ràng buộc vùng tự do từ trạng thái hiện tại.

        Với mỗi xe k:
          * `min_pos[k]` = số nút đã cam kết (chân trời đóng băng), trừ biên
            an toàn `H_0` nếu phần còn lại quá ngắn;
          * `free_map[k]` = tập nút thuộc vùng tự do (sau chân trời).
        """
        min_pos: dict[int, int] = {}
        free_map: dict[int, set[int]] = {}

        for k, route in enumerate(sol.routes):
            vc = self.vehicles.get(k)
            horizon = vc.horizon if vc is not None else 0
            m = len(route.stops)

            # Biên an toàn: nếu phần tự do quá ngắn thì mở băng sớm hơn.
            free_len = m - horizon
            if self.safety > 0.0 and free_len < self.safety:
                horizon = max(0, m - int(self.safety))

            if horizon <= 0:
                continue                      # xe này chưa cam kết gì
            min_pos[k] = horizon
            free_map[k] = set(route.stops[horizon:])

        return FreezingConstraint(min_pos=min_pos, free_map=free_map,
                                   safety=self.safety)
