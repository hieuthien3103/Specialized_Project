"""Bộ chuyển đổi RNG giữa `numpy.random.Generator` và API `random.Random`.

Thư viện `alns` (Wouda & Lan [20]) truyền `numpy.random.Generator` cho các
toán tử, trong khi các toán tử trong `operators.py` được viết theo API quen
thuộc của `random.Random`. Lớp này cung cấp lại đúng các phương thức mà
toán tử dùng, để một bộ toán tử có thể chạy được với RNG của cả hai thư viện
(thuận tiện cho việc đối chiếu tính đúng đắn theo mục "Công cụ cài đặt" của
báo cáo).

Lưu ý: `sample` trả về các phần tử theo thứ tự ngẫu nhiên, khác với
`random.sample` về thứ tự, nhưng tập phần tử là như nhau nên không ảnh hưởng
tính đúng đắn của thuật toán.
"""
from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class RNGAdapter:
    """Bọc `numpy.random.Generator` (hoặc `random.Random`) thành API thống nhất."""

    def __init__(self, rng):
        self._rng = rng

    # -------------------------------------------------------------- sinh số
    def random(self) -> float:
        """Số thực trong [0, 1)."""
        return float(self._rng.random())

    def randint(self, a: int, b: int) -> int:
        """Số nguyên trong [a, b] (bao gồm cả hai đầu)."""
        if hasattr(self._rng, "integers"):        # numpy.random.Generator
            return int(self._rng.integers(a, b + 1))
        return int(self._rng.randint(a, b))

    def uniform(self, a: float, b: float) -> float:
        """Số thực trong [a, b)."""
        return float(self._rng.uniform(a, b))

    def choice(self, seq: Sequence[T]) -> T:
        """Chọn ngẫu nhiên một phần tử của `seq`."""
        return self._rng.choice(list(seq))

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        """Chọn ngẫu nhiên `k` phần tử khác nhau (không lặp lại)."""
        pop = list(population)
        if k >= len(pop):
            return pop
        if hasattr(self._rng, "choice"):          # numpy.random.Generator
            idx = self._rng.choice(len(pop), size=k, replace=False)
            return [pop[int(i)] for i in idx]
        return self._rng.sample(pop, k)

    def shuffle(self, seq: list) -> None:
        """Trộn thứ tự của `seq` tại chỗ."""
        if hasattr(self._rng, "shuffle"):
            self._rng.shuffle(seq)
        else:
            self._rng.shuffle(seq)

    # ---------------------------------------------------------------- khác
    def spawn(self, seed: int) -> "RNGAdapter":
        """Sinh RNG con với seed xác định (dùng để tái lập thực nghiệm)."""
        return RNGAdapter(random.Random(seed))


def make_rng(seed: int | None = None) -> RNGAdapter:
    """Tạo RNG thống nhất từ seed.

    Dùng `random.Random` để kết quả tái lập được độc lập phiên bản numpy.
    """
    return RNGAdapter(random.Random(seed))
