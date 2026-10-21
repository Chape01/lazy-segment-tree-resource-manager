from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    task_id: str
    start: int      # inclusive time slot
    end: int        # exclusive time slot
    cpu: int

@dataclass
class AllocationResult:
    accepted: bool
    message: str
    available_min: int | float