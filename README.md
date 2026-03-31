# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

PawPal+ goes beyond a basic task list with four algorithmic features:

### Sorting by time
Tasks can be assigned a preferred start time in `HH:MM` format. `Scheduler.sort_by_time()` uses Python's `sorted()` with a lambda key to order tasks chronologically — tasks without a time are placed at the end.

```python
sorted_tasks = Scheduler.sort_by_time(pet.get_tasks())
```

### Filtering by pet or status
`Scheduler.filter_tasks()` accepts optional `pet_name` and `completed` filters, returning only the `(Pet, Task)` pairs that match. This powers the filter panel in the UI.

```python
pending = scheduler.filter_tasks(pet_name="Mochi", completed=False)
```

### Recurring tasks
`Task` has a `frequency` field (`"once"` / `"daily"` / `"weekly"`) and a `due_date`. Calling `mark_complete()` on a recurring task automatically advances `due_date` by the correct interval and resets `completed` to `False`, so the task is immediately ready for its next occurrence.

### Conflict detection
`Scheduler.check_conflicts()` groups all timed tasks by their `HH:MM` slot and returns a warning string for every slot where two or more tasks collide. The Streamlit UI surfaces these warnings with `st.warning` before the schedule is generated.

```python
warnings = scheduler.check_conflicts()  # e.g. ["Conflict at 08:00 — Mochi: Walk, Luna: Eye drops"]
```

## Testing PawPal+

### Run the test suite

```bash
python -m pytest
```

### What the tests cover

| Class | Tests | Key behaviors verified |
|---|---|---|
| `Task` | 3 | `mark_complete` flips status; `reset` restores it; default priority is medium |
| `Pet` | 3 | `add_task` increases count; `get_tasks` returns a copy; `pending_tasks` excludes completed |
| `Owner` | 2 | `add_pet` increases count; `get_all_tasks` aggregates across all pets |
| `Scheduler` (schedule) | 7 | Budget not exceeded; high priority first; completed tasks excluded; zero budget → empty; empty plan message; multi-pet; preferred category ordering |
| `Scheduler` (sort) | 4 | Chronological order; untimed tasks last; empty list; already-sorted list |
| `Scheduler` (recurrence) | 5 | Daily advances by 1 day and stays pending; weekly advances by 7 days; once stays complete; no due_date defaults to today |
| `Scheduler` (conflicts) | 5 | Different times → no conflict; same time → flagged; untimed tasks → no conflict; cross-pet conflict; per-pet check ignores other pets |
| `Scheduler` (filter) | 3 | Filter by pet name; filter by pending status; no args returns all |

**Total: 32 tests — all passing**

### Confidence level

⭐⭐⭐⭐ (4/5) — High confidence in the happy path and all tested edge cases. The main gap is duration-overlap conflict detection (two tasks whose time windows overlap but don't share the exact same start time).
