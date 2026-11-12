"""Kiểm thử bộ nạp dữ liệu mô phỏng từ mạng đường TP.HCM."""
from pathlib import Path

from dpdp import load_hcm_instance


ROOT = Path(__file__).resolve().parents[1]
HCM = ROOT / "dpdp_project/data/network_hcm"


def test_load_uniform_hcm_network():
    inst, release = load_hcm_instance(
        HCM / "hcm_uniform_100req_matrix.npz",
        HCM / "hcm_uniform_100req_requests.csv")
    assert inst.n_requests == 100
    assert len(release) == 100
    assert len(inst.dist) == len(inst.tt) == 201
    assert inst.dist[0][0] == 0.0
    assert all(0.0 <= t <= inst.nodes[p].l for p, t in release.items())


def test_load_clustered_hcm_network():
    inst, release = load_hcm_instance(
        HCM / "hcm_clustered_100req_matrix.npz",
        HCM / "hcm_clustered_100req_requests.csv")
    assert inst.n_requests == 100
    assert set(release) == set(inst.requests)
