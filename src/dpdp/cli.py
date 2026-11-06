"""Chạy các thuật toán đối chứng trên một thể hiện và kiểm tra bằng checker.

    python -m dpdp.cli --instance data/lilim/lc101.txt
    python -m dpdp.cli --synthetic 50 --seed 1
    python -m dpdp.cli --instance data/lilim/lrc101.txt --vehicles 15 --late-max 10

Kết quả được ghi vào CSV + bảng văn bản trong `--output-dir` (mặc định
`experiments/H1_distance_freezing/results/raw`) kèm metadata (mã commit, thời điểm)
để bảo đảm tái lập được.
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from .baselines import greedy_insertion, regret_insertion
from .checker import validate
from .instance import generate_synthetic, parse_lilim
from .paths import lilim_dir, raw_results_dir, run_metadata
from .route import Params

DEFAULT_OUTPUT = raw_results_dir("H1_distance_freezing")


def _resolve_instance(name: str) -> Path:
    """Cho phép truyền tên file ngắn (`lc101.txt`) và tự tìm trong `data/lilim`."""
    p = Path(name)
    if p.exists():
        return p
    cand = lilim_dir() / name
    if cand.exists():
        return cand
    raise FileNotFoundError(f"không tìm thấy file thể hiện: {name}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--instance", help="đường dẫn file Li & Lim (hoặc tên file trong data/lilim)")
    src.add_argument("--synthetic", type=int, metavar="N",
                     help="sinh thể hiện thử với N yêu cầu (chỉ để gỡ lỗi)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vehicles", type=int, help="ghi đè số xe K")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", type=float, default=1000.0)
    ap.add_argument("--gamma", type=float, default=0.25)
    ap.add_argument("--late-max", type=float, default=0.0, help="L̄ (0 = khung cứng)")
    ap.add_argument("--output-dir", default=None,
                    help="thư mục lưu kết quả (mặc định: experiments/H1.../results/raw)")
    a = ap.parse_args(argv)

    if a.instance:
        path = _resolve_instance(a.instance)
        inst = parse_lilim(path)
        input_name = str(path)
    else:
        inst = generate_synthetic(a.synthetic, a.seed)
        input_name = f"synthetic:{a.synthetic}"

    params = Params(a.alpha, a.beta, a.gamma, a.late_max)
    k = a.vehicles or inst.num_vehicles
    summary = (f"{inst.name}: {inst.n_requests} yêu cầu, K={k}, Q={inst.capacity:g}, "
               f"L̄={params.late_max:g}")
    header = (f"{'thuật toán':<12}{'phục vụ':>9}{'từ chối':>9}{'số xe':>7}"
              f"{'quãng đường':>14}{'độ trễ':>9}{'mục tiêu':>12}{'giây':>8}  hợp lệ")
    print(summary)
    print(header)
    table_lines = [summary, header]
    results = []
    for name, fn in (("greedy", greedy_insertion), ("regret-2", regret_insertion)):
        t0 = time.perf_counter()
        sol = fn(inst, params, num_vehicles=k)
        dt = time.perf_counter() - t0
        rep = validate(inst, sol.as_lists(), params, sol.unassigned)
        result_line = (f"{name:<12}{rep.served:>9}{rep.rejected:>9}{rep.vehicles_used:>7}"
                       f"{rep.distance:>14.2f}{rep.lateness:>9.2f}"
                       f"{rep.objective(params):>12.2f}{dt:>8.2f}"
                       f"  {'OK' if rep.ok else 'LỖI'}")
        print(result_line)
        table_lines.append(result_line)
        for e in rep.errors[:5]:
            print("   !", e)
            table_lines.append(f"   ! {e}")
        results.append({
            "input": input_name,
            "instance": inst.name,
            "seed": a.seed if a.synthetic is not None else "",
            "vehicles": k,
            "capacity": inst.capacity,
            "late_max": params.late_max,
            "algorithm": name,
            "served": rep.served,
            "rejected": rep.rejected,
            "vehicles_used": rep.vehicles_used,
            "distance": f"{rep.distance:.2f}",
            "lateness": f"{rep.lateness:.2f}",
            "objective": f"{rep.objective(params):.2f}",
            "seconds": f"{dt:.4f}",
            "valid": rep.ok,
        })

    output_dir = Path(a.output_dir) if a.output_dir else DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)
    meta = run_metadata()
    output_path = output_dir / f"{Path(inst.name).stem}_results.csv"
    fieldnames = list(results[0].keys()) + ["commit", "timestamp", "python"]
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            row.update(meta)
            writer.writerow(row)
    text_output_path = output_dir / f"{Path(inst.name).stem}_results.txt"
    text_output_path.write_text("\n".join(table_lines) + "\n", encoding="utf-8")
    print(f"\nĐã lưu kết quả CSV: {output_path}")
    print(f"Đã lưu bảng Terminal: {text_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
