"""Chạy:  python tests/test_core.py   (hoặc pytest nếu đã cài)."""
import itertools
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dpdp import (InfeasibleRoute, Params, Route, Solution, degree_of_dynamism,
                  dynamize, generate_synthetic, greedy_insertion, insert_request,
                  parse_lilim, regret_insertion, validate, write_lilim)

HARD = Params()
SOFT = Params(late_max=25.0, gamma=0.5)


def brute_best_insertion(route, p, d):
    """Duyệt vét cạn mọi (i, j) bằng cách dựng lại cả lộ trình từ đầu."""
    best = None
    base = route.cost
    m = len(route.stops)
    for i in range(m + 1):
        for j in range(i, m + 1):
            s = route.stops
            cand = s[:i] + [p] + s[i:j] + [d] + s[j:]
            try:
                c = Route(route.inst, route.params, cand).cost
            except InfeasibleRoute:
                continue
            if best is None or c - base < best - 1e-12:
                best = c - base
    return best


def test_roundtrip_parse_write():
    inst = generate_synthetic(20, seed=3)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "x.txt")
        write_lilim(inst, path)
        back = parse_lilim(path)
    assert back.n_requests == inst.n_requests
    assert back.capacity == inst.capacity and back.num_vehicles == inst.num_vehicles
    for a, b in zip(inst.nodes, back.nodes):
        assert a == b


def test_best_insertion_matches_bruteforce():
    """Cắt tỉa + lối tắt 'đuôi không đổi' không được làm sai Δ chi phí."""
    for params in (HARD, SOFT):
        for seed in range(6):
            inst = generate_synthetic(25, seed=seed)
            rng = random.Random(seed)
            sol = Solution(inst, params, num_vehicles=3)
            reqs = inst.requests[:]
            rng.shuffle(reqs)
            for p in reqs:
                d = inst.delivery_of(p)
                for route in sol.routes:
                    fast = route.best_insertion(p, d)
                    slow = brute_best_insertion(route, p, d)
                    if slow is None:
                        assert fast is None, (seed, p)
                    else:
                        assert fast is not None, (seed, p)
                        assert abs(fast[0] - slow) < 1e-6, (seed, p, fast[0], slow)
                insert_request(sol, p)


def test_solutions_are_valid_and_cost_consistent():
    for params in (HARD, SOFT):
        for seed in range(4):
            inst = generate_synthetic(40, seed=seed)
            for fn in (greedy_insertion, regret_insertion):
                sol = fn(inst, params, num_vehicles=10)
                rep = validate(inst, sol.as_lists(), params, sol.unassigned)
                assert rep.ok, rep.errors[:3]
                assert abs(rep.distance - sol.distance) < 1e-6
                assert abs(rep.lateness - sol.lateness) < 1e-6
                assert rep.served + rep.rejected == inst.n_requests
                assert abs(rep.objective(params) - sol.cost) < 1e-6


def test_limited_fleet_rejects_requests():
    inst = generate_synthetic(40, seed=2)
    sol = greedy_insertion(inst, HARD, num_vehicles=1)
    assert len(sol.unassigned) > 0
    rep = validate(inst, sol.as_lists(), HARD, sol.unassigned)
    assert rep.ok and rep.rejected == len(sol.unassigned)


def test_checker_detects_violations():
    inst = generate_synthetic(10, seed=0)
    p = inst.requests[0]
    d = inst.delivery_of(p)
    # giao trước lấy
    assert not validate(inst, [[d, p]], HARD, set(inst.requests[1:])).ok
    # thiếu điểm giao
    assert not validate(inst, [[p]], HARD, set(inst.requests[1:])).ok
    # yêu cầu bị bỏ sót không ghi nhận
    assert not validate(inst, [[p, d]], HARD, set()).ok
    # thăm trùng
    assert not validate(inst, [[p, d], [p, d]], HARD, set(inst.requests[1:])).ok
    # quá tải: ép sức chứa nhỏ
    small = generate_synthetic(10, seed=0, capacity=5.0)
    assert not validate(small, [[small.requests[0], small.delivery_of(small.requests[0])]],
                        HARD, set(small.requests[1:])).ok
    # hợp lệ khi đúng
    assert validate(inst, [[p, d]], HARD, set(inst.requests[1:])).ok


def test_route_refuses_infeasible_and_keeps_state():
    inst = generate_synthetic(10, seed=0)
    r = Route(inst, HARD)
    p = inst.requests[0]
    d = inst.delivery_of(p)
    r.insert(p, d, 0, 0)
    before = list(r.stops)
    try:
        r.insert(d, p, 0, 0)         # đảo vai trò: giao trước lấy, vi phạm tải/thứ tự
        raised = False
    except InfeasibleRoute:
        raised = True
    assert raised and r.stops == before


def test_removal_keeps_feasibility_and_never_increases_cost():
    inst = generate_synthetic(40, seed=5)
    sol = greedy_insertion(inst, HARD, num_vehicles=10)
    for route in sol.routes:
        for p in [x for x in route.stops if inst.nodes[x].is_pickup]:
            before = route.cost
            route.remove_request(p, inst.delivery_of(p))   # không ném lỗi
            assert route.cost <= before + 1e-9
            break


def test_soft_lateness_never_worse_than_hard():
    """Nới khung giao (L̄ > 0) chỉ mở rộng miền khả thi."""
    inst = generate_synthetic(40, seed=7)
    hard = greedy_insertion(inst, HARD, num_vehicles=4)
    soft = greedy_insertion(inst, Params(late_max=60.0, gamma=0.1), num_vehicles=4)
    assert soft.n_served >= hard.n_served


def test_dynamize():
    inst = generate_synthetic(100, seed=1)
    rel = dynamize(inst, rho=0.5, lead_time=10, seed=4)
    assert set(rel) == set(inst.requests)
    assert all(0 <= v <= inst.nodes[p].l for p, v in rel.items())
    assert 0.3 <= degree_of_dynamism(rel) <= 0.5      # ≤ ρ vì có thể rơi τ=0
    assert rel == dynamize(inst, rho=0.5, lead_time=10, seed=4)   # tái lập được
    assert degree_of_dynamism(dynamize(inst, rho=0.0)) == 0.0


def test_parse_interleaved_ids_like_real_files():
    """File thật xen kẽ lấy/giao: nút giao có thể có id nhỏ hơn nút lấy."""
    text = ("2\t100\t1\n"
            "0\t40\t50\t0\t0\t1000\t0\t0\t0\n"
            "1\t45\t68\t-10\t100\t300\t10\t3\t0\n"   # giao, lấy ở nút 3
            "2\t35\t30\t-20\t100\t300\t10\t4\t0\n"   # giao, lấy ở nút 4
            "3\t42\t60\t10\t0\t200\t10\t0\t1\n"      # lấy, giao ở nút 1
            "4\t30\t40\t20\t0\t200\t10\t0\t2\n")     # lấy, giao ở nút 2
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "mini.txt")
        open(path, "w").write(text)
        inst = parse_lilim(path)
    assert inst.requests == [3, 4]
    assert inst.delivery_of(3) == 1 and inst.delivery_of(4) == 2
    sol = greedy_insertion(inst, HARD)
    rep = validate(inst, sol.as_lists(), HARD, sol.unassigned)
    assert rep.ok and rep.served == 2


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as e:           # noqa: BLE001
            failed += 1
            import traceback
            print(f"FAIL  {name}: {e!r}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} đạt")
    sys.exit(1 if failed else 0)
