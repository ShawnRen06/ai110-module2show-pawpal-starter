"""
main.py — PawPal+ CLI demo

Run with:  python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def hr(char: str = "─", width: int = 55) -> None:
    print(char * width)


def main() -> None:
    # ── Owner ──────────────────────────────────────────────────────────
    jordan = Owner(
        name="Jordan",
        available_minutes=90,
        preferences=["exercise", "feeding"],
    )

    # ── Pets ───────────────────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5, special_needs="daily eye drops")

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Tasks — with explicit times, frequencies, and priorities ───────
    mochi.add_task(Task("Morning walk",    "exercise",   30, "high",   time="08:00", frequency="daily",  due_date=date.today()))
    mochi.add_task(Task("Breakfast",       "feeding",    10, "high",   time="08:30", frequency="daily",  due_date=date.today()))
    mochi.add_task(Task("Enrichment game", "enrichment", 20, "medium", time="10:00", frequency="once"))
    mochi.add_task(Task("Brush coat",      "grooming",   15, "low",    time="17:00", frequency="weekly", due_date=date.today()))

    luna.add_task(Task("Eye drops",  "medical",     5,  "high",   time="08:00", frequency="daily",  due_date=date.today()))
    luna.add_task(Task("Wet food",   "feeding",     5,  "high",   time="08:30", frequency="daily",  due_date=date.today()))
    luna.add_task(Task("Laser play", "enrichment",  10, "medium", time="11:00", frequency="once"))
    luna.add_task(Task("Nail trim",  "grooming",    10, "low",    time="17:00", frequency="weekly", due_date=date.today()))

    scheduler = Scheduler(jordan)

    # ── 1. Full schedule ───────────────────────────────────────────────
    hr("═")
    print("  PawPal+  —  Today's Schedule")
    hr("═")
    schedule = scheduler.generate_schedule()
    print(scheduler.explain_plan(schedule))

    # ── 2. Sort by time ────────────────────────────────────────────────
    hr()
    print("\n[SORT BY TIME — Mochi's tasks in chronological order]")
    sorted_tasks = Scheduler.sort_by_time(mochi.get_tasks())
    for t in sorted_tasks:
        print(f"  {t.time or '??:??'}  [{t.priority:<6}]  {t.title}  ({t.duration_minutes} min)")

    # ── 3. Filter tasks ────────────────────────────────────────────────
    hr()
    print("\n[FILTER — pending tasks for Luna only]")
    pending_luna = scheduler.filter_tasks(pet_name="Luna", completed=False)
    for p, t in pending_luna:
        print(f"  ○  {p.name:<8}  {t.title}")

    # ── 4. Conflict detection ──────────────────────────────────────────
    hr()
    print("\n[CONFLICT DETECTION]")
    conflicts = scheduler.check_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  ⚠  {warning}")
    else:
        print("  No conflicts detected.")

    # Introduce a conflict on purpose and re-check
    print("\n  Adding a conflicting task for Mochi at 08:00...")
    mochi.add_task(Task("Vet call", "medical", 15, "high", time="08:00"))
    conflicts = scheduler.check_conflicts()
    for warning in conflicts:
        print(f"  ⚠  {warning}")

    # ── 5. Recurring task demo ─────────────────────────────────────────
    hr()
    print("\n[RECURRING TASKS — mark_complete advances due_date]")
    walk = mochi.tasks[0]
    print(f"  Before: {walk.title}  due={walk.due_date}  completed={walk.completed}")
    walk.mark_complete()
    print(f"  After:  {walk.title}  due={walk.due_date}  completed={walk.completed}")
    print("  (daily task auto-advances to tomorrow — stays pending)")

    eye = luna.tasks[0]
    print(f"\n  Before: {eye.title}  due={eye.due_date}  completed={eye.completed}")
    eye.mark_complete()
    print(f"  After:  {eye.title}  due={eye.due_date}  completed={eye.completed}")

    # ── 6. All tasks summary ───────────────────────────────────────────
    hr()
    print("\nAll registered tasks:")
    for pet, task in jordan.get_all_tasks():
        status = "✓" if task.completed else "○"
        freq   = f"[{task.frequency}]" if task.frequency != "once" else ""
        print(
            f"  {status}  {pet.name:<8}  [{task.priority:<6}]  "
            f"{task.title:<22}  {task.duration_minutes:>3} min  "
            f"{task.time or '     '}  {freq}"
        )


if __name__ == "__main__":
    main()
