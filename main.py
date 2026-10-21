from src.manager import CloudResourceManager
from src.models import Task
from src.observers import ConsoleLogger, StatsCollector
from src.policies import StrictPolicy, ReservePolicy

MENU = """
===== Cloud Resource Allocation & Monitoring =====
 1. Allocate a task
 2. Release a task
 3. Check availability (min free CPU over an interval)
 4. Dry run: would a request fit?
 5. Usage report (free CPU per slot)
 6. Peak / lowest CPU usage
 7. Average utilization
 8. List active tasks
 9. Statistics (accepted / rejected / released)
 0. Exit
"""


def read_int(prompt):
    return int(input(prompt).strip())


def read_interval():
    start = read_int("Start slot: ")
    end = read_int("End slot (exclusive): ")
    return start, end


def choose_policy():
    print("Admission policy: 1) Strict  2) Reserve (10% kept free)")
    return ReservePolicy(0.1) if input("> ").strip() == "2" else StrictPolicy()


def show_usage(mgr):
    free = mgr.usage_report()
    print("\nSlot | Free | Used | Usage bar")
    for i, f in enumerate(free):
        used = mgr.total_cpu - f
        print(f"{i:>4} | {f:>4} | {used:>4} | {'#' * used}")


def main():
    total = read_int("Total CPU capacity: ")
    slots = read_int("Number of time slots: ")
    mgr = CloudResourceManager(total, slots, choose_policy())
    stats = StatsCollector()
    mgr.add_observer(ConsoleLogger())
    mgr.add_observer(stats)

    while True:
        print(MENU)
        choice = input("> ").strip()
        try:
            if choice == "1":
                tid = input("Task id: ").strip()
                start, end = read_interval()
                cpu = read_int("CPU needed: ")
                res = mgr.allocate(Task(tid, start, end, cpu))
                print("Result:", res.message)
            elif choice == "2":
                tid = input("Task id: ").strip()
                print("Released." if mgr.release(tid) else "Task not found.")
            elif choice == "3":
                start, end = read_interval()
                print("Minimum free CPU:", mgr.check_availability(start, end))
            elif choice == "4":
                start, end = read_interval()
                cpu = read_int("CPU needed: ")
                if mgr.can_fit(start, end, cpu):
                    print("Yes, this request would be accepted.")
                else:
                    slot = mgr.first_conflict_slot(start, end, cpu)
                    print("No." + (f" First conflicting slot: {slot}" if slot != -1
                                   else " It violates the reserve policy."))
            elif choice == "5":
                show_usage(mgr)
            elif choice == "6":
                print("Peak CPU in use:", mgr.peak_usage())
                print("Lowest CPU in use:", mgr.lowest_usage())
            elif choice == "7":
                print(f"Average utilization: {mgr.average_utilization():.1%}")
            elif choice == "8":
                tasks = mgr.active_tasks()
                if not tasks:
                    print("No active tasks.")
                for t in tasks:
                    print(f"{t.task_id}: {t.cpu} CPU, slots [{t.start}, {t.end})")
            elif choice == "9":
                print(vars(stats))
            elif choice == "0":
                print("Goodbye.")
                break
            else:
                print("Invalid option.")
        except ValueError as err:
            print("Error:", err)
        except IndexError as err:
            print("Error:", err)


if __name__ == "__main__":
    main()