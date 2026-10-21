from .segment_tree import LazySegmentTree
from .models import Task, AllocationResult
from .policies import AdmissionPolicy, StrictPolicy


class CloudResourceManager:
    """Facade: hides the segment tree behind allocate / release / monitor calls.

    The tree stores FREE CPU for every time slot.
    Task intervals are [start, end) (end exclusive); the tree uses inclusive
    indices, so we always pass end - 1 to it.
    """

    def __init__(self, total_cpu, time_slots, policy: AdmissionPolicy = None):
        if total_cpu <= 0 or time_slots <= 0:
            raise ValueError("total_cpu and time_slots must be positive")
        self.total_cpu = total_cpu
        self.time_slots = time_slots
        self.tree = LazySegmentTree(size=time_slots, initial=total_cpu)
        self.policy = policy or StrictPolicy()
        self.tasks: dict[str, Task] = {}
        self.observers = []

    # ---------------- observers ----------------
    def add_observer(self, obs):
        self.observers.append(obs)

    def _emit(self, event, task_id, detail):
        for o in self.observers:
            o.notify(event, task_id, detail)

    # ---------------- validation ----------------
    def _validate_interval(self, start, end):
        if not (0 <= start < end <= self.time_slots):
            raise ValueError(
                f"Invalid time interval [{start}, {end}); "
                f"valid slots are 0..{self.time_slots}")

    def _validate(self, task: Task):
        self._validate_interval(task.start, task.end)
        if task.cpu <= 0 or task.cpu > self.total_cpu:
            raise ValueError("Invalid CPU request")

    # ---------------- availability ----------------
    def check_availability(self, start, end):
        """Minimum free CPU over [start, end)."""
        self._validate_interval(start, end)
        return self.tree.range_min(start, end - 1)

    def can_fit(self, start, end, cpu) -> bool:
        """Dry run: would this request be accepted? (does not change state)"""
        self._validate_interval(start, end)
        free = self.tree.range_min(start, end - 1)
        return self.policy.accept(free, cpu, self.total_cpu)

    def first_conflict_slot(self, start, end, cpu) -> int:
        """First time slot in [start, end) with less than `cpu` free, or -1."""
        self._validate_interval(start, end)
        return self.tree.find_first_less(start, end - 1, cpu)

    # ---------------- allocate / release ----------------
    def allocate(self, task: Task) -> AllocationResult:
        self._validate(task)
        if task.task_id in self.tasks:
            raise ValueError("Duplicate task id")

        free = self.check_availability(task.start, task.end)

        if self.policy.accept(free, task.cpu, self.total_cpu):
            self.tree.range_add(task.start, task.end - 1, -task.cpu)
            self.tasks[task.task_id] = task
            self._emit("ACCEPTED", task.task_id,
                       f"{task.cpu} CPU [{task.start},{task.end})")
            return AllocationResult(True, "Accepted", free - task.cpu)

        slot = self.first_conflict_slot(task.start, task.end, task.cpu)
        if slot != -1:
            reason = (f"Rejected: not enough CPU at slot {slot} "
                      f"(free {self.tree.point_query(slot)}, needs {task.cpu})")
        else:
            reason = "Rejected: violates the reserve policy"
        self._emit("REJECTED", task.task_id, reason)
        return AllocationResult(False, reason, free)

    def release(self, task_id) -> bool:
        task = self.tasks.pop(task_id, None)
        if task is None:
            return False
        self.tree.range_add(task.start, task.end - 1, task.cpu)
        self._emit("RELEASED", task_id, f"{task.cpu} CPU returned")
        return True

    # ---------------- monitoring ----------------
    def usage_report(self):
        """Free CPU for every slot."""
        return self.tree.to_list()

    def peak_usage(self, start=0, end=None):
        """Highest CPU in use in [start, end)."""
        end = self.time_slots if end is None else end
        self._validate_interval(start, end)
        return self.total_cpu - self.tree.range_min(start, end - 1)

    def lowest_usage(self, start=0, end=None):
        """Lowest CPU in use in [start, end)."""
        end = self.time_slots if end is None else end
        self._validate_interval(start, end)
        return self.total_cpu - self.tree.range_max(start, end - 1)

    def average_utilization(self, start=0, end=None):
        """Average utilization (0.0 - 1.0) over [start, end)."""
        end = self.time_slots if end is None else end
        self._validate_interval(start, end)
        slots = end - start
        free_sum = self.tree.range_sum(start, end - 1)
        used_sum = self.total_cpu * slots - free_sum
        return used_sum / (self.total_cpu * slots)

    def active_tasks(self):
        return list(self.tasks.values())