"""Các thành phần thích ứng của ALNS-D cho bài toán động.

Ánh xạ báo cáo:

    2.2.3 cơ chế đóng băng phần lộ trình đã cam kết  -> freezing.py
    2.2.4 bộ lọc ứng viên theo độ lệch & hướng       -> filter.py

Cả hai được cài trên khung ALNS của thư viện `alns` (Wouda & Lan [20]); chúng
là *đóng góp* của đề tài, không phải thuật toán mới.
"""
from .filter import CandidateFilter, FilterConfig
from .freezing import (FreezingConstraint, FreezingManager,
                        VehicleCommitment)

__all__ = [
    "FreezingConstraint", "FreezingManager", "VehicleCommitment",
    "CandidateFilter", "FilterConfig",
]