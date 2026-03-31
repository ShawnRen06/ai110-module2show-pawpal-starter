"""
tests/test_pawpal.py — Automated tests for PawPal+ core logic.

Run with:  python -m pytest
"""

import pytest
from datetime import date, timedelta
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


# ── Sorting tests ─────────────────────────────────────────────────────────────

class TestSortByTime:
    def test_tasks_returned_in_chronological_order(self):
        """sort_by_time() must return tasks ordered earliest to latest HH:MM."""
        tasks = [
            Task("Dinner",    "feeding",   10, time="18:00"),
            Task("Walk",      "exercise",  30, time="08:00"),
            Task("Lunch med", "medical",    5, time="12:30"),
        ]
        result = Scheduler.sort_by_time(tasks)
        times = [t.time for t in result]
        assert times == ["08:00", "12:30", "18:00"]

    def test_tasks_without_time_go_last(self):
        """Tasks with no time set should appear after all timed tasks."""
        tasks = [
            Task("Flex task", "enrichment", 10, time=""),
            Task("Walk",      "exercise",   30, time="08:00"),
        ]
        result = Scheduler.sort_by_time(tasks)
        assert result[0].time == "08:00"
        assert result[1].time == ""

    def test_empty_list_returns_empty(self):
        """sort_by_time on an empty list should return an empty list."""
        assert Scheduler.sort_by_time([]) == []

    def test_already_sorted_list_unchanged(self):
        """sort_by_time on an already-sorted list should not change order."""
        tasks = [
            Task("A", "exercise", 10, time="07:00"),
            Task("B", "feeding",  10, time="09:00"),
            Task("C", "grooming", 10, time="17:00"),
        ]
        result = Scheduler.sort_by_time(tasks)
        assert [t.title for t in result] == ["A", "B", "C"]


# ── Recurrence tests ──────────────────────────────────────────────────────────

class TestRecurrence:
    def test_daily_task_advances_due_date_by_one_day(self):
        """Completing a daily task should move due_date forward by 1 day."""
        today = date.today()
        task = Task("Walk", "exercise", 30, frequency="daily", due_date=today)
        task.mark_complete()
        assert task.due_date == today + timedelta(days=1)

    def test_daily_task_stays_pending_after_complete(self):
        """A daily task should remain pending (completed=False) after mark_complete."""
        task = Task("Walk", "exercise", 30, frequency="daily", due_date=date.today())
        task.mark_complete()
        assert task.completed is False

    def test_weekly_task_advances_due_date_by_seven_days(self):
        """Completing a weekly task should move due_date forward by 7 days."""
        today = date.today()
        task = Task("Grooming", "grooming", 15, frequency="weekly", due_date=today)
        task.mark_complete()
        assert task.due_date == today + timedelta(weeks=1)

    def test_once_task_stays_complete(self):
        """A 'once' task should remain completed=True after mark_complete."""
        task = Task("Vet visit", "medical", 60, frequency="once")
        task.mark_complete()
        assert task.completed is True

    def test_recurring_task_without_due_date_uses_today(self):
        """A recurring task with no due_date set should default to today when completed."""
        task = Task("Walk", "exercise", 30, frequency="daily")
        assert task.due_date is None
        task.mark_complete()
        assert task.due_date == date.today() + timedelta(days=1)


# ── Conflict detection tests ──────────────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflicts_when_times_differ(self):
        """Tasks at different times should not be flagged."""
        owner = Owner(name="Sam", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task("Walk", "exercise", 30, time="08:00"))
        pet.add_task(Task("Feed", "feeding",  10, time="09:00"))
        owner.add_pet(pet)
        assert Scheduler(owner).check_conflicts() == []

    def test_two_tasks_same_time_flagged(self):
        """Two tasks at the same HH:MM should produce one conflict warning."""
        owner = Owner(name="Sam", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task("Walk", "exercise", 30, time="08:00"))
        pet.add_task(Task("Feed", "feeding",  10, time="08:00"))
        owner.add_pet(pet)
        conflicts = Scheduler(owner).check_conflicts()
        assert len(conflicts) == 1
        assert "08:00" in conflicts[0]

    def test_tasks_without_time_never_conflict(self):
        """Tasks with no time set should never be flagged as conflicts."""
        owner = Owner(name="Sam", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task("Walk", "exercise", 30, time=""))
        pet.add_task(Task("Feed", "feeding",  10, time=""))
        owner.add_pet(pet)
        assert Scheduler(owner).check_conflicts() == []

    def test_cross_pet_conflict_detected(self):
        """Tasks for different pets at the same time should also be flagged."""
        owner = Owner(name="Sam", available_minutes=60)
        p1 = Pet(name="Rex",     species="dog")
        p2 = Pet(name="Whiskers", species="cat")
        p1.add_task(Task("Walk",      "exercise", 30, time="08:00"))
        p2.add_task(Task("Eye drops", "medical",   5, time="08:00"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        conflicts = Scheduler(owner).check_conflicts()
        assert len(conflicts) == 1
        assert "Rex" in conflicts[0] and "Whiskers" in conflicts[0]

    def test_per_pet_conflict_check_ignores_other_pets(self):
        """check_conflicts(pet=...) should only look at that pet's tasks."""
        owner = Owner(name="Sam", available_minutes=60)
        p1 = Pet(name="Rex",     species="dog")
        p2 = Pet(name="Whiskers", species="cat")
        p1.add_task(Task("Walk",      "exercise", 30, time="08:00"))
        p2.add_task(Task("Eye drops", "medical",   5, time="08:00"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        # Each pet has only one task at 08:00 — no conflict within a single pet
        assert Scheduler(owner).check_conflicts(pet=p1) == []
        assert Scheduler(owner).check_conflicts(pet=p2) == []


# ── Filter tests ──────────────────────────────────────────────────────────────

class TestFilterTasks:
    def test_filter_by_pet_name(self):
        """filter_tasks(pet_name=...) should return only that pet's tasks."""
        owner = Owner(name="Sam", available_minutes=60)
        p1 = Pet(name="Rex",     species="dog")
        p2 = Pet(name="Whiskers", species="cat")
        p1.add_task(Task("Walk", "exercise", 30))
        p2.add_task(Task("Feed", "feeding",  10))
        owner.add_pet(p1)
        owner.add_pet(p2)
        result = Scheduler(owner).filter_tasks(pet_name="Rex")
        assert all(p.name == "Rex" for p, _ in result)
        assert len(result) == 1

    def test_filter_by_completed_false(self):
        """filter_tasks(completed=False) should exclude completed tasks."""
        owner = Owner(name="Sam", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        t1 = Task("Walk", "exercise", 30)
        t2 = Task("Feed", "feeding",  10)
        t1.mark_complete()
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        result = Scheduler(owner).filter_tasks(completed=False)
        titles = [t.title for _, t in result]
        assert "Walk" not in titles
        assert "Feed" in titles

    def test_filter_no_args_returns_all(self):
        """filter_tasks() with no arguments should return every task."""
        owner = Owner(name="Sam", available_minutes=60)
        pet = Pet(name="Rex", species="dog")
        pet.add_task(Task("Walk", "exercise", 30))
        pet.add_task(Task("Feed", "feeding",  10))
        owner.add_pet(pet)
        assert len(Scheduler(owner).filter_tasks()) == 2
