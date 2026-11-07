"""Summarize paired H1 results and run Wilcoxon signed-rank tests."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dpdp.paths import analysis_dir, raw_results_dir


def _fallback_wilcoxon_less(x: list[float], y: list[float]) -> float:
    """Paired signed-rank p-value without SciPy for small experiment runs."""
    diffs = [a - b for a, b in zip(x, y) if abs(a - b) > 1e-12]
    n = len(diffs)
    if not n:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(diffs[i]))
    ranks = [0.0] * n
    pos = 0
    while pos < n:
        end = pos + 1
        while end < n and abs(abs(diffs[order[end]]) - abs(diffs[order[pos]])) < 1e-12:
            end += 1
        rank = (pos + 1 + end) / 2.0
        for i in order[pos:end]:
            ranks[i] = rank
        pos = end
    observed = sum(rank for rank, diff in zip(ranks, diffs) if diff < 0)
    if n <= 20:
        extreme = 0
        total = 1 << n
        for mask in range(total):
            statistic = sum(ranks[i] for i in range(n) if mask & (1 << i))
            if statistic <= observed + 1e-12:
                extreme += 1
        return extreme / total
    mean = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    z = (observed - mean + 0.5) / math.sqrt(variance)
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


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
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["instance"], row["seed"])][row["algorithm"]] = row

    pairs = [pair for pair in grouped.values()
             if "greedy" in pair and "alns_freezing" in pair]
    if not pairs:
        parser.error("no complete greedy/alns_freezing pairs found")

    metrics = ("total_distance", "total_lateness", "rejected", "seconds")
    summary = []
    for metric in metrics:
        greedy = [float(pair["greedy"][metric]) for pair in pairs]
        alns = [float(pair["alns_freezing"][metric]) for pair in pairs]
        differences = [a - g for a, g in zip(alns, greedy)]
        mean_g = sum(greedy) / len(greedy)
        mean_a = sum(alns) / len(alns)
        std_g = statistics.stdev(greedy) if len(greedy) > 1 else 0.0
        std_a = statistics.stdev(alns) if len(alns) > 1 else 0.0
        improvement = ((mean_g - mean_a) / mean_g * 100.0
                       if mean_g else 0.0)
        try:
            from scipy.stats import wilcoxon
            test = wilcoxon(alns, greedy, alternative="less",
                            zero_method="wilcox", method="auto")
            p_value = float(test.pvalue)
        except ImportError:
            p_value = _fallback_wilcoxon_less(alns, greedy)
        summary.append({
            "metric": metric,
            "pairs": len(pairs),
            "greedy_mean": f"{mean_g:.6f}",
            "greedy_std": f"{std_g:.6f}",
            "alns_freezing_mean": f"{mean_a:.6f}",
            "alns_freezing_std": f"{std_a:.6f}",
            "alns_minus_greedy_mean": f"{sum(differences) / len(differences):.6f}",
            "alns_improvement_percent": f"{improvement:.4f}",
            "wilcoxon_p_less": f"{p_value:.8g}",
            "significant_at_0.05": (
                "yes" if p_value < 0.05 else "no"),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary[0])
        writer.writeheader()
        writer.writerows(summary)
    print(f"Saved summary to {args.output}")
    for row in summary:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
