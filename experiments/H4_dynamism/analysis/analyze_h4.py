"""Tổng hợp độ nhạy theo mức động cho ALNS-D và các đối chứng."""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

METRICS = ("total_distance", "served_rate", "rejected",
           "decision_seconds_mean", "decision_seconds_max")
CONTROLS = ("greedy", "regret2", "alns_full")


def _pvalue(x, y):
    if all(abs(a - b) <= 1e-12 for a, b in zip(x, y)):
        return 1.0
    from scipy.stats import wilcoxon
    return float(wilcoxon(x, y, alternative="two-sided", zero_method="wilcox",
                          method="auto").pvalue)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=ROOT / "experiments/H4_dynamism/results/raw/h4_results.csv")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/H4_dynamism/analysis/tables/h4_by_rho.csv")
    args = parser.parse_args(argv)
    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"instance", "seed", "rho", "budget", "freeze_horizon",
                "time_scale", "horizon", "vehicles", "algorithm", *METRICS,
                "valid"}
    if not rows or required - set(rows[0]):
        parser.error(f"file thiếu dữ liệu yêu cầu: {sorted(required - set(rows[0]) if rows else required)}")
    if any(r["valid"] != "True" for r in rows):
        parser.error("có lần chạy không hợp lệ")

    grouped = defaultdict(dict)
    for row in rows:
        key = tuple(row[c] for c in (
            "instance", "seed", "rho", "budget", "freeze_horizon",
            "time_scale", "horizon", "vehicles"))
        grouped[key][row["algorithm"]] = row

    out = []
    for rho in sorted({key[2] for key in grouped}, key=float):
        pairs_by_control = {
            control: [value for key, value in grouped.items()
                      if key[2] == rho and control in value and "alns_freezing" in value]
            for control in CONTROLS
        }
        for control, pairs in pairs_by_control.items():
            for metric in METRICS:
                baseline = [float(p[control][metric]) for p in pairs]
                proposed = [float(p["alns_freezing"][metric]) for p in pairs]
                diff = [a - b for a, b in zip(proposed, baseline)]
                out.append({
                    "rho": rho, "comparison": f"alns_freezing_vs_{control}",
                    "metric": metric, "pairs": len(pairs),
                    "control_mean": f"{statistics.mean(baseline):.6f}" if pairs else "",
                    "alns_freezing_mean": f"{statistics.mean(proposed):.6f}" if pairs else "",
                    "mean_difference": f"{statistics.mean(diff):.6f}" if pairs else "",
                    "median_difference": f"{statistics.median(diff):.6f}" if pairs else "",
                    "wilcoxon_p_two_sided": f"{_pvalue(proposed, baseline):.8g}" if pairs else "",
                })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    print(f"Saved {len(out)} summaries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
