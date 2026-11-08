"""Lộ trình của một xe và thao tác chèn / loại yêu cầu.

Mô hình thời gian (khớp mục 2.2.1 của báo cáo):
  - xe rời kho tại thời điểm e_0, được phép chờ tại nút đến sớm;
  - điểm lấy: khung thời gian cứng [e, l];
  - điểm giao: cận dưới cứng e, cận trên mềm l với độ trễ tối đa L̄ = late_max
    (late_max = 0 nghĩa là khung cứng, đúng bộ Li & Lim gốc);
  - mục tiêu của lộ trình: α·quãng đường + γ·tổng độ trễ.

Route luôn ở trạng thái KHẢ THI: mọi thao tác làm hỏng khả thi đều ném
InfeasibleRoute thay vì âm thầm lưu lộ trình sai.
"""
from __future__ import annotations

from dataclasses import dataclass

from .instance import Instance

EPS = 1e-9
INF = float("inf")


@dataclass(frozen=True)
class Params:
    alpha: float = 1.0       # trọng số quãng đường
    beta: float = 1000.0     # phạt mỗi yêu cầu bị từ chối (xem Nhận xét 2.4)
    gamma: float = 0.25      # trọng số độ trễ
    late_max: float = 0.0    # L̄: độ trễ tối đa tại điểm giao (0 = khung cứng)


class InfeasibleRoute(Exception):
    pass


class Route:
    def __init__(self, inst: Instance, params: Params, stops=()):
        self.inst = inst
        self.params = params
        self._nodes = inst.nodes
        self._tt = inst.tt
        self._dist = inst.dist
        self._cap = inst.capacity
        self.stops: list[int] = list(stops)
        self._refresh()

    # ------------------------------------------------------------ cơ bản
    def _serve(self, prev: int, tdep: float, load: float, nid: int):
        """Phục vụ nút nid sau khi rời prev lúc tdep.

        Trả về (thời điểm rời nút, tải sau phục vụ, độ trễ) hoặc None nếu vi phạm.
        """
        nd = self._nodes[nid]
        arr = tdep + self._tt[prev][nid]
        if arr < nd.e:
            arr = nd.e
        load += nd.demand
        if load > self._cap + EPS:
            return None
        if nd.delivery:                       # nút lấy hàng: khung cứng
            if arr > nd.l + EPS:
                return None
            late = 0.0
        else:                                 # nút giao hàng: cận trên mềm
            over = arr - nd.l
            if over > self.params.late_max + EPS:
                return None
            late = over if over > 0.0 else 0.0
        return arr + nd.s, load, late

    def _check_structure(self) -> None:
        """Mỗi nút tối đa một lần; lấy trước giao; cặp lấy–giao đủ cả hai."""
        nodes, seen = self._nodes, set()
        for nid in self.stops:
            if not (0 < nid < len(nodes)):
                raise InfeasibleRoute(f"nút {nid} không hợp lệ")
            if nid in seen:
                raise InfeasibleRoute(f"nút {nid} bị thăm hai lần")
            nd = nodes[nid]
            if nd.is_delivery and nd.pickup not in seen:
                raise InfeasibleRoute(f"điểm giao {nid} đứng trước điểm lấy {nd.pickup}")
            seen.add(nid)
        for nid in seen:
            nd = nodes[nid]
            if nd.is_pickup and nd.delivery not in seen:
                raise InfeasibleRoute(f"thiếu điểm giao {nd.delivery} của điểm lấy {nid}")

    def _refresh(self) -> None:
        nodes, dist, serve = self._nodes, self._dist, self._serve
        depot = nodes[0]
        self._check_structure()
        prev, t, load, D, L = 0, depot.e, 0.0, 0.0, 0.0
        pre = [(prev, t, load, D, L)]        # trạng thái TRƯỚC mỗi vị trí
        dep, lat = [], []
        for nid in self.stops:
            r = serve(prev, t, load, nid)
            if r is None:
                raise InfeasibleRoute(f"vi phạm tại nút {nid}")
            D += dist[prev][nid]
            t, load, late = r
            L += late
            prev = nid
            pre.append((prev, t, load, D, L))
            dep.append(t)
            lat.append(late)
        if t + self._tt[prev][0] > depot.l + EPS:
            raise InfeasibleRoute("về kho quá muộn")
        D += dist[prev][0]

        m = len(self.stops)
        rem_d, rem_l = [0.0] * m, [0.0] * m  # phần còn lại SAU nút k
        if m:
            acc_d, acc_l = dist[self.stops[-1]][0], 0.0
            for k in range(m - 1, -1, -1):
                rem_d[k], rem_l[k] = acc_d, acc_l
                acc_l += lat[k]
                if k > 0:
                    acc_d += dist[self.stops[k - 1]][self.stops[k]]
        self.pre, self.dep, self.rem_d, self.rem_l = pre, dep, rem_d, rem_l
        self.total_dist, self.total_late = D, L

    # ------------------------------------------------------------ truy vấn
    @property
    def cost(self) -> float:
        p = self.params
        return p.alpha * self.total_dist + p.gamma * self.total_late

    def __len__(self) -> int:
        return len(self.stops)

    def can_serve(self, p: int, d: int) -> bool:
        """Điều kiện khả thi SƠ BỘ của việc phục vụ cặp (p, d) trên xe này.

        Chỉ kiểm tra: sức chứa còn đủ, và cặp lấy–giao có thời gian hợp lệ nếu
        xe chạy thẳng từ kho (bỏ qua các nút đã có trong lộ trình). Đây là điều
        kiện *cần thiết*, nên tập xe trả về là superset của tập xe thực sự
        khả thi — dùng cho thành phần ω_4 của công thức (2.3) với chi phí O(1)
        thay vì gọi `best_insertion` (O(m²)) cho mọi xe.
        """
        nodes, tt = self._nodes, self._tt
        demand = nodes[p].demand + nodes[d].demand
        if demand > self._cap + EPS:
            return False
        t = max(self._nodes[0].e, nodes[p].e)
        if t > nodes[p].l + EPS:
            return False                      # không tới được điểm lấy đúng hạn
        arr_p = t + tt[0][p]
        if arr_p > nodes[p].l + EPS:
            return False
        arr_d = arr_p + nodes[p].s + tt[p][d]
        if arr_d > nodes[d].l + self.params.late_max + EPS:
            return False                      # giao trễ quá L̄
        return True

    def copy(self) -> "Route":
        return Route(self.inst, self.params, self.stops)

    # ------------------------------------------------------------ chèn / loại
    def best_insertion(self, p: int, d: int, min_pos: int = 0,
                       noise: float = 0.0, rng=None, dmax: float = 0.0):
        """Vị trí chèn tốt nhất cặp (p, d) -> (Δ chi phí, i, j) hoặc None.

        Thứ tự sau khi chèn: stops[:i] + [p] + stops[i:j] + [d] + stops[j:], i ≤ j.

        Tham số:
            min_pos: chỉ xét các vị trí chèn từ `min_pos` trở đi. Dùng cho cơ chế
                đóng băng (mục 2.2.3): `min_pos` = độ dài tiền tố đã đóng băng,
                nên ALNS chỉ được thay đổi phần tự do của lộ trình.
            noise:  η trong công thức (2.5). Khi η > 0, mỗi Δ ứng viên được cộng
                nhiễu `η·dmax·ε`, ε ~ U(−1, 1), và chọn theo Δ′ = max{0, Δ + nhiễu}.
                Cần truyền `rng` và `dmax` (khoảng cách lớn nhất giữa hai điểm).

        Cắt tỉa: (1) bỏ i nếu không đến p được; (2) dừng tăng j khi đoạn
        p→stops[i..j-1] đã vi phạm; (3) khi thời điểm rời nút trùng với lộ
        trình gốc thì phần đuôi giữ nguyên nên cộng luôn phần còn lại.
        """
        stops, m, pre = self.stops, len(self.stops), self.pre
        serve, dist, tt = self._serve, self._dist, self._tt
        alpha, gamma = self.params.alpha, self.params.gamma
        depot_l = self._nodes[0].l
        base_d, base_l = self.total_dist, self.total_late
        dep, rem_d, rem_l = self.dep, self.rem_d, self.rem_l
        best, best_delta = None, INF

        for i in range(min_pos, m + 1):
            prev0, t0, load0, d0, l0 = pre[i]
            r = serve(prev0, t0, load0, p)
            if r is None:
                continue
            t, load, late = r
            dd = d0 + dist[prev0][p]
            ll = l0 + late
            prev = p
            j = i
            while True:
                rd = serve(prev, t, load, d)         # thử chèn d trước stops[j]
                if rd is not None:
                    t2, load2, late2 = rd
                    d2 = dd + dist[prev][d]
                    l2 = ll + late2
                    pv, ok, done = d, True, False
                    for k in range(j, m):
                        nid = stops[k]
                        rs = serve(pv, t2, load2, nid)
                        if rs is None:
                            ok = False
                            break
                        d2 += dist[pv][nid]
                        t2, load2, lt = rs
                        l2 += lt
                        pv = nid
                        if abs(t2 - dep[k]) <= EPS:  # đuôi không đổi
                            d2 += rem_d[k]
                            l2 += rem_l[k]
                            done = True
                            break
                    if ok and not done:
                        if t2 + tt[pv][0] > depot_l + EPS:
                            ok = False
                        else:
                            d2 += dist[pv][0]
                    if ok:
                        delta = alpha * (d2 - base_d) + gamma * (l2 - base_l)
                        if noise > 0.0:
                            eps = rng.uniform(-1.0, 1.0)
                            delta = max(0.0, delta + noise * dmax * eps)
                        if delta < best_delta - 1e-12:
                            best_delta, best = delta, (delta, i, j)
                if j == m:
                    break
                nid = stops[j]                        # đi tiếp mà chưa chèn d
                rs = serve(prev, t, load, nid)
                if rs is None:
                    break
                dd += dist[prev][nid]
                t, load, lt = rs
                ll += lt
                prev = nid
                j += 1
        return best

    def insert(self, p: int, d: int, i: int, j: int) -> None:
        s = self.stops
        self.stops = s[:i] + [p] + s[i:j] + [d] + s[j:]
        try:
            self._refresh()
        except InfeasibleRoute:
            self.stops = s
            self._refresh()
            raise

    def remove_request(self, p: int, d: int) -> None:
        """Loại yêu cầu (p, d). Luôn giữ khả thi (Bổ đề 2.1) vì xe được chờ."""
        self.stops = [x for x in self.stops if x != p and x != d]
        self._refresh()
