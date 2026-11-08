"""Sự kiện và hàng đợi ưu tiên của khung mô phỏng DES (mục 2.2.2).

Bài toán DPDP được mô phỏng theo kiểu *event-driven*: một bộ sự kiện được
sinh ra theo thời gian, và mỗi khi có yêu cầu mới xuất hiện thì bộ điều khiển
quyết định có tái tối ưu hay không.

Bốn sự kiện theo mục 2.2.2:

    E_1  yêu cầu mới xuất hiện          (τ_r đến)
    E_2  phương tiện hoàn thành chuyến   (quay về kho)
    E_3  hết ngân sách tái tối ưu       (hết B giây kể từ E_1 gần nhất)
    E_4  kết thúc thời gian mô phỏng    (t = T_H)

Hàng đợi ưu tiên theo thời gian: sự kiện sớm hơn được xử lý trước; khi trùng
thời gian thì sự kiện *quản lý* (E_3, E_4) được ưu tiên hơn sự kiện *vận hành*
(E_1, E_2), vì quyết định quản lý phải dựa trên trạng thái đã cập nhật.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from enum import IntEnum


class EventType(IntEnum):
    """Bốn loại sự kiện của mục 2.2.2."""

    NEW_REQUEST = 1      # E_1
    VEHICLE_FREE = 2     # E_2
    OPTIMIZATION_END = 3  # E_3
    SIMULATION_END = 4   # E_4


#: Sự kiện quản lý được ưu tiên khi trùng thời gian (số nhỏ hơn = ưu tiên cao).
_MANAGEMENT_FIRST = {EventType.OPTIMIZATION_END, EventType.SIMULATION_END}


@dataclass(order=False)
class Event:
    """Một sự kiện trong hàng đợi ưu tiên theo thời gian."""

    time: float
    type: EventType
    payload: object = None
    #: Điểm ưu tiên khi trùng thời gian (số nhỏ hơn được xử lý trước).
    priority: int = field(default=0, compare=False)

    def __lt__(self, other: "Event") -> bool:
        if self.time != other.time:
            return self.time < other.time
        return self.priority < other.priority

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return (self.time == other.time and self.type == other.type
                and self.priority == other.priority)


class EventQueue:
    """Hàng đợi ưu tiên theo thời gian (mục 2.2.2)."""

    def __init__(self):
        self._heap: list[Event] = []
        self._counter = 0

    def push(self, time: float, type: EventType, payload=None) -> None:
        """Đưa một sự kiện vào hàng đợi."""
        priority = 0 if type in _MANAGEMENT_FIRST else 1
        ev = Event(time=time, type=type, payload=payload, priority=priority)
        heapq.heappush(self._heap, ev)

    def pop(self) -> Event | None:
        """Lấy sự kiện sớm nhất; trả None nếu hàng đợi rỗng."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def peek_time(self) -> float | None:
        """Thời điểm của sự kiện sớm nhất."""
        return self._heap[0].time if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)
