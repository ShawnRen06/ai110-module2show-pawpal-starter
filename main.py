"""
main.py — PawPal+ CLI demo

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def hr(char: str = "─", width: int = 50) -> str:
    return char * width


def main() -> None:
    # ── Owner ──────────────────────────────────────────────────────────
    jordan = Owner(
        name="Jordan",
        available_minutes=90,
        preferences=["exercise", "feeding"],
    )

    # ── Pets ───────────────────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", age=3, special_needs="")
    luna = Pet(name="Luna", species="cat", age=5, special_needs="daily eye drops")

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Tasks for Mochi (dog) ──────────────────────────────────────────
    mochi.add_task(Task("Morning walk",    "exercise",    duration_minutes=30, priority="high"))
    mochi.add_task(Task("Breakfast",       "feeding",     duration_minutes=10, priority="high"))
    mochi.add_task(Task("Enrichment game", "enrichment",  duration_minutes=20, priority="medium"))
    mochi.add_task(Task("Brush coat",      "grooming",    duration_minutes=15, priority="low"))

    # ── Tasks for Luna (cat) ───────────────────────────────────────────
    luna.add_task(Task("Eye drops",   "medical",     duration_minutes=5,  priority="high",
                       notes="1 drop each eye, morning"))
    luna.add_task(Task("Wet food",    "feeding",     duration_minutes=5,  priority="high"))
    luna.add_task(Task("Laser play",  "enrichment",  duration_minutes=10, priority="medium"))
    luna.add_task(Task("Nail trim",   "grooming",    duration_minutes=10, priority="low"))

    # ── Schedule ───────────────────────────────────────────────────────
    scheduler = Scheduler(jordan)

    print(hr("═"))
    print("  PawPal+  —  Today's Schedule")
    print(hr("═"))

    # Whole-household plan
    full_schedule = scheduler.generate_schedule()
    print(scheduler.explain_plan(full_schedule))

    print()
    print(hr())

    # Per-pet plan
    for pet in jordan.get_pets():
        pet_schedule = scheduler.generate_schedule(pet=pet)
        print(f"\n[{pet.name.upper()} — {pet.species}]")
        print(scheduler.explain_plan(pet_schedule))

    # ── Mark a task complete and re-run ───────────────────────────────
    print()
    print(hr())
    print("\nSimulating: Mochi's morning walk is done...")
    mochi.tasks[0].mark_complete()

    updated_schedule = scheduler.generate_schedule(pet=mochi)
    print(scheduler.explain_plan(updated_schedule))

    # ── All tasks summary ──────────────────────────────────────────────
    print()
    print(hr())
    print("\nAll registered tasks:")
    for pet, task in jordan.get_all_tasks():
        status = "✓" if task.completed else "○"
        print(
            f"  {status}  {pet.name:<8}  [{task.priority:<6}]  "
            f"{task.title:<22}  {task.duration_minutes:>3} min  ({task.category})"
        )


if __name__ == "__main__":
    main()
