"""Sàng lọc tham số ALNS-D trên tập calibration tách khỏi tập đánh giá.

Tiêu chí chọn có thứ tự từ điển: tối đa tỷ lệ phục vụ, tối thiểu tổng quãng
đường, rồi tối thiểu thời gian quyết định trung bình. Kết quả và cấu hình được
chọn đều được lưu, không hiệu chỉnh lại trên tập test.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dpdp.datasets import read_release, release_path
from dpdp.paths import lilim_dir, run_metadata
from run_h1 import run_one


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", type=Path,
                        default=ROOT / "experiments/H1_distance_freezing/configs/calibration_grid.json")
    parser.add_argument("--release-root", type=Path, default=ROOT / "data/dynamic")
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "data/dynamic/manifest.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/H1_distance_freezing/results/raw/calibration.csv")
    parser.add_argument("--selected", type=Path,
                        default=ROOT / "experiments/H1_distance_freezing/configs/selected_alns.json")
    args = parser.parse_args(argv)
    grid = json.loads(args.grid.read_text(encoding="utf-8"))
    protocol, candidates = grid["protocol"], grid["candidates"]
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"không đọc được manifest: {exc}")
    rows = []
    for candidate in candidates:
        for instance_name in protocol["instances"]:
            path = lilim_dir() / instance_name
            if not path.exists():
                parser.error(f"thiếu instance calibration: {path}")
            entry = manifest.get("instances", {}).get(path.stem)
            if entry is None:
                parser.error(f"thiếu {path.stem} trong manifest {args.manifest}")
            fleet_level = protocol.get("fleet_level")
            vehicles = (entry["fleet"][fleet_level] if fleet_level
                        else protocol.get("vehicles"))
            for seed in protocol["seeds"]:
                release_file = release_path(args.release_root, path.stem,
                                            protocol["rho"], seed)
                if not release_file.exists():
                    parser.error(f"thiếu release scenario: {release_file}")
                row = run_one(path, seed, protocol["rho"], candidate["budget"],
                              None, protocol["max_iterations"], vehicles,
                              "alns_freezing", read_release(release_file),
                              candidate.get("alns_overrides", {}),
                              candidate["freeze_horizon"],
                              protocol.get("time_scale", 1.0))
                row["candidate"] = candidate["id"]
                row["fleet_level"] = fleet_level or ""
                row["alns_overrides"] = json.dumps(candidate.get("alns_overrides", {}),
                                                     sort_keys=True)
                rows.append(row)
    if not rows:
        parser.error("grid không sinh lần chạy nào")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) + list(run_metadata())
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            row.update(run_metadata())
            writer.writerow(row)

    grouped = defaultdict(list)
    for row in rows:
        if row["valid"] is True or row["valid"] == "True":
            grouped[row["candidate"]].append(row)
    if not grouped:
        parser.error("không có cấu hình hợp lệ")
    candidate_by_id = {c["id"]: c for c in candidates}
    ranking = []
    for candidate_id, values in grouped.items():
        service = sum(float(v["served_rate"]) for v in values) / len(values)
        distance = sum(float(v["total_distance"]) for v in values) / len(values)
        decision = sum(float(v["decision_seconds_mean"]) for v in values) / len(values)
        ranking.append((-service, distance, decision, candidate_id))
    _, _, _, winner_id = min(ranking)
    selected = {
        "selected_candidate": winner_id,
        "selection_rule": "max served_rate, then min total_distance, then min mean decision time",
        "calibration_protocol": protocol,
        "budget": candidate_by_id[winner_id]["budget"],
        "freeze_horizon": candidate_by_id[winner_id]["freeze_horizon"],
        "time_scale": protocol.get("time_scale", 1.0),
        "alns_overrides": candidate_by_id[winner_id].get("alns_overrides", {}),
    }
    args.selected.parent.mkdir(parents=True, exist_ok=True)
    args.selected.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(rows)} calibration runs to {args.output}")
    print(f"Selected {winner_id} -> {args.selected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
