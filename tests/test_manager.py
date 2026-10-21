import pytest
from src.manager import CloudResourceManager
from src.models import Task
from src.policies import ReservePolicy
from src.observers import StatsCollector


@pytest.fixture
def mgr():
    return CloudResourceManager(total_cpu=16, time_slots=24)


def test_accept_when_capacity_available(mgr):
    r = mgr.allocate(Task("T1", 0, 10, 8))
    assert r.accepted and r.available_min == 8


def test_overlapping_tasks_accepted_until_full(mgr):
    assert mgr.allocate(Task("T1", 0, 10, 8)).accepted
    assert mgr.allocate(Task("T2", 5, 15, 8)).accepted
    assert mgr.check_availability(5, 10) == 0


def test_reject_when_insufficient_capacity(mgr):
    mgr.allocate(Task("T1", 0, 10, 8))
    mgr.allocate(Task("T2", 5, 15, 8))
    r = mgr.allocate(Task("T3", 6, 8, 1))
    assert not r.accepted
    assert "slot 6" in r.message


def test_rejected_task_does_not_change_state(mgr):
    mgr.allocate(Task("T1", 0, 10, 16))
    before = mgr.usage_report()
    assert not mgr.allocate(Task("T2", 0, 10, 1)).accepted
    assert mgr.usage_report() == before


def test_release_frees_capacity_for_new_task(mgr):
    mgr.allocate(Task("T1", 0, 10, 8))
    mgr.allocate(Task("T2", 5, 15, 8))
    assert not mgr.allocate(Task("T3", 6, 8, 1)).accepted
    assert mgr.release("T1")
    assert mgr.allocate(Task("T3", 6, 8, 1)).accepted


def test_release_unknown_task_returns_false(mgr):
    assert mgr.release("nope") is False


def test_double_release_is_safe(mgr):
    mgr.allocate(Task("T1", 0, 5, 4))
    assert mgr.release("T1")
    assert not mgr.release("T1")
    assert mgr.usage_report() == [16] * 24


def test_non_overlapping_tasks_use_full_capacity(mgr):
    assert mgr.allocate(Task("A", 0, 5, 16)).accepted
    assert mgr.allocate(Task("B", 5, 10, 16)).accepted


def test_adjacent_intervals_do_not_conflict(mgr):
    mgr.allocate(Task("A", 0, 5, 16))
    assert mgr.allocate(Task("B", 5, 8, 16)).accepted   # end is exclusive


def test_exact_fit_is_accepted(mgr):
    assert mgr.allocate(Task("A", 0, 24, 16)).accepted
    assert mgr.check_availability(0, 24) == 0


def test_invalid_requests_raise(mgr):
    with pytest.raises(ValueError):
        mgr.allocate(Task("X", 5, 5, 1))        # empty interval
    with pytest.raises(ValueError):
        mgr.allocate(Task("X", 0, 30, 1))       # beyond time range
    with pytest.raises(ValueError):
        mgr.allocate(Task("X", 0, 5, 99))       # more than total CPU
    with pytest.raises(ValueError):
        mgr.allocate(Task("X", 0, 5, 0))        # zero CPU


def test_duplicate_task_id_rejected(mgr):
    mgr.allocate(Task("T1", 0, 5, 2))
    with pytest.raises(ValueError):
        mgr.allocate(Task("T1", 6, 8, 2))


def test_monitoring_metrics(mgr):
    mgr.allocate(Task("T1", 0, 10, 8))
    mgr.allocate(Task("T2", 5, 15, 8))
    assert mgr.peak_usage() == 16
    assert mgr.lowest_usage() == 0
    expected = sum(16 - f for f in mgr.usage_report()) / (16 * 24)
    assert mgr.average_utilization() == pytest.approx(expected)


def test_can_fit_is_a_dry_run(mgr):
    mgr.allocate(Task("T1", 0, 10, 10))
    assert mgr.can_fit(0, 10, 6)
    assert not mgr.can_fit(0, 10, 7)
    assert mgr.usage_report()[0] == 6


def test_reserve_policy_keeps_buffer():
    m = CloudResourceManager(10, 5, ReservePolicy(0.2))
    assert m.allocate(Task("A", 0, 5, 8)).accepted
    r = m.allocate(Task("B", 0, 5, 1))
    assert not r.accepted and "reserve" in r.message


def test_observer_counts():
    m = CloudResourceManager(4, 5)
    s = StatsCollector(); m.add_observer(s)
    m.allocate(Task("A", 0, 5, 4))
    m.allocate(Task("B", 0, 5, 1))
    m.release("A")
    assert (s.accepted, s.rejected, s.released) == (1, 1, 1)