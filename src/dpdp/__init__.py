"""Khung mã cho đồ án: ALNS cho bài toán giao nhận hàng động (DPDP).

Bố cục module (xem README.md ở thư mục gốc):
    instance.py      – đọc/ghi file Li & Lim, sinh dữ liệu thử, động hoá
    route.py         – lộ trình một xe, chèn/loại yêu cầu, khả thi
    solution.py      – lời giải (tập lộ trình + yêu cầu bị từ chối)
    baselines.py     – thuật toán chèn đối chứng (greedy, regret-2)
    checker.py       – bộ kiểm tra độc lập tính hợp lệ của lời giải
    alns/            – engine ALNS: toán tử phá huỷ/sửa chữa, trọng số, tiêu chuẩn chấp nhận
    adaptations/     – đóng băng phần lô trình, bộ lọc ứng viên
    des/             – khung mô phỏng sự kiện rời rạc
    evaluation/      – chỉ số đánh giá và kiểm định thống kê
"""
from .instance import (Instance, Node, degree_of_dynamism, dynamize,
                       generate_synthetic, parse_lilim, write_lilim)
from .route import InfeasibleRoute, Params, Route
from .solution import Solution, insert_request
from .baselines import greedy_insertion, regret_insertion
from .checker import Report, validate

__all__ = [
    "Instance", "Node", "parse_lilim", "write_lilim", "generate_synthetic",
    "dynamize", "degree_of_dynamism", "Params", "Route", "InfeasibleRoute",
    "Solution", "insert_request", "greedy_insertion", "regret_insertion",
    "validate", "Report",
]
