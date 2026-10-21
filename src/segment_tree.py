"""
Lazy Segment Tree: complete implementation.

Each node stores, for its segment: minimum, maximum and sum.
Lazy tags per node: a pending "assign" value (or None) and a pending "add" value.
All indices are 0-based and INCLUSIVE: [l, r].

Operation                      Complexity
-----------------------------  -----------
build                          O(n)
range_add / point_add          O(log n)
range_assign / point_set       O(log n)
range_min / max / sum          O(log n)
point_query                    O(log n)
find_first_less / find_first_geq  O(log n)
to_list                        O(n)
"""

from typing import List, Optional, Sequence

INF = float("inf")


class LazySegmentTree:
    def __init__(self, size: Optional[int] = None, initial: int = 0,
                 data: Optional[Sequence[int]] = None):
        """Build from `data`, or from `size` copies of `initial`."""
        if data is not None:
            values = list(data)
        else:
            if size is None or size <= 0:
                raise ValueError("size must be a positive integer")
            values = [initial] * size
        if len(values) == 0:
            raise ValueError("cannot build an empty tree")

        self.n = len(values)
        self.mn = [0] * (4 * self.n)
        self.mx = [0] * (4 * self.n)
        self.sm = [0] * (4 * self.n)
        self.assign_tag: List[Optional[int]] = [None] * (4 * self.n)
        self.add_tag = [0] * (4 * self.n)
        self._build(1, 0, self.n - 1, values)

    # ------------------------------------------------------------------ #
    # Basic helpers
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return self.n

    def __getitem__(self, i: int) -> int:
        return self.point_query(i)

    def _check_range(self, l: int, r: int) -> None:
        if not (0 <= l <= r < self.n):
            raise IndexError(f"range [{l}, {r}] outside [0, {self.n - 1}]")

    def _check_index(self, i: int) -> None:
        if not (0 <= i < self.n):
            raise IndexError(f"index {i} outside [0, {self.n - 1}]")

    def _pull(self, node: int) -> None:
        """Recompute a node from its two children."""
        a, b = 2 * node, 2 * node + 1
        self.mn[node] = min(self.mn[a], self.mn[b])
        self.mx[node] = max(self.mx[a], self.mx[b])
        self.sm[node] = self.sm[a] + self.sm[b]

    def _apply_assign(self, node: int, length: int, v: int) -> None:
        self.mn[node] = v
        self.mx[node] = v
        self.sm[node] = v * length
        self.assign_tag[node] = v
        self.add_tag[node] = 0

    def _apply_add(self, node: int, length: int, v: int) -> None:
        self.mn[node] += v
        self.mx[node] += v
        self.sm[node] += v * length
        if self.assign_tag[node] is not None:
            self.assign_tag[node] += v      # fold the add into the assignment
        else:
            self.add_tag[node] += v

    def _push(self, node: int, l: int, r: int) -> None:
        """Send pending lazy tags of `node` down to its children."""
        m = (l + r) // 2
        left_len, right_len = m - l + 1, r - m
        if self.assign_tag[node] is not None:
            v = self.assign_tag[node]
            self._apply_assign(2 * node, left_len, v)
            self._apply_assign(2 * node + 1, right_len, v)
            self.assign_tag[node] = None
        if self.add_tag[node] != 0:
            v = self.add_tag[node]
            self._apply_add(2 * node, left_len, v)
            self._apply_add(2 * node + 1, right_len, v)
            self.add_tag[node] = 0

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #
    def _build(self, node: int, l: int, r: int, values: Sequence[int]) -> None:
        if l == r:
            self.mn[node] = self.mx[node] = self.sm[node] = values[l]
            return
        m = (l + r) // 2
        self._build(2 * node, l, m, values)
        self._build(2 * node + 1, m + 1, r, values)
        self._pull(node)

    def reset(self, value: int = 0) -> None:
        """Set every element to `value` in O(1) (lazy assign at the root)."""
        self._apply_assign(1, self.n, value)

    # ------------------------------------------------------------------ #
    # Updates
    # ------------------------------------------------------------------ #
    def range_add(self, l: int, r: int, v: int) -> None:
        self._check_range(l, r)
        self._add(1, 0, self.n - 1, l, r, v)

    def _add(self, node, l, r, ql, qr, v) -> None:
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self._apply_add(node, r - l + 1, v)
            return
        self._push(node, l, r)
        m = (l + r) // 2
        self._add(2 * node, l, m, ql, qr, v)
        self._add(2 * node + 1, m + 1, r, ql, qr, v)
        self._pull(node)

    def range_assign(self, l: int, r: int, v: int) -> None:
        self._check_range(l, r)
        self._assign(1, 0, self.n - 1, l, r, v)

    def _assign(self, node, l, r, ql, qr, v) -> None:
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self._apply_assign(node, r - l + 1, v)
            return
        self._push(node, l, r)
        m = (l + r) // 2
        self._assign(2 * node, l, m, ql, qr, v)
        self._assign(2 * node + 1, m + 1, r, ql, qr, v)
        self._pull(node)

    def point_add(self, i: int, v: int) -> None:
        self._check_index(i)
        self._add(1, 0, self.n - 1, i, i, v)

    def point_set(self, i: int, v: int) -> None:
        self._check_index(i)
        self._assign(1, 0, self.n - 1, i, i, v)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def range_min(self, l: int, r: int):
        self._check_range(l, r)
        return self._query(1, 0, self.n - 1, l, r, self.mn, min, INF)

    def range_max(self, l: int, r: int):
        self._check_range(l, r)
        return self._query(1, 0, self.n - 1, l, r, self.mx, max, -INF)

    def range_sum(self, l: int, r: int):
        self._check_range(l, r)
        return self._query(1, 0, self.n - 1, l, r, self.sm,
                           lambda a, b: a + b, 0)

    def point_query(self, i: int) -> int:
        self._check_index(i)
        return self._query(1, 0, self.n - 1, i, i, self.sm,
                           lambda a, b: a + b, 0)

    def _query(self, node, l, r, ql, qr, arr, combine, neutral):
        if qr < l or r < ql:
            return neutral
        if ql <= l and r <= qr:
            return arr[node]
        self._push(node, l, r)
        m = (l + r) // 2
        return combine(
            self._query(2 * node, l, m, ql, qr, arr, combine, neutral),
            self._query(2 * node + 1, m + 1, r, ql, qr, arr, combine, neutral),
        )

    # ------------------------------------------------------------------ #
    # Search (tree descent)
    # ------------------------------------------------------------------ #
    def find_first_less(self, l: int, r: int, x: int) -> int:
        """Leftmost index in [l, r] with value < x, or -1. O(log n)."""
        self._check_range(l, r)
        return self._find(1, 0, self.n - 1, l, r, x, less=True)

    def find_first_geq(self, l: int, r: int, x: int) -> int:
        """Leftmost index in [l, r] with value >= x, or -1. O(log n)."""
        self._check_range(l, r)
        return self._find(1, 0, self.n - 1, l, r, x, less=False)

    def _find(self, node, l, r, ql, qr, x, less) -> int:
        if qr < l or r < ql:
            return -1
        if less and self.mn[node] >= x:      # nothing smaller here
            return -1
        if not less and self.mx[node] < x:   # nothing large enough here
            return -1
        if l == r:
            return l
        self._push(node, l, r)
        m = (l + r) // 2
        res = self._find(2 * node, l, m, ql, qr, x, less)
        if res != -1:
            return res
        return self._find(2 * node + 1, m + 1, r, ql, qr, x, less)

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #
    def to_list(self) -> List[int]:
        """Return all element values (pushes every lazy tag down). O(n)."""
        out: List[int] = []
        self._collect(1, 0, self.n - 1, out)
        return out

    def _collect(self, node, l, r, out) -> None:
        if l == r:
            out.append(self.sm[node])
            return
        self._push(node, l, r)
        m = (l + r) // 2
        self._collect(2 * node, l, m, out)
        self._collect(2 * node + 1, m + 1, r, out)

    def __repr__(self) -> str:
        return f"LazySegmentTree({self.to_list()})"