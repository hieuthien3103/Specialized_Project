"""Run the H1 paired comparison on Li & Lim instances.

The two algorithms share the same dynamic releases, fleet, horizon, budget,
instance and seed. The greedy baseline uses only the initial greedy insertion
and arrival-time assignment; ALNS-D reoptimizes with route freezing enabled.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dpdp.des import SimConfig, Simulator
from dpdp.checker import validate
from dpdp.instance import parse_lilim
from dpdp.paths import lilim_dir, raw_results_dir, run_metadata
from dpdp.route import Params


def run_one(path: Path, seed: int, rho: float, budget: float,
            horizon: float, max_iterations: int, vehicles: int | None,
            algorithm: str) -> dict:
    inst = parse_lilim(path)
    config = SimConfig(
        horizon=horizon,
        rho=rho,
        budget=budget,
        max_iterations=max_iterations,
        seed=seed,
        num_vehicles=vehicles,
        use_freezing=algorithm == "alns_freezing",
        reoptimize_on_arrival=algorithm == "alns_freezing",
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
        "horizon": horizon,
        "vehicles": vehicles or inst.num_vehicles,
        "served": result.served,
        "rejected": result.rejected,
        "total_distance": f"{result.total_distance:.6f}",
        "total_lateness": f"{result.total_lateness:.6f}",
        "vehicles_used": result.vehicles_used,
        "reoptimizations": result.reoptimizations,
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
    parser.add_argument("--budget", type=float, default=0.2)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--vehicles", type=int)
    parser.add_argument("--output", type=Path,
                        default=raw_results_dir("H1_distance_freezing")
                        / "h1_paired_results.csv")
    args = parser.parse_args(argv)

    paths = []
    for value in args.instances:
        path = Path(value)
        if not path.exists():
            path = lilim_dir() / value
        if not path.exists():
            parser.error(f"instance not found: {value}")
        paths.append(path)

    rows = []
    for path in paths:
        for seed in args.seeds:
            for algorithm in ("greedy", "alns_freezing"):
                print(f"{path.name} seed={seed} algorithm={algorithm}", flush=True)
                rows.append(run_one(
                    path, seed, args.rho, args.budget, args.horizon,
                    args.max_iterations, args.vehicles, algorithm))

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
