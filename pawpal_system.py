"""
PawPal+ — Logic Layer
All backend classes for the pet care planning system.

UML (Mermaid — paste into https://mermaid.live to render):

classDiagram
    class Task {
        +str title
        +str category
        +int duration_minutes
        +str priority
        +str notes
        +str time
        +str frequency
        +date|None due_date
        +bool completed
        +mark_complete() None
        +reset() None
    }

    class Pet {
        +str name
        +str species
        +int age
        +str special_needs
        +list[Task] tasks
        +add_task(task: Task) None
        +get_tasks() list[Task]
        +pending_tasks() list[Task]
    }

    class Owner {
        +str name
        +int available_minutes
        +list[str] preferences
        +list[Pet] pets
        +add_pet(pet: Pet) None
        +get_pets() list[Pet]
        +get_all_tasks() list[tuple[Pet, Task]]
    }

    class ScheduledItem {
        +Pet pet
        +Task task
        +int start_minute
        +str reason
    }

    class Scheduler {
        +Owner owner
        +generate_schedule(pet: Pet | None) list[ScheduledItem]
        +sort_by_time(tasks: list[Task]) list[Task]
        +filter_tasks(pet_name, completed) list[tuple[Pet, Task]]
        +check_conflicts(pet: Pet | None) list[str]
        +explain_plan(schedule: list[ScheduledItem]) str
    }

    Owner "1" --> "many" Pet : owns
    Pet "1" --> "many" Task : has
    Scheduler --> Owner : uses
    Scheduler ..> ScheduledItem : produces
    ScheduledItem --> Pet : for
    ScheduledItem --> Task : wraps
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta


# Priority rank used for sorting (lower number = higher priority)
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

# Day start offset in minutes from midnight (08:00 = 480)
DAY_START_MINUTE: int = 8 * 60


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity with duration, priority, recurrence, and completion state."""

    title: str
    category: str               # "exercise" | "feeding" | "medical" | "grooming" | "enrichment"
    duration_minutes: int
    priority: str = "medium"    # "low" | "medium" | "high"
    notes: str = ""
    time: str = ""              # preferred wall-clock start in "HH:MM" format (empty = flexible)
    frequency: str = "once"     # "once" | "daily" | "weekly"
    due_date: date | None = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark task done; recurring tasks auto-advance their due_date instead of staying complete."""
        if self.frequency == "daily":
            self.due_date = (self.due_date or date.today()) + timedelta(days=1)
            self.completed = False          # immediately ready for tomorrow
        elif self.frequency == "weekly":
            self.due_date = (self.due_date or date.today()) + timedelta(weeks=1)
            self.completed = False
        else:
            self.completed = True           # "once" tasks stay complete

    def reset(self) -> None:
        """Reset completion status (e.g., for a new day or undo)."""
        self.completed = False


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet with its own list of care tasks."""

    name: str
    species: str            # "dog" | "cat" | "other"
    age: int = 0
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a new care task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks assigned to this pet."""
        return list(self.tasks)

    def pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """The pet owner, holding their daily time budget, preferences, and pets."""

    name: str
    available_minutes: int = 120    # total care time available in a day
    preferences: list[str] = field(default_factory=list)   # preferred task categories
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return a copy of the owner's pet list."""
        return list(self.pets)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all of the owner's pets."""
        pairs: list[tuple[Pet, Task]] = []
        for pet in self.pets:
            for task in pet.get_tasks():
                pairs.append((pet, task))
        return pairs


# ---------------------------------------------------------------------------
# ScheduledItem
# ---------------------------------------------------------------------------

@dataclass
class ScheduledItem:
    """One time-slot in a generated daily schedule."""

    pet: Pet
    task: Task
    start_minute: int   # offset in minutes from DAY_START_MINUTE (0 = 08:00)
    reason: str = ""    # plain-English explanation for this placement


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates an optimised daily care schedule for one or all of the owner's pets.

    Scheduling algorithm
    --------------------
    1. Collect pending (incomplete) tasks from the target pet(s).
    2. Sort by: priority rank → owner preference → title (for stability).
    3. Greedily fill the owner's time budget back-to-back from 08:00.
    4. Tasks that would exceed the budget are skipped (deferred).

    Additional algorithms
    ---------------------
    - sort_by_time(): sort a task list by preferred HH:MM start time.
    - filter_tasks(): filter (pet, task) pairs by pet name or completion status.
    - check_conflicts(): detect tasks whose HH:MM times overlap or collide.
    """

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with the owner whose budget/preferences apply."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by their preferred HH:MM start time.

        Tasks with no time set are placed at the end (treated as '99:99').
        Uses a lambda key so that lexicographic comparison of zero-padded
        strings gives correct chronological order.
        """
        return sorted(tasks, key=lambda t: t.time if t.time else "99:99")

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs filtered by pet name and/or completion status.

        Parameters
        ----------
        pet_name:
            When given, only tasks belonging to that pet are returned.
        completed:
            When True, return only completed tasks.
            When False, return only pending tasks.
            When None (default), return all tasks regardless of status.
        """
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.completed == completed]
        return pairs

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def check_conflicts(self, pet: Pet | None = None) -> list[str]:
        """Detect tasks assigned the same HH:MM start time.

        Returns a list of human-readable warning strings — one per
        conflicting time slot.  Returns an empty list when no conflicts exist.

        Parameters
        ----------
        pet:
            When given, only checks that pet's tasks.
            When None, checks tasks across all of the owner's pets.
        """
        if pet is not None:
            pairs: list[tuple[Pet, Task]] = [(pet, t) for t in pet.get_tasks()]
        else:
            pairs = self.owner.get_all_tasks()

        # Only tasks that have an explicit time can conflict
        timed_pairs = [(p, t) for p, t in pairs if t.time]

        # Group by time slot
        time_map: dict[str, list[tuple[Pet, Task]]] = defaultdict(list)
        for p, t in timed_pairs:
            time_map[t.time].append((p, t))

        warnings: list[str] = []
        for time_str, group in sorted(time_map.items()):
            if len(group) > 1:
                names = ", ".join(f"{p.name}: {t.title}" for p, t in group)
                warnings.append(f"Conflict at {time_str} — {names}")
        return warnings

    # ------------------------------------------------------------------
    # Schedule generation
    # ------------------------------------------------------------------

    def generate_schedule(self, pet: Pet | None = None) -> list[ScheduledItem]:
        """Build a daily schedule for one pet or all pets.

        Tasks are sorted by priority then owner preferences, and greedily
        assigned back-to-back time slots from 08:00 until the budget runs out.
        """
        if pet is not None:
            pairs: list[tuple[Pet, Task]] = [
                (pet, t) for t in pet.pending_tasks()
            ]
        else:
            pairs = [
                (p, t)
                for p in self.owner.pets
                for t in p.pending_tasks()
            ]

        def sort_key(pair: tuple[Pet, Task]) -> tuple[int, int, str]:
            _, t = pair
            priority_rank = PRIORITY_ORDER.get(t.priority, 1)
            preferred = 0 if t.category in self.owner.preferences else 1
            return (priority_rank, preferred, t.title)

        sorted_pairs = sorted(pairs, key=sort_key)

        schedule: list[ScheduledItem] = []
        elapsed = 0

        for p, task in sorted_pairs:
            if elapsed + task.duration_minutes > self.owner.available_minutes:
                continue
            reason = self._build_reason(task)
            schedule.append(
                ScheduledItem(pet=p, task=task, start_minute=elapsed, reason=reason)
            )
            elapsed += task.duration_minutes

        return schedule

    def explain_plan(self, schedule: list[ScheduledItem]) -> str:
        """Return a formatted, human-readable summary of a generated schedule."""
        if not schedule:
            return (
                f"No tasks could be scheduled within "
                f"{self.owner.available_minutes} minutes. "
                "Try shortening task durations or increasing available time."
            )

        lines: list[str] = [f"╔══ Daily Care Plan — {self.owner.name} ══"]

        for item in schedule:
            abs_min = DAY_START_MINUTE + item.start_minute
            hh, mm = divmod(abs_min, 60)
            time_str = f"{hh:02d}:{mm:02d}"
            priority_badge = f"[{item.task.priority.upper():6}]"
            pet_tag = f"({item.pet.name})" if len(self.owner.pets) > 1 else ""
            lines.append(
                f"  {time_str}  {priority_badge}  "
                f"{item.task.title}{' ' + pet_tag if pet_tag else ''}  "
                f"· {item.task.duration_minutes} min  — {item.reason}"
            )

        total = sum(i.task.duration_minutes for i in schedule)
        remaining = self.owner.available_minutes - total
        lines.append("╚" + "═" * 40)
        lines.append(
            f"  Scheduled: {total} min  |  Buffer: {remaining} min  |  "
            f"Tasks: {len(schedule)}"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_reason(self, task: Task) -> str:
        """Compose a short explanation for a task's scheduling priority."""
        parts: list[str] = []
        if task.priority == "high":
            parts.append("high priority")
        if task.category in self.owner.preferences:
            parts.append("matches owner preference")
        if not parts:
            parts.append("fits within available time")
        return ", ".join(parts)
