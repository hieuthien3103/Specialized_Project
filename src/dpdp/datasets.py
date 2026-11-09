"""Chuẩn bị dữ liệu động từ Li & Lim (phần A: mục 1.3.1 của báo cáo).

Một "bộ dữ liệu động" là bộ ba (thể hiện, ρ, seed): thể hiện Li & Lim tĩnh cộng
với *thời điểm xuất hiện* τ_r của từng yêu cầu (công thức 1.3). Thời điểm này
được ghi ra file CSV để mọi thuật toán và mọi giả thuyết H1–H4 dùng chung đúng
một dòng đơn hàng, và để kết quả tái lập được.

Bố cục thư mục đầu ra:

    data/dynamic/
    ├── manifest.json                      # tham số sinh, K, horizon, checksum
    └── <thể_hiện>/rho0.50_seed3.csv       # cột: request_id, release_time

`request_id` là id nút LẤY hàng (cùng quy ước với `Instance.requests`).
"""
from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

from .core.instance import (Instance, degree_of_dynamism, dynamize,
                       effective_dynamism)
from .core.route import Params

#: Tập thể hiện mặc định: nhóm 1 (khung thời gian hẹp) và nhóm 2 (khung rộng),
#: đủ ba họ phân bố C / R / RC.
DEFAULT_INSTANCES = (
    "lc101.txt", "lc103.txt", "lr101.txt", "lr103.txt",
    "lrc101.txt", "lrc103.txt",
    "lc201.txt", "lr201.txt", "lrc201.txt",
)
DEFAULT_RHOS = (0.25, 0.5, 0.75, 1.0)
DEFAULT_SEEDS = tuple(range(10))
PRECISION = 6          # số chữ số thập phân của release_time trong CSV


# ------------------------------------------------------------ đường dẫn / I-O
def rho_tag(rho: float) -> str:
    return f"rho{rho:.2f}"


def release_path(root: str | Path, inst_name: str, rho: float, seed: int) -> Path:
    return Path(root) / inst_name / f"{rho_tag(rho)}_seed{seed}.csv"


def write_release(path: Path, release: dict[int, float]) -> str:
    """Ghi release time ra CSV, trả về sha256 của file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["request_id", "release_time"])
        for p in sorted(release):
            writer.writerow([p, f"{release[p]:.{PRECISION}f}"])
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_release(path: str | Path) -> dict[int, float]:
    """Đọc release time; dùng để nạp thẳng vào mô phỏng thay cho `dynamize`."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return {int(r["request_id"]): float(r["release_time"])
                for r in csv.DictReader(handle)}


# --------------------------------------------------------------- đặc trưng
def horizon_of(inst: Instance) -> float:
    """T_H: giờ đóng cửa của kho (khác nhau theo họ: 1236, 230, 240, ...)."""
    return inst.nodes[0].l


def static_fleet(inst: Instance, params: Params | None = None) -> tuple[int, int]:
    """Số xe mà chèn tham lam TĨNH cần (biết hết yêu cầu) và số yêu cầu bị từ chối.

    Dùng làm mốc để chọn K: header Li & Lim (K = 25 hay 100...) quá rộng nên
    mỗi đơn gần như có xe riêng và không có cạnh tranh giữa các đơn.
    """
    from .baselines import greedy_insertion
    sol = greedy_insertion(inst, params or Params(), num_vehicles=inst.num_vehicles)
    return sol.vehicles_used, len(sol.unassigned)


def fleet_levels(greedy_vehicles: int, loose_factor: float = 1.5) -> dict[str, int]:
    """K "chặt" (đúng bằng mốc tĩnh) và K "rộng" (nhân hệ số)."""
    v = max(1, greedy_vehicles)
    return {"tight": v, "loose": max(v + 1, math.ceil(loose_factor * v))}


# ------------------------------------------------------------------ sinh
def build_instance_set(inst: Instance, root: str | Path, rhos, seeds,
                       lead_time: float, params: Params | None = None) -> dict:
    """Sinh mọi file (ρ, seed) của một thể hiện; trả về mục manifest."""
    horizon = horizon_of(inst)
    v, rejected = static_fleet(inst, params)
    files = []
    for rho in rhos:
        for seed in seeds:
            rel = dynamize(inst, rho, lead_time=lead_time, seed=seed)
            path = release_path(root, inst.name, rho, seed)
            digest = write_release(path, rel)
            files.append({
                "rho_target": rho,
                "seed": seed,
                "file": str(path.relative_to(root)),
                "n_dynamic": sum(1 for t in rel.values() if t > 0),
                "rho_realized": round(degree_of_dynamism(rel), 4),
                "rho_eff": round(effective_dynamism(rel, horizon), 4),
                "sha256": digest,
            })
    return {
        "n_requests": inst.n_requests,
        "header_vehicles": inst.num_vehicles,
        "capacity": inst.capacity,
        "horizon": horizon,
        "static_greedy_vehicles": v,
        "static_greedy_rejected": rejected,
        "fleet": fleet_levels(v),
        "files": files,
    }


def verify_instance_set(inst: Instance, root: str | Path, entry: dict,
                        lead_time: float) -> list[str]:
    """Sinh lại từ (thể hiện, ρ, seed) và so với file đã lưu; trả về danh sách lỗi."""
    errors = []
    for f in entry["files"]:
        path = Path(root) / f["file"]
        if not path.exists():
            errors.append(f"thiếu file {path}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != f["sha256"]:
            errors.append(f"checksum sai: {path}")
            continue
        fresh = dynamize(inst, f["rho_target"], lead_time=lead_time, seed=f["seed"])
        stored = read_release(path)
        bad = [p for p in fresh if abs(fresh[p] - stored.get(p, math.nan)) > 10 ** -PRECISION]
        if bad:
            errors.append(f"{path}: {len(bad)} yêu cầu lệch so với dynamize()")
    return errors