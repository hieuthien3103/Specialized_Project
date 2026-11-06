"""Đường dẫn chuẩn của dự án (dữ liệu, kết quả thực nghiệm).

Dùng để mọi script trong `experiments/` trỏ về cùng một nơi, tránh tình trạng
kết quả nằm rải rác ở nhiều thư mục `results/` khác nhau.
"""
from __future__ import annotations

import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    """Thư mục gốc của repo (nơi chứa pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Cài đặt kiểu pip: dùng cwd làm gốc dự án.
    return Path.cwd()


def data_dir() -> Path:
    """Thư mục dữ liệu: `data/` (chứa `lilim/` và `hcm/`)."""
    return repo_root() / "data"


def lilim_dir() -> Path:
    """Bộ dữ liệu Li & Lim (mục 1.3.1 của báo cáo)."""
    return data_dir() / "lilim"


def experiments_dir() -> Path:
    """Thư mục chứa bốn thư mục thực nghiệm H1–H4."""
    return repo_root() / "experiments"


def hypothesis_dir(tag: str) -> Path:
    """Thư mục của một giả thuyết, ví dụ `H1_distance_freezing`."""
    return experiments_dir() / tag


def raw_results_dir(tag: str) -> Path:
    """Thư mục kết quả thô của một giả thuyết (mỗi lần chạy một file CSV)."""
    return hypothesis_dir(tag) / "results" / "raw"


def analysis_dir(tag: str) -> Path:
    """Thư mục chứa bảng và tóm tắt phân tích của một giả thuyết."""
    return hypothesis_dir(tag) / "analysis"


def git_commit() -> str:
    """Mã commit hiện tại (chuỗi rỗng nếu không phải repo git)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root(), capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def run_metadata() -> dict[str, str]:
    """Metadata ghi kèm vào file kết quả để bảo đảm tái lập được."""
    return {
        "commit": git_commit(),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
    }
