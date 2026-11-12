"""Khung mô phỏng sự kiện rời rạc (Discrete Event Simulation).

Ánh xạ báo cáo:

    2.2.2 tái tối ưu theo sự kiện yêu cầu đến                  -> simulator.py
    Các loại sự kiện và hàng đợi ưu tiên theo thời gian       -> events.py

Phần ghép DES với khung ALNS của thư viện `alns` (Wouda & Lan [20]) nằm ở
`simulator.py` — đây là một trong hai đóng góp của đề tài (đóng góp còn lại
là cấu hình tham số theo Bảng 2.4).
"""
from .events import Event, EventQueue, EventType
from .simulator import SimConfig, SimResult, Simulator

__all__ = [
    "Event", "EventQueue", "EventType",
    "SimConfig", "SimResult", "Simulator",
]
