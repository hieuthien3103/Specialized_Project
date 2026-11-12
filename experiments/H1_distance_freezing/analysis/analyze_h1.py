"""Tổng hợp so sánh theo cặp cho bốn thuật toán động.

Mỗi cặp được xác định bằng cùng instance, release scenario (rho, seed), đội xe,
chân trời và ngân sách. ALNS-D được kiểm định hai phía với từng đối chứng;
việc dùng hai phía tránh khẳng định hướng cải thiện trước khi có dữ liệu.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dpdp.paths import analysis_dir, raw_results_dir

PAIR_COLUMNS = ("instance", "seed", "rho", "budget", "horizon", "vehicles")
METRICS = (
    "total_distance", "served_rate", "rejected", "total_lateness",
    "route_changes", "decision_seconds_mean", "decision_seconds_max",
)
CONTROLS = ("greedy", "regret2", "alns_full")


def _paired_test(x: list[float], y: list[float]) -> float:
    """Wilcoxon hai phía, trả 1 khi toàn bộ sai khác bằng 0."""
    if all(abs(a - b) <= 1e-12 for a, b in zip(x, y)):
        return 1.0
    from scipy.stats import wilcoxon
    return float(wilcoxon(x, y, alternative="two-sided", zero_method="wilcox",
                          method="auto").pvalue)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=raw_results_dir("H1_distance_freezing")
                        / "h1_paired_results.csv")
    parser.add_argument("--output", type=Path,
                        default=analysis_dir("H1_distance_freezing")
                        / "tables/h1_summary.csv")
    args = parser.parse_args(argv)

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        parser.error("file kết quả rỗng")
    missing = (set(PAIR_COLUMNS) | {"algorithm", *METRICS}) - set(rows[0])
    if missing:
        parser.error(f"thiếu cột: {sorted(missing)}")
    invalid = [r for r in rows if r.get("valid") != "True"]
    if invalid:
        parser.error(f"có {len(invalid)} lần chạy không hợp lệ; không kiểm định")

    grouped: dict[tuple[str, ...], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        key = tuple(row[c] for c in PAIR_COLUMNS)
        if row["algorithm"] in grouped[key]:
            parser.error(f"trùng kết quả cho cặp {key}, {row['algorithm']}")
        grouped[key][row["algorithm"]] = row

    summary = []
    for control in CONTROLS:
        pairs = [pair for pair in grouped.values()
                 if control in pair and "alns_freezing" in pair]
        if not pairs:
            continue
        for metric in METRICS:
            control_values = [float(p[control][metric]) for p in pairs]
            proposed_values = [float(p["alns_freezing"][metric]) for p in pairs]
            diff = [a - b for a, b in zip(proposed_values, control_values)]
            mean_control = statistics.mean(control_values)
            mean_proposed = statistics.mean(proposed_values)
            summary.append({
                "comparison": f"alns_freezing_vs_{control}",
                "metric": metric,
                "pairs": len(pairs),
                "control_mean": f"{mean_control:.6f}",
                "control_std": f"{statistics.stdev(control_values) if len(pairs) > 1 else 0.0:.6f}",
                "alns_freezing_mean": f"{mean_proposed:.6f}",
                "alns_freezing_std": f"{statistics.stdev(proposed_values) if len(pairs) > 1 else 0.0:.6f}",
                "mean_difference": f"{statistics.mean(diff):.6f}",
                "median_difference": f"{statistics.median(diff):.6f}",
                "relative_change_percent": (
                    f"{(mean_proposed - mean_control) / mean_control * 100.0:.4f}"
                    if mean_control else ""),
                "wilcoxon_p_two_sided": f"{_paired_test(proposed_values, control_values):.8g}",
            })

    if not summary:
        parser.error("không có cặp alns_freezing/đối chứng hoàn chỉnh")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Saved {len(summary)} summaries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
