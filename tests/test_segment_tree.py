import random
import pytest
from src.segment_tree import LazySegmentTree


def make_pair(n=30, lo=-20, hi=20):
    init = [random.randint(lo, hi) for _ in range(n)]
    return LazySegmentTree(data=init), init[:]


def rand_range(n):
    l = random.randint(0, n - 1)
    return l, random.randint(l, n - 1)


def test_build_from_size_and_initial():
    t = LazySegmentTree(size=5, initial=7)
    assert t.to_list() == [7] * 5
    assert len(t) == 5


def test_build_from_list():
    t = LazySegmentTree(data=[4, 1, 3])
    assert t.to_list() == [4, 1, 3]
    assert t[1] == 1


def test_range_add_and_min():
    t = LazySegmentTree(size=10, initial=10)
    t.range_add(2, 5, -4)
    assert t.range_min(0, 9) == 6
    assert t.range_min(0, 1) == 10
    assert t.range_min(3, 4) == 6


def test_range_assign():
    t = LazySegmentTree(size=8, initial=5)
    t.range_assign(2, 4, 0)
    assert t.to_list() == [5, 5, 0, 0, 0, 5, 5, 5]


def test_assign_then_add_composes_correctly():
    t = LazySegmentTree(size=6, initial=1)
    t.range_assign(0, 5, 10)
    t.range_add(1, 3, 5)
    assert t.to_list() == [10, 15, 15, 15, 10, 10]


def test_point_operations():
    t = LazySegmentTree(size=5, initial=0)
    t.point_set(2, 9)
    t.point_add(2, -3)
    assert t.point_query(2) == 6


def test_range_max_and_sum():
    t = LazySegmentTree(data=[3, 8, 1, 9, 2])
    assert t.range_max(0, 2) == 8
    assert t.range_sum(1, 3) == 18
    t.range_add(0, 4, 1)
    assert t.range_sum(0, 4) == 28


def test_find_first_less_and_geq():
    t = LazySegmentTree(data=[5, 5, 2, 5, 1, 5])
    assert t.find_first_less(0, 5, 3) == 2
    assert t.find_first_less(3, 5, 3) == 4
    assert t.find_first_less(0, 1, 3) == -1
    assert t.find_first_geq(2, 5, 5) == 3
    assert t.find_first_geq(4, 4, 5) == -1


def test_reset():
    t = LazySegmentTree(size=6, initial=3)
    t.range_add(0, 2, 4)
    t.reset(9)
    assert t.to_list() == [9] * 6


def test_invalid_inputs_raise():
    t = LazySegmentTree(size=5, initial=1)
    with pytest.raises(IndexError):
        t.range_add(-1, 2, 1)
    with pytest.raises(IndexError):
        t.range_min(3, 9)
    with pytest.raises(IndexError):
        t.point_query(5)
    with pytest.raises(ValueError):
        LazySegmentTree(size=0)


def test_single_element_tree():
    t = LazySegmentTree(size=1, initial=4)
    t.range_add(0, 0, -1)
    assert t.range_min(0, 0) == 3


def test_all_operations_against_bruteforce():
    random.seed(7)
    for _ in range(200):
        n = random.randint(1, 40)
        t, a = make_pair(n)
        for _ in range(200):
            l, r = rand_range(n)
            v = random.randint(-10, 10)
            op = random.choice(["add", "assign", "min", "max", "sum",
                                "point", "less", "geq", "list"])
            if op == "add":
                t.range_add(l, r, v); a[l:r + 1] = [x + v for x in a[l:r + 1]]
            elif op == "assign":
                t.range_assign(l, r, v); a[l:r + 1] = [v] * (r - l + 1)
            elif op == "min":
                assert t.range_min(l, r) == min(a[l:r + 1])
            elif op == "max":
                assert t.range_max(l, r) == max(a[l:r + 1])
            elif op == "sum":
                assert t.range_sum(l, r) == sum(a[l:r + 1])
            elif op == "point":
                assert t.point_query(l) == a[l]
            elif op == "less":
                exp = next((i for i in range(l, r + 1) if a[i] < v), -1)
                assert t.find_first_less(l, r, v) == exp
            elif op == "geq":
                exp = next((i for i in range(l, r + 1) if a[i] >= v), -1)
                assert t.find_first_geq(l, r, v) == exp
            else:
                assert t.to_list() == a