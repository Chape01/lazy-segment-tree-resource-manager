"""Scripted demo for presentation: runs the whole scenario without typing."""
from src.manager import CloudResourceManager
from src.models import Task
from src.observers import ConsoleLogger, StatsCollector


def bar(mgr, upto=16):
    free = mgr.usage_report()
    print("Slot: " + " ".join(f"{i:>2}" for i in range(upto)))
    print("Free: " + " ".join(f"{f:>2}" for f in free[:upto]))


def step(title):
    print("\n" + "=" * 60 + f"\n{title}\n" + "=" * 60)


mgr = CloudResourceManager(total_cpu=16, time_slots=24)
stats = StatsCollector()
mgr.add_observer(ConsoleLogger())
mgr.add_observer(stats)

step("1. Start: 16 CPU, 24 time slots, nothing allocated")
bar(mgr)

step("2. Allocate T1: 8 CPU in slots [0, 10)")
print("Result:", mgr.allocate(Task("T1", 0, 10, 8)).message)
bar(mgr)

step("3. Allocate T2: 8 CPU in slots [5, 15)  (overlaps T1 in slots 5-9)")
print("Result:", mgr.allocate(Task("T2", 5, 15, 8)).message)
bar(mgr)

step("4. Availability check: minimum free CPU in [5, 10)")
print("Minimum free CPU:", mgr.check_availability(5, 10))

step("5. Allocate T3: 1 CPU in slots [6, 8)  -> should be REJECTED")
print("Result:", mgr.allocate(Task("T3", 6, 8, 1)).message)

step("6. Release T1")
print("Released:", mgr.release("T1"))
bar(mgr)

step("7. Retry T3 -> should now be ACCEPTED")
print("Result:", mgr.allocate(Task("T3", 6, 8, 1)).message)
bar(mgr)

step("8. Monitoring")
print("Peak CPU in use   :", mgr.peak_usage())
print("Lowest CPU in use :", mgr.lowest_usage())
print(f"Average utilization: {mgr.average_utilization():.1%}")
print("Statistics:", vars(stats))