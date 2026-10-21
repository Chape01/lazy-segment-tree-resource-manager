from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def notify(self, event: str, task_id: str, detail: str): ...

class ConsoleLogger(Observer):
    def notify(self, event, task_id, detail):
        print(f"[{event}] {task_id}: {detail}")

class StatsCollector(Observer):
    def __init__(self):
        self.accepted = self.rejected = self.released = 0
    def notify(self, event, task_id, detail):
        if event == "ACCEPTED": self.accepted += 1
        elif event == "REJECTED": self.rejected += 1
        elif event == "RELEASED": self.released += 1