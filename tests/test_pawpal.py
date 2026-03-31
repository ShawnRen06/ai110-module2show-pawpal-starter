"""
tests/test_pawpal.py — Automated tests for PawPal+ core logic.

Run with:  python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_ORDER


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def basic_owner() -> Owner:
    return Owner(name="Jordan", available_minutes=90, preferences=["exercise"])


@pytest.fixture
def dog() -> Pet:
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Morning walk",    "exercise",   duration_minutes=30, priority="high"))
    pet.add_task(Task("Breakfast",       "feeding",    duration_minutes=10, priority="high"))
    pet.add_task(Task("Enrichment game", "enrichment", duration_minutes=20, priority="medium"))
    pet.add_task(Task("Brush coat",      "grooming",   duration_minutes=15, priority="low"))
    return pet


# ── Task tests ────────────────────────────────────────────────────────────────

class TestTask:
    def test_mark_complete_changes_status(self):
        """mark_complete() should flip completed from False to True."""
        task = Task("Walk", "exercise", duration_minutes=20)
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_reset_clears_completion(self):
        """reset() should restore completed to False after mark_complete()."""
        task = Task("Walk", "exercise", duration_minutes=20)
        task.mark_complete()
        task.reset()
        assert task.completed is False

    def test_default_priority_is_medium(self):
        task = Task("Walk", "exercise", duration_minutes=20)
        assert task.priority == "medium"


# ── Pet tests ─────────────────────────────────────────────────────────────────

class TestPet:
    def test_add_task_increases_count(self):
        """Adding a task to a Pet should increase its task count by 1."""
        pet = Pet(name="Buddy", species="dog")
        before = len(pet.get_tasks())
        pet.add_task(Task("Walk", "exercise", duration_minutes=20))
        assert len(pet.get_tasks()) == before + 1

    def test_get_tasks_returns_copy(self):
        """get_tasks() should return a copy; mutating it must not affect the pet."""
        pet = Pet(name="Buddy", species="dog")
        pet.add_task(Task("Walk", "exercise", duration_minutes=20))
        copy = pet.get_tasks()
        copy.clear()
        assert len(pet.get_tasks()) == 1

    def test_pending_tasks_excludes_completed(self):
        """pending_tasks() must not include tasks already marked complete."""
        pet = Pet(name="Buddy", species="dog")
        t1 = Task("Walk", "exercise", duration_minutes=20)
        t2 = Task("Feed", "feeding", duration_minutes=10)
        pet.add_task(t1)
        pet.add_task(t2)
        t1.mark_complete()
        pending = pet.pending_tasks()
        assert t1 not in pending
        assert t2 in pending


# ── Owner tests ───────────────────────────────────────────────────────────────

class TestOwner:
    def test_add_pet_increases_pet_count(self):
        owner = Owner(name="Sam", available_minutes=60)
        owner.add_pet(Pet(name="Rex", species="dog"))
        assert len(owner.get_pets()) == 1

    def test_get_all_tasks_aggregates_across_pets(self):
        """get_all_tasks() should return tasks from every pet."""
        owner = Owner(name="Sam", available_minutes=60)
        p1 = Pet(name="Rex", species="dog")
        p2 = Pet(name="Whiskers", species="cat")
        p1.add_task(Task("Walk", "exercise", duration_minutes=20))
        p2.add_task(Task("Feed", "feeding", duration_minutes=5))
        p2.add_task(Task("Play", "enrichment", duration_minutes=10))
        owner.add_pet(p1)
        owner.add_pet(p2)
        all_tasks = owner.get_all_tasks()
        assert len(all_tasks) == 3
        pets_in_result = {p.name for p, _ in all_tasks}
        assert pets_in_result == {"Rex", "Whiskers"}


# ── Scheduler tests ───────────────────────────────────────────────────────────

class TestScheduler:
    def test_schedule_fits_within_time_budget(self, basic_owner, dog):
        """Total scheduled duration must not exceed available_minutes."""
        basic_owner.add_pet(dog)
        scheduler = Scheduler(basic_owner)
        schedule = scheduler.generate_schedule(pet=dog)
        total = sum(item.task.duration_minutes for item in schedule)
        assert total <= basic_owner.available_minutes

    def test_high_priority_tasks_scheduled_before_low(self, basic_owner, dog):
        """High-priority tasks should always appear before low-priority ones."""
        basic_owner.add_pet(dog)
        scheduler = Scheduler(basic_owner)
        schedule = scheduler.generate_schedule(pet=dog)
        priorities = [PRIORITY_ORDER[item.task.priority] for item in schedule]
        assert priorities == sorted(priorities), "Schedule not sorted by priority"

    def test_completed_tasks_excluded_from_schedule(self, basic_owner, dog):
        """Tasks marked complete must not appear in the generated schedule."""
        basic_owner.add_pet(dog)
        dog.tasks[0].mark_complete()   # mark the first task done
        scheduler = Scheduler(basic_owner)
        schedule = scheduler.generate_schedule(pet=dog)
        titles = [item.task.title for item in schedule]
        assert dog.tasks[0].title not in titles

    def test_zero_available_minutes_produces_empty_schedule(self):
        """If the owner has no time, the schedule should be empty."""
        owner = Owner(name="Busy", available_minutes=0)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task("Walk", "exercise", duration_minutes=20))
        owner.add_pet(pet)
        schedule = Scheduler(owner).generate_schedule(pet=pet)
        assert schedule == []

    def test_explain_plan_empty_schedule_returns_message(self, basic_owner, dog):
        """explain_plan with an empty list should return a helpful message, not crash."""
        basic_owner.add_pet(dog)
        msg = Scheduler(basic_owner).explain_plan([])
        assert "No tasks" in msg

    def test_multi_pet_schedule_includes_all_pets(self, basic_owner):
        """generate_schedule(pet=None) should draw from all of the owner's pets."""
        p1 = Pet(name="Rex", species="dog")
        p2 = Pet(name="Luna", species="cat")
        p1.add_task(Task("Walk", "exercise", duration_minutes=10, priority="high"))
        p2.add_task(Task("Feed", "feeding", duration_minutes=5, priority="high"))
        basic_owner.add_pet(p1)
        basic_owner.add_pet(p2)
        schedule = Scheduler(basic_owner).generate_schedule()
        pet_names = {item.pet.name for item in schedule}
        assert "Rex" in pet_names
        assert "Luna" in pet_names

    def test_preferred_category_scheduled_before_non_preferred_same_priority(self):
        """Within the same priority level, preferred categories should come first."""
        owner = Owner(name="Alex", available_minutes=60, preferences=["exercise"])
        pet = Pet(name="Bud", species="dog")
        pet.add_task(Task("Grooming",  "grooming",  duration_minutes=15, priority="medium"))
        pet.add_task(Task("Walk",      "exercise",  duration_minutes=15, priority="medium"))
        owner.add_pet(pet)
        schedule = Scheduler(owner).generate_schedule(pet=pet)
        assert schedule[0].task.category == "exercise"
