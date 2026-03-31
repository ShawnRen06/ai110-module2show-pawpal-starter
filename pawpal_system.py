"""
PawPal+ — Logic Layer
All backend classes for the pet care planning system.

UML (Mermaid):

classDiagram
    class Owner {
        +str name
        +int available_minutes
        +list[str] preferences
        +list[Pet] pets
        +add_pet(pet: Pet) None
        +get_pets() list[Pet]
    }

    class Pet {
        +str name
        +str species
        +int age
        +str special_needs
        +list[Task] tasks
        +add_task(task: Task) None
        +get_tasks() list[Task]
    }

    class Task {
        +str title
        +str category
        +int duration_minutes
        +str priority
        +str notes
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +generate_schedule() list[ScheduledItem]
        +explain_plan(schedule: list[ScheduledItem]) str
    }

    class ScheduledItem {
        +Task task
        +int start_minute
        +str reason
    }

    Owner "1" --> "many" Pet : owns
    Pet "1" --> "many" Task : has
    Scheduler --> Owner : uses
    Scheduler --> Pet : uses
    Scheduler ..> ScheduledItem : produces
"""

from dataclasses import dataclass, field
from typing import Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care task (walk, feeding, medication, grooming, etc.)."""

    title: str
    category: str                   # e.g. "exercise", "feeding", "medical", "grooming", "enrichment"
    duration_minutes: int
    priority: str = "medium"        # "low" | "medium" | "high"
    notes: str = ""


@dataclass
class Pet:
    """Represents a pet owned by an Owner."""

    name: str
    species: str                    # e.g. "dog", "cat", "other"
    age: int = 0
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """Represents the pet owner with their time budget and preferences."""

    name: str
    available_minutes: int = 120    # total care time available per day
    preferences: list[str] = field(default_factory=list)  # preferred task categories
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self.pets)


@dataclass
class ScheduledItem:
    """One task slot in a generated daily schedule."""

    task: Task
    start_minute: int   # minutes from start of day (0 = 8:00 AM by default)
    reason: str = ""    # human-readable explanation of why this task was included


class Scheduler:
    """
    Generates a daily care schedule for a pet.

    Scheduling rules (in priority order):
    1. High-priority tasks are always scheduled first (if time allows).
    2. Within the same priority, preferred categories (owner.preferences) come next.
    3. Tasks are scheduled back-to-back starting from minute 0 (8:00 AM).
    4. Tasks that don't fit within available_minutes are deferred with a note.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet

    def generate_schedule(self) -> list[ScheduledItem]:
        """
        Sort tasks by priority (and owner preferences), then greedily assign
        time slots until the daily budget is exhausted.

        Returns a list of ScheduledItem in chronological order.
        """
        tasks = self.pet.get_tasks()

        # Sort: primary key = priority rank, secondary key = preferred category first
        def sort_key(t: Task):
            priority_rank = PRIORITY_ORDER.get(t.priority, 1)
            preferred = 0 if t.category in self.owner.preferences else 1
            return (priority_rank, preferred, t.title)

        sorted_tasks = sorted(tasks, key=sort_key)

        schedule: list[ScheduledItem] = []
        elapsed = 0

        for task in sorted_tasks:
            if elapsed + task.duration_minutes > self.owner.available_minutes:
                # Not enough time — skip but note why
                continue

            reason = self._build_reason(task, elapsed)
            schedule.append(ScheduledItem(task=task, start_minute=elapsed, reason=reason))
            elapsed += task.duration_minutes

        return schedule

    def explain_plan(self, schedule: list[ScheduledItem]) -> str:
        """
        Return a human-readable explanation of the generated schedule.
        Lists each task with its start time and the reason it was included/ordered.
        """
        if not schedule:
            return (
                f"No tasks could be scheduled within {self.owner.available_minutes} minutes. "
                "Try reducing task durations or increasing available time."
            )

        lines = [f"Daily care plan for {self.pet.name} ({self.owner.name})\n"]
        for item in schedule:
            start_hour, start_min = divmod(8 * 60 + item.start_minute, 60)
            time_str = f"{start_hour:02d}:{start_min:02d}"
            lines.append(
                f"  {time_str}  [{item.task.priority.upper()}] {item.task.title} "
                f"({item.task.duration_minutes} min) — {item.reason}"
            )

        total = sum(i.task.duration_minutes for i in schedule)
        remaining = self.owner.available_minutes - total
        lines.append(f"\nTotal scheduled: {total} min | Buffer remaining: {remaining} min")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_reason(self, task: Task, elapsed: int) -> str:
        """Compose a short explanation for why a task was placed at this slot."""
        parts = []
        if task.priority == "high":
            parts.append("high priority")
        if task.category in self.owner.preferences:
            parts.append("matches owner preference")
        if not parts:
            parts.append("fits within available time")
        return ", ".join(parts)
