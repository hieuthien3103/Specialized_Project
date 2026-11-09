"""Chạy:  python tests/test_dynamic_data.py   (hoặc pytest)."""
import math
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dpdp.datasets import (build_instance_set, fleet_levels, horizon_of,
                           read_release, release_path, verify_instance_set,
                           write_release)
from dpdp.core.instance import dynamize, parse_lilim

LC101 = Path(__file__).resolve().parents[1] / "data" / "lilim" / "lc101.txt"


def _inst():
    return parse_lilim(LC101)


def test_roundtrip_csv():
    inst = _inst()
    rel = dynamize(inst, 0.5, lead_time=10, seed=3)
    with tempfile.TemporaryDirectory() as tmp:
        path = release_path(tmp, inst.name, 0.5, 3)
        write_release(path, rel)
        back = read_release(path)
    assert set(back) == set(rel)
    assert all(abs(back[p] - rel[p]) < 1e-6 for p in rel)


def test_build_and_verify_reproducible():
    inst = _inst()
    with tempfile.TemporaryDirectory() as tmp:
        entry = build_instance_set(inst, tmp, (0.25, 1.0), (0, 1), lead_time=10)
        assert len(entry["files"]) == 4
        assert verify_instance_set(inst, tmp, entry, 10) == []
        # sửa một file -> phải bị phát hiện
        victim = Path(tmp) / entry["files"][0]["file"]
        victim.write_text(victim.read_text().replace("\n", "\n", 1) + "999,1.0\n")
        assert verify_instance_set(inst, tmp, entry, 10)


def test_realized_rho_not_above_target_and_valid_times():
    inst = _inst()
    with tempfile.TemporaryDirectory() as tmp:
        entry = build_instance_set(inst, tmp, (0.25, 0.5, 0.75, 1.0), (0, 1, 2), 10)
    for f in entry["files"]:
        # dynamize chọn ⌈ρ·n⌉ yêu cầu; có thể ít hơn nếu τ rơi đúng 0
        assert f["n_dynamic"] <= math.ceil(f["rho_target"] * inst.n_requests)
    assert entry["horizon"] == horizon_of(inst) == 1236
    assert entry["static_greedy_rejected"] == 0


def test_release_not_later_than_pickup_deadline():
    inst = _inst()
    rel = dynamize(inst, 1.0, lead_time=10, seed=0)
    for p, tau in rel.items():
        assert 0.0 <= tau <= inst.nodes[p].l - inst.tt[0][p] - 10 + 1e-9


def test_fleet_levels():
    assert fleet_levels(10) == {"tight": 10, "loose": 15}
    assert fleet_levels(1)["loose"] > fleet_levels(1)["tight"]


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn(); print(f"PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL  {name}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} đạt")
    sys.exit(1 if failed else 0)