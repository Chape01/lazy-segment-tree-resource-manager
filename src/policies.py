from abc import ABC, abstractmethod

class AdmissionPolicy(ABC):
    @abstractmethod
    def accept(self, min_available: int, requested: int, total: int) -> bool: ...

class StrictPolicy(AdmissionPolicy):
    """Accept only if the request fits fully."""
    def accept(self, min_available, requested, total):
        return min_available >= requested

class ReservePolicy(AdmissionPolicy):
    """Keep a safety buffer, e.g. 10% of capacity always free."""
    def __init__(self, reserve_ratio=0.1):
        self.reserve_ratio = reserve_ratio
    def accept(self, min_available, requested, total):
        return min_available - requested >= total * self.reserve_ratio