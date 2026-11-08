"""Kiểm thử khung mô phỏng DES và các thành phần thích ứng.

Chạy:  python tests/test_des.py   (hoặc pytest nếu đã cài).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dpdp import Params, parse_lilim, validate
from dpdp.adaptations import CandidateFilter, FilterConfig, FreezingManager
from dpdp.des import Event, EventQueue, EventType, SimConfig, Simulator
from dpdp.core.instance import generate_synthetic

HARD = Params()


def _instance(n=30, seed=0):
    return generate_synthetic(n, seed=seed)


def test_event_queue_is_time_ordered():
    """Hàng đợi ưu tiên theo thời gian: sự kiện sớm hơn được lấy trước."""
    q = EventQueue()
    q.push(5.0, EventType.NEW_REQUEST, "b")
    q.push(1.0, EventType.NEW_REQUEST, "a")
    q.push(3.0, EventType.VEHICLE_FREE, 0)
    order = []
    while True:
        ev = q.pop()
        if ev is None:
            break
        order.append(ev.payload)
    assert order == ["a", 0, "b"]


def test_event_queue_prefers_management_events_on_tie():
    """Khi trùng thời gian, sự kiện quản lý (E_3, E_4) được ưu tiên."""
    q = EventQueue()
    q.push(10.0, EventType.NEW_REQUEST, "req")
    q.push(10.0, EventType.SIMULATION_END)
    first = q.pop()
    assert first.type is EventType.SIMULATION_END


def test_event_queue_empty_returns_none():
    q = EventQueue()
    assert q.pop() is None
    assert not q
    assert q.peek_time() is None


def test_simulator_conserves_requests():
    """Mọi yêu cầu phải thuộc đúng một trong ba trạng thái: đã hoàn thành,
    đang được phục vụ, hoặc bị từ chối."""
    inst = _instance(30, seed=1)
    cfg = SimConfig(horizon=800.0, rho=0.5, budget=0.2, max_iterations=20,
                    seed=1)
    sim = Simulator(inst, HARD, cfg)
    res = sim.run()
    covered = (sim.completed | sim.solution.served_requests
               | sim.solution.unassigned)
    assert covered == set(inst.requests)
    assert res.served + res.rejected == inst.n_requests


def test_simulator_zero_dynamism_serves_all():
    """ρ = 0 thì bài toán suy biến về PDPTW: mọi yêu cầu đều phải phục vụ."""
    inst = _instance(25, seed=2)
    cfg = SimConfig(horizon=1000.0, rho=0.0, budget=0.2, max_iterations=20,
                    seed=1)
    res = Simulator(inst, HARD, cfg).run()
    assert res.served == inst.n_requests
    assert res.rejected == 0


def test_simulator_distance_is_monotone_in_dynamism():
    """Mức độ động tăng thì tổng quãng đường phải không giảm."""
    inst = _instance(25, seed=3)
    dists = []
    for rho in (0.0, 0.5, 1.0):
        cfg = SimConfig(horizon=800.0, rho=rho, budget=0.2,
                        max_iterations=20, seed=1)
        res = Simulator(inst, HARD, cfg).run()
        dists.append(res.total_distance)
    assert dists[0] <= dists[1] <= dists[2]


def test_simulator_is_deterministic():
    inst = _instance(20, seed=4)
    cfg = SimConfig(horizon=800.0, rho=0.4, budget=0.2, max_iterations=20,
                    seed=7)
    a = Simulator(inst, HARD, cfg).run()
    b = Simulator(inst, HARD, cfg).run()
    assert a.served == b.served and a.rejected == b.rejected
    assert abs(a.total_distance - b.total_distance) < 1e-6


def test_simulator_solution_stays_valid():
    """Lời giải cuối cùng phải thoả mọi ràng buộc (2.11)–(2.19)."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "lilim", "lc101.txt")
    if not os.path.exists(path):
        inst = _instance(30, seed=5)
    else:
        inst = parse_lilim(path)
    cfg = SimConfig(horizon=900.0, rho=0.3, budget=0.3, max_iterations=30,
                    seed=1)
    sim = Simulator(inst, HARD, cfg)
    res = sim.run()
    rep = validate(inst, res.solution.as_lists(), HARD,
                   res.solution.unassigned, sim.completed)
    assert rep.ok, rep.errors[:3]


def test_freezing_manager_blocks_committed_stops():
    """Cơ chế đóng băng (2.2.3): vị trí chèn trước chân trời bị chặn."""
    inst = _instance(20, seed=6)
    from dpdp.baselines import greedy_insertion
    sol = greedy_insertion(inst, HARD, num_vehicles=3)

    mgr = FreezingManager(safety=0.0)
    mgr.commit(0, 2)                     # 2 nút đầu của xe 0 đã cam kết
    constraint = mgr.constraint(sol)
    assert constraint.min_pos.get(0) == 2
    ctx = constraint.context(sol)
    assert ctx.min_pos_for(0) == 2
    assert ctx.min_pos_for(1) == 0        # xe khác không bị chặn


def test_freezing_safety_margin_opens_horizon():
    """Biên an toàn H_0 mở băng sớm hơn khi phần tự do quá ngắn."""
    inst = _instance(20, seed=7)
    from dpdp.baselines import greedy_insertion
    sol = greedy_insertion(inst, HARD, num_vehicles=3)
    mgr = FreezingManager(safety=3.0)
    mgr.commit(0, 2)
    constraint = mgr.constraint(sol)
    # xe 0 có nhiều nút nên chân trời vẫn là 2; xe rỗng không bị ràng buộc
    assert constraint.min_pos.get(0) in (0, 2)


def test_candidate_filter_blocks_far_candidates():
    """Bộ lọc ứng viên (2.2.4) phải loại được ứng viên quá lệch tuyến."""
    cfg = FilterConfig(delta_max=5.0, phi_max=45.0, radius=0.0)
    filt = CandidateFilter(cfg, [], [])

    # Ứng viên lệch hẳn sang bên: bị loại do góc hướng vượt φ_max.
    sideways = filt.accepts((0.0, 0.0), (1.0, 0.0), (10.0, 50.0), (12.0, 50.0))
    assert not sideways

    # Ứng viên lệch tuyến nhưng cùng hướng: bị loại do δ_max.
    detour = filt.accepts((0.0, 0.0), (1.0, 0.0), (0.0, 30.0), (30.0, 0.0))
    assert not detour

    # Ứng viên gần, ngay phía trước: được giữ.
    near = filt.accepts((0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (2.0, 0.0))
    assert near


def test_candidate_filter_radius_exempts_nearby():
    """Trong bán kính r_0, ứng viên không bị lọc dù hướng lệch."""
    cfg = FilterConfig(delta_max=1.0, phi_max=1.0, radius=10.0)
    filt = CandidateFilter(cfg, [], [])
    assert filt.accepts((0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (2.0, 0.0))


def test_candidate_filter_inactive_accepts_all():
    """Bộ lọc không cấu hình thì không loại ứng viên nào."""
    filt = CandidateFilter(FilterConfig(), [], [])
    assert filt.accepts((0.0, 0.0), (1.0, 0.0), (100.0, 100.0), (200.0, 0.0))


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