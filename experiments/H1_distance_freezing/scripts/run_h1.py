"""Run paired dynamic comparisons on Li & Lim instances.

All algorithms share an instance, stored release scenario, fleet, horizon,
budget and seed. The four supported variants are the two insertion baselines,
full ALNS re-optimisation, and ALNS-D with route freezing.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dpdp.des import SimConfig, Simulator
from dpdp.datasets import read_release, release_path
from dpdp.core.checker import validate
from dpdp.core.instance import parse_lilim
from dpdp.paths import lilim_dir, raw_results_dir, run_metadata
from dpdp.core.route import Params


def run_one(path: Path, seed: int, rho: float, budget: float,
            horizon: float | None, max_iterations: int, vehicles: int | None,
            algorithm: str, release_times: dict[int, float] | None = None,
            alns_overrides: dict[str, object] | None = None) -> dict:
    inst = parse_lilim(path)
    if algorithm not in {"greedy", "regret2", "alns_full", "alns_freezing"}:
        raise ValueError(f"algorithm không hỗ trợ: {algorithm}")
    is_alns = algorithm.startswith("alns_")
    resolved_horizon = inst.nodes[0].l if horizon is None else horizon
    config = SimConfig(
        horizon=resolved_horizon,
        rho=rho,
        budget=budget,
        max_iterations=max_iterations,
        seed=seed,
        num_vehicles=vehicles,
        use_freezing=algorithm == "alns_freezing",
        reoptimize_on_arrival=is_alns,
        construction="regret2" if algorithm == "regret2" else "greedy",
        release_times=release_times,
        alns_overrides=alns_overrides or {},
    )
    simulator = Simulator(inst, Params(), config)
    result = simulator.run()
    report = validate(inst, result.solution.as_lists(), Params(),
                      result.solution.unassigned, simulator.completed)
    return {
        "instance": inst.name,
        "input": str(path),
        "algorithm": algorithm,
        "seed": seed,
        "rho": rho,
        "budget": budget,
        "horizon": resolved_horizon,
        "vehicles": vehicles or inst.num_vehicles,
        "served": result.served,
        "served_rate": f"{result.served / inst.n_requests:.6f}",
        "rejected": result.rejected,
        "total_distance": f"{result.total_distance:.6f}",
        "total_lateness": f"{result.total_lateness:.6f}",
        "vehicles_used": result.vehicles_used,
        "reoptimizations": result.reoptimizations,
        "route_changes": result.route_changes,
        "improved_reoptimizations": result.improved_reoptimizations,
        "decision_count": len(result.decision_seconds),
        "decision_seconds_mean": (
            f"{sum(result.decision_seconds) / len(result.decision_seconds):.6f}"
            if result.decision_seconds else "0.000000"),
        "decision_seconds_max": (
            f"{max(result.decision_seconds):.6f}"
            if result.decision_seconds else "0.000000"),
        "seconds": f"{result.seconds:.6f}",
        "valid": report.ok,
        "validation_errors": "; ".join(report.errors[:3]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", default=["lc101.txt"],
                        help="Li & Lim filenames or paths")
    parser.add_argument("--seeds", nargs="+", type=int,
                        default=list(range(10)))
    parser.add_argument("--rho", type=float, default=0.5)
    parser.add_argument("--rhos", nargs="+", type=float,
                        help="Nhiều mức động; thay thế --rho, dùng cho H4")
    parser.add_argument("--budget", type=float, default=0.2)
    parser.add_argument("--horizon", type=float,
                        help="T_H; mặc định là giờ đóng cửa kho của từng thể hiện")
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--vehicles", type=int)
    parser.add_argument("--algorithms", nargs="+",
                        default=["greedy", "regret2", "alns_full", "alns_freezing"],
                        choices=["greedy", "regret2", "alns_full", "alns_freezing"])
    parser.add_argument("--release-root", type=Path,
                        help="Thư mục data/dynamic đã sinh sẵn; thiếu thì dùng dynamize() tái lập")
    parser.add_argument("--alns-config", type=Path,
                        help="JSON các trường ALNSConfig cần ghi đè (dùng cho hiệu chỉnh)")
    parser.add_argument("--output", type=Path,
                        default=raw_results_dir("H1_distance_freezing")
                        / "h1_paired_results.csv")
    args = parser.parse_args(argv)
    alns_overrides = {}
    if args.alns_config is not None:
        try:
            alns_overrides = json.loads(args.alns_config.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"không đọc được --alns-config: {exc}")
        if not isinstance(alns_overrides, dict):
            parser.error("--alns-config phải là JSON object")

    paths = []
    for value in args.instances:
        path = Path(value)
        if not path.exists():
            path = lilim_dir() / value
        if not path.exists():
            parser.error(f"instance not found: {value}")
        paths.append(path)

    rhos = args.rhos if args.rhos is not None else [args.rho]
    if any(not 0.0 <= rho <= 1.0 for rho in rhos):
        parser.error("mọi rho phải thuộc [0, 1]")
    rows = []
    for path in paths:
        for rho in rhos:
            for seed in args.seeds:
                release_times = None
                if args.release_root is not None:
                    release_file = release_path(args.release_root, path.stem,
                                                rho, seed)
                    if not release_file.exists():
                        parser.error(f"không có release scenario: {release_file}")
                    release_times = read_release(release_file)
                for algorithm in args.algorithms:
                    print(f"{path.name} rho={rho} seed={seed} algorithm={algorithm}",
                          flush=True)
                    row = run_one(
                        path, seed, rho, args.budget, args.horizon,
                        args.max_iterations, args.vehicles, algorithm,
                        release_times, alns_overrides)
                    rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) + list(run_metadata())
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            row.update(run_metadata())
            writer.writerow(row)
    print(f"Saved {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
