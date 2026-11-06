"""Cấu hình ALNS-D.

Giá trị mặc định lấy theo Bảng 2.4 của báo cáo (nguồn tham chiếu: Ropke &
Pisinger [8]); các giá trị ghi "khảo sát ở Chương 3" sẽ được hiệu chỉnh bằng
thực nghiệm sàng lọc ở giai đoạn 5.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class ALNSConfig:
    """Tham số của một lần chạy ALNS-D."""

    # --- ngân sách thời gian (mục 2.2.5) ---
    budget: float = 1.0          # B: ngân sách CPU cho mỗi chu kỳ tái tối ưu (giây)
    max_iterations: int = 10_000  # N_max: trần số vòng lặp
    stall_iterations: int = 300   # N_stall: dừng nếu N_stall vòng lặp không cải thiện

    # --- toán tử phá huỷ (mục 2.1.3) ---
    destroy_fraction: float = 0.4   # ξ: tỷ lệ yêu cầu bị loại
    max_destroy: int = 100          # ν_cap
    p_worst: int = 3                # p: tham số điều khiển tính tất định (loại tệ nhất)
    p_related: int = 6              # p: tham số điều khiển tính tất định (loại liên quan)

    # --- độ liên quan (2.3) ---
    omega_distance: float = 9.0     # ω_1
    omega_time: float = 3.0         # ω_2
    omega_demand: float = 2.0       # ω_3
    omega_vehicle: float = 5.0      # ω_4

    # --- toán tử sửa chữa (mục 2.1.4) ---
    regret_k: int = 2               # g: bậc hối tiếc
    noise: float = 0.025            # η: biên nhiễu trong (2.5)

    # --- cập nhật trọng số (mục 2.1.5) ---
    sigma_new_best: float = 33.0    # σ_1
    sigma_better: float = 9.0       # σ_2
    sigma_accepted: float = 13.0    # σ_3
    reaction: float = 0.1           # λ: hệ số phản ứng
    segment_min: int = 10           # θ_min: độ dài phân đoạn tối thiểu
    segments_per_cycle: int = 1     # s_seg: số lần cập nhật trọng số mỗi chu kỳ

    # --- tiêu chuẩn chấp nhận (mục 2.1.6) ---
    initial_acceptance: float = 0.05  # w_0
    final_temperature_ratio: float = 0.05  # Θ_f / Θ_0

    # --- thích ứng (mục 2.2.3, 2.2.4) ---
    use_freezing: bool = False      # cơ chế đóng băng phần lộ trình đã cam kết
    freeze_safety: float = 0.0      # H_0: biên an toàn của chân trời đóng băng
    use_filter: bool = False        # bộ lọc ứng viên
    filter_kappa: int = 5           # κ: số xe ứng viên tối đa
    filter_delta_max: float = 0.0   # δ_max: ngưỡng độ lệch tuyến (0 = không lọc)
    filter_phi_max: float = 0.0     # φ_max: ngưỡng góc hướng (0 = không lọc)
    filter_radius: float = 0.0      # r_0: bán kính miễn lọc quanh xe

    # --- đa dạng hoá ---
    seed: int = 0

    # --- toán tử dùng (tên trong `alns.operators`) ---
    destroy_operators: tuple[str, ...] = ("random", "worst", "related")
    repair_operators: tuple[str, ...] = ("greedy", "regret2", "greedy_noise")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ALNSConfig":
        """Tạo cấu hình từ dict (dùng cho file YAML/JSON của thực nghiệm)."""
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"tham số không hợp lệ: {sorted(unknown)}")
        kwargs = dict(data)
        for key in ("destroy_operators", "repair_operators"):
            if key in kwargs and isinstance(kwargs[key], list):
                kwargs[key] = tuple(kwargs[key])
        return cls(**kwargs)
