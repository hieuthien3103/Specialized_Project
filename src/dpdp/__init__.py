"""Khung mã cho đồ án: ALNS cho bài toán giao nhận hàng động (DPDP).

Bố cục module (xem README.md ở thư mục gốc):
    core/            – instance, route, solution, checker
    baselines.py     – thuật toán chèn đối chứng (greedy, regret-2)
    checker.py       – bộ kiểm tra độc lập tính hợp lệ của lời giải
    alns/            – engine ALNS: toán tử phá huỷ/sửa chữa, trọng số, tiêu chuẩn chấp nhận
    adaptations/     – đóng băng phần lô trình, bộ lọc ứng viên
    des/             – khung mô phỏng sự kiện rời rạc
    evaluation/      – chỉ số đánh giá và kiểm định thống kê
"""
from .core import (InfeasibleRoute, Instance, Node, Params, Report, Route,
                   Solution, degree_of_dynamism, dynamize,
                   effective_dynamism, generate_synthetic, insert_request,
                   parse_lilim, validate, write_lilim)
from .baselines import greedy_insertion, regret_insertion

__all__ = [
    "Instance", "Node", "parse_lilim", "write_lilim", "generate_synthetic",
    "dynamize", "degree_of_dynamism", "effective_dynamism", "Params", "Route",
    "InfeasibleRoute",
    "Solution", "insert_request", "greedy_insertion", "regret_insertion",
    "validate", "Report",
]
