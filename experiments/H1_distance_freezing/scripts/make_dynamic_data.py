"""Sinh các kịch bản động Li & Lim dùng chung cho thực nghiệm.

Ví dụ:
    python experiments/H1_distance_freezing/scripts/make_dynamic_data.py \
        --instances lc101.txt lr101.txt lrc101.txt --rhos 0.25 0.5 0.75 1.0

Mỗi file release chỉ được sinh một lần và được dùng lại nguyên vẹn cho mọi
thuật toán trong các so sánh theo cặp.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dpdp.core.instance import parse_lilim
from dpdp.datasets import (DEFAULT_INSTANCES, DEFAULT_RHOS, DEFAULT_SEEDS,
                           build_instance_set)
from dpdp.paths import data_dir, lilim_dir, run_metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", nargs="+", default=list(DEFAULT_INSTANCES))
    parser.add_argument("--rhos", nargs="+", type=float, default=list(DEFAULT_RHOS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--lead-time", type=float, default=10.0)
    parser.add_argument("--output", type=Path, default=data_dir() / "dynamic")
    args = parser.parse_args(argv)

    if any(not 0.0 <= rho <= 1.0 for rho in args.rhos):
        parser.error("mọi rho phải thuộc [0, 1]")
    if any(seed < 0 for seed in args.seeds):
        parser.error("seed phải không âm")

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    instances = {}
    for name in args.instances:
        path = Path(name)
        if not path.exists():
            path = lilim_dir() / name
        if not path.exists():
            parser.error(f"không tìm thấy instance: {name}")
        inst = parse_lilim(path)
        instances[inst.name] = build_instance_set(
            inst, output, args.rhos, args.seeds, args.lead_time)

    manifest = {
        "generated": run_metadata(),
        "params": {
            "lead_time": args.lead_time,
            "rhos": args.rhos,
            "seeds": args.seeds,
            "late_max": 0.0,
            "formula": "tau_r ~ U(0, max(0, l_r - t0r - lead_time))",
        },
        "instances": instances,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"Saved {sum(len(v['files']) for v in instances.values())} scenarios to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
