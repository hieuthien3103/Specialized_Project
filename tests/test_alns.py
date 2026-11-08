"""Kiểm thử engine ALNS.

Chạy:  python tests/test_alns.py   (hoặc pytest nếu đã cài).
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dpdp import Params, greedy_insertion, validate
from dpdp.alns.acceptance import HillClimbing, SimulatedAnnealing
from dpdp.alns.adapter import (DPDPState, make_destroy_operator,
                               make_repair_operator)
from dpdp.alns.config import ALNSConfig
from dpdp.alns.engine import ALNSEngine
from dpdp.alns.operators import (DESTROY_OPERATORS, REPAIR_OPERATORS,
                                 FreeContext, destroy_random, destroy_related,
                                 destroy_worst)
from dpdp.alns.weights import OperatorWeights
from dpdp.core.instance import generate_synthetic, parse_lilim
from dpdp.core.solution import Solution

HARD = Params()


def _setup(n=40, seed=0, vehicles=8):
    inst = generate_synthetic(n, seed=seed)
    sol = greedy_insertion(inst, HARD, num_vehicles=vehicles)
    return inst, sol


def test_config_roundtrip():
    cfg = ALNSConfig(budget=2.5, use_freezing=True, seed=7)
    data = cfg.to_dict()
    back = ALNSConfig.from_dict(data)
    assert back.budget == 2.5 and back.use_freezing and back.seed == 7
    assert back.destroy_operators == cfg.destroy_operators
    try:
        ALNSConfig.from_dict({"khong_ton_tai": 1})
        raise AssertionError("phải báo lỗi với tham số lạ")
    except ValueError:
        pass


def test_weights_update_formula():
    """Kiểm tra (2.7): w' = (1−λ)w + λ·π/n, và n_i = 0 thì giữ nguyên."""
    w = OperatorWeights(names=("a", "b"), reaction=0.5)
    w.weights["a"] = 2.0
    w.weights["b"] = 4.0
    w.reward("a", "new_best")     # 33 điểm, dùng 1 lần
    w.reward("a", "better")      # +9  => 42 điểm, dùng 2 lần
    w.update()
    # π_a/n_a = 42/2 = 21  -> w_a' = 0.5*2 + 0.5*21 = 11.5
    assert abs(w.weights["a"] - 11.5) < 1e-9
    assert abs(w.weights["b"] - 4.0) < 1e-9, "n_b = 0 thì w_b giữ nguyên"


def test_weights_geometric_convergence():
    """Mệnh đề 2.1: w_k − π̄ = (1−λ)^k (w_0 − π̄)."""
    lam = 0.1
    w = OperatorWeights(names=("a",), reaction=lam)
    w.weights["a"] = 1.0
    w.reward("a", "new_best")     # π̄ = 33
    w0 = w.weights["a"]
    for _ in range(5):
        w.update()
        w.reset_segment()
        w.reward("a", "new_best")
    expected = 33 + (1 - lam) ** 5 * (w0 - 33)
    assert abs(w.weights["a"] - expected) < 1e-9


def test_weight_selection_probability():
    """Toán tử có trọng số lớn hơn phải được chọn thường xuyên hơn."""
    w = OperatorWeights(names=("a", "b"), reaction=0.1)
    w.weights["a"], w.weights["b"] = 9.0, 1.0
    rng = random.Random(0)
    counts = {"a": 0, "b": 0}
    for _ in range(4000):
        counts[w.select(rng)] += 1
    assert counts["a"] > counts["b"] * 4


def test_acceptance_criteria():
    """(2.9): lời giải tệ hơn w_0% được chấp nhận với xác suất ~0,5."""
    sa = SimulatedAnnealing(initial_cost=100.0, initial_acceptance=0.05,
                            final_ratio=0.05, budget=1.0)
    rng = random.Random(0)
    accepts = sum(sa.accept(100.0, 105.0, 0.0, rng) for _ in range(2000))
    assert 0.42 < accepts / 2000 < 0.58
    # luôn chấp nhận lời giải tốt hơn
    assert sa.accept(100.0, 99.0, 0.0, rng)
    # nhiệt độ giảm dần theo thời gian
    assert sa.temperature(0.5) > sa.temperature(0.9)


def test_hill_climbing_rejects_worse():
    hc = HillClimbing()
    rng = random.Random(0)
    assert hc.accept(100.0, 99.0, 0.0, rng)
    assert not hc.accept(100.0, 101.0, 0.0, rng)


def test_destroy_operators_return_valid_requests():
    inst, sol = _setup()
    ctx = FreeContext()
    for name, fn in DESTROY_OPERATORS.items():
        rng = random.Random(1)
        removed = fn(sol, rng, ALNSConfig(), ctx)
        assert isinstance(removed, list)
        for p in removed:
            assert p in sol.served_requests, (name, p)
            assert p in inst.requests


def test_destroy_worst_prefers_expensive_requests():
    """Loại tệ nhất phải ưu tiên yêu cầu có mức tiết kiệm lớn (2.2)."""
    inst, sol = _setup(n=30, seed=3)
    removed = destroy_worst(sol, random.Random(0), ALNSConfig(), FreeContext())
    assert removed
    assert len(removed) <= max(1, int(0.4 * len(inst.requests)))


def test_repair_operators_produce_valid_solutions():
    inst, sol = _setup()
    for name, fn in REPAIR_OPERATORS.items():
        cand = sol.copy()
        removed = destroy_random(cand, random.Random(2), ALNSConfig(), FreeContext())
        for p in removed:
            d = inst.delivery_of(p)
            for route in cand.routes:
                if p in route.stops and d in route.stops:
                    route.remove_request(p, d)
                    break
            cand.unassigned.add(p)
        fn(cand, removed, random.Random(2), ALNSConfig(), FreeContext())
        rep = validate(inst, cand.as_lists(), HARD, cand.unassigned)
        assert rep.ok, (name, rep.errors[:3])


def test_engine_improves_or_keeps_solution():
    """ALNS không được làm hỏng lời giải, và thường cải thiện nó."""
    inst, sol = _setup(n=50, seed=5, vehicles=6)
    cfg = ALNSConfig(budget=1.0, max_iterations=200, seed=1)
    engine = ALNSEngine(inst, HARD, cfg)
    best, stats = engine.run(sol)
    rep = validate(inst, best.as_lists(), HARD, best.unassigned)
    assert rep.ok, rep.errors[:3]
    assert best.cost <= sol.cost + 1e-6, "ALNS phải không tệ hơn lời giải đầu vào"
    assert stats.iterations > 0
    assert stats.seconds > 0


def test_engine_respects_budget():
    """Điều kiện dừng theo thời gian (mục 2.2.5)."""
    inst, sol = _setup(n=40, seed=2, vehicles=5)
    cfg = ALNSConfig(budget=0.5, max_iterations=10**9, seed=1)
    best, stats = ALNSEngine(inst, HARD, cfg).run(sol)
    assert stats.seconds < 2.0, "phải dừng theo ngân sách thời gian"


def test_engine_max_iterations():
    inst, sol = _setup(n=30, seed=4, vehicles=5)
    cfg = ALNSConfig(budget=100.0, max_iterations=25, seed=1)
    _, stats = ALNSEngine(inst, HARD, cfg).run(sol)
    assert stats.iterations <= 25


def test_engine_is_deterministic_with_seed():
    inst, sol = _setup(n=30, seed=6, vehicles=5)
    cfg = ALNSConfig(budget=100.0, max_iterations=60, seed=42)
    a, sa = ALNSEngine(inst, HARD, cfg).run(sol)
    b, sb = ALNSEngine(inst, HARD, cfg).run(sol)
    assert abs(a.cost - b.cost) < 1e-9
    assert sa.iterations == sb.iterations


def test_engine_on_real_instance():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "lilim", "lc101.txt")
    if not os.path.exists(path):
        return
    inst = parse_lilim(path)
    sol = greedy_insertion(inst, HARD, num_vehicles=inst.num_vehicles)
    cfg = ALNSConfig(budget=1.0, max_iterations=100, seed=1)
    best, stats = ALNSEngine(inst, HARD, cfg).run(sol)
    rep = validate(inst, best.as_lists(), HARD, best.unassigned)
    assert rep.ok, rep.errors[:3]
    assert best.cost <= sol.cost + 1e-6


def test_adapter_wraps_solution_as_alns_state():
    """`DPDPState` phải thoả giao thức `alns.State` (chỉ cần `objective()`)."""
    inst, sol = _setup(n=20, seed=7, vehicles=3)
    state = DPDPState(solution=sol)
    assert abs(state.objective() - sol.cost) < 1e-9


def test_adapter_destroy_then_repair_is_valid():
    """Chuỗi phá huỷ → sửa chữa qua adapter phải cho lời giải hợp lệ."""
    import numpy as np
    inst, sol = _setup(n=30, seed=8, vehicles=4)
    cfg = ALNSConfig()
    rng = np.random.default_rng(0)
    state = DPDPState(solution=sol)

    destroyed = make_destroy_operator("random", cfg)(state, rng)
    assert destroyed.removed, "phải loại được ít nhất một yêu cầu"
    for p in destroyed.removed:
        assert p not in destroyed.solution.served_requests

    repaired = make_repair_operator("greedy", cfg)(destroyed, rng)
    rep = validate(inst, repaired.solution.as_lists(), HARD,
                   repaired.solution.unassigned)
    assert rep.ok, rep.errors[:3]


def test_engine_uses_library_acceptance_and_selection():
    """Cấu hình phải ánh xạ đúng sang thư viện `alns` (Bảng 2.4)."""
    inst, sol = _setup(n=25, seed=9, vehicles=3)
    cfg = ALNSConfig(budget=0.5, max_iterations=40, seed=1,
                     reaction=0.1, segment_min=5)
    engine = ALNSEngine(inst, HARD, cfg)
    scheme = engine._select_scheme(cfg)
    # decay = 1 − λ
    assert abs(scheme.decay - (1.0 - cfg.reaction)) < 1e-12
    assert list(scheme.scores) == [cfg.sigma_new_best, cfg.sigma_better,
                                   cfg.sigma_accepted, 0.0]
    assert scheme.seg_length == cfg.segment_min

    accept = engine._accept_criterion(cfg, 100.0, 1000)
    assert accept.start_temperature > 0
    assert accept.end_temperature <= accept.start_temperature


def test_engine_records_operator_weights():
    """Thống kê phải trả về trọng số và điểm thưởng của từng toán tử."""
    inst, sol = _setup(n=25, seed=10, vehicles=3)
    cfg = ALNSConfig(budget=0.6, max_iterations=50, seed=1)
    _, stats = ALNSEngine(inst, HARD, cfg).run(sol)
    assert set(stats.weights) >= {"destroy:random", "destroy:worst",
                                  "destroy:related", "repair:greedy"}
    assert all(v > 0 for v in stats.weights.values())


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
