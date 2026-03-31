# PawPal+ Project Reflection

## 1. System Design

**Three core user actions:**
1. **Add a pet** — enter the pet's name, species, age, and any special needs.
2. **Add care tasks** — create tasks (walk, feeding, medication, grooming, enrichment) with a duration and priority level.
3. **Generate and view today's plan** — produce a prioritized daily schedule that fits within the owner's available time and displays a plain-English explanation of why each task was chosen and when it starts.

**a. Initial design**

The system is built around four classes:

| Class | Responsibility |
|---|---|
| `Task` (dataclass) | Holds a single care item: title, category, duration, priority, and optional notes. Pure data — no logic. |
| `Pet` (dataclass) | Owns a list of `Task` objects; provides `add_task` / `get_tasks`. Tracks species, age, and special needs. |
| `Owner` (dataclass) | Holds the owner's name, daily time budget (`available_minutes`), category preferences, and a list of `Pet` objects. |
| `Scheduler` | Takes an `Owner` and a `Pet`, sorts tasks by priority and owner preferences, greedily fills the time budget, and produces a list of `ScheduledItem` objects plus a human-readable explanation. |

A `ScheduledItem` helper dataclass ties a `Task` to a `start_minute` offset and a short `reason` string, keeping presentation logic out of `Task`.

Relationships:
- `Owner` **1 → many** `Pet` (an owner can have multiple pets)
- `Pet` **1 → many** `Task` (each pet carries its own task list)
- `Scheduler` **uses** `Owner` and `Pet`; **produces** `ScheduledItem` objects

**b. Design changes**

One notable design decision: tasks live on `Pet` (not on `Owner` or `Scheduler`). An early alternative was to have `Owner` own all tasks and tag each with a pet reference, but that would make it harder to swap pets in and out of the scheduler independently. Keeping tasks pet-scoped is cleaner for a multi-pet household.

I also added `ScheduledItem` as a separate dataclass rather than returning raw tuples from `generate_schedule`. Tuples are fragile once you add a third field (the `reason`); a named dataclass keeps the API stable and self-documenting.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, applied in this order:

1. **Task priority** (`high → medium → low`) — a pet's health and safety tasks (medication, feeding) must never be bumped by lower-stakes activities.
2. **Owner preferences** (a list of category names) — within the same priority tier, tasks whose category matches the owner's stated preferences are scheduled first. This lets owners signal "I care most about exercise" without overriding medical tasks.
3. **Daily time budget** (`available_minutes`) — tasks are added greedily until the budget is exhausted; any remaining tasks are silently deferred.

Time budget matters most _within_ a priority tier. A high-priority 5-minute task will always beat a low-priority 60-minute task, but if the budget runs out entirely, even high-priority tasks are skipped (rare in practice; a warning message covers this case).

**b. Tradeoffs**

The greedy "fill in priority order" approach is simple and predictable, but it can fail to find a feasible packing when several medium-priority tasks collectively fit but individually don't leave room for a later high-priority one. A proper bin-packing or backtracking solver would fix this.

That tradeoff is reasonable here because the daily time budgets are loose (the scenario targets ~1–2 hours), and task durations are short (5–30 min). An exact solver would add complexity with negligible real-world benefit for a typical pet owner.

For conflict detection, the scheduler only flags tasks that share the exact same `HH:MM` string — it does not check whether a task's *duration* causes it to overlap with the next one. For example, a 30-minute walk starting at 08:00 and a feeding starting at 08:15 would not be flagged, even though they overlap. A duration-aware check would require tracking end times per task, which is a reasonable next step but was intentionally left out to keep the logic simple and easy to test.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

15 tests across four classes (`TestTask`, `TestPet`, `TestOwner`, `TestScheduler`):

- `mark_complete()` flips `completed` from `False` to `True`
- `reset()` restores `completed` to `False`
- Adding a task to a `Pet` increases its task count by exactly 1
- `get_tasks()` returns a copy (mutating the copy doesn't affect the pet)
- `pending_tasks()` excludes completed tasks
- `get_all_tasks()` aggregates tasks across all pets
- Schedule total duration never exceeds `available_minutes`
- High-priority tasks always appear before low-priority ones
- Completed tasks never appear in the generated schedule
- Zero-budget owner produces an empty schedule
- `explain_plan([])` returns a helpful message rather than crashing
- Multi-pet schedule draws from all pets
- Preferred-category tasks beat non-preferred tasks of equal priority

These tests matter because the scheduler's core promise is "high-priority tasks first, within budget" — any regression there would silently produce a wrong plan with no visible error.

**b. Confidence**

High confidence for the happy path and the tested edge cases. Edge cases to tackle next:
- Two tasks with identical title, priority, and category (sort stability)
- A single task whose duration exactly equals `available_minutes`
- Tasks added after a schedule is generated (stale schedule detection)
- Owner with no pets or pets with no tasks

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
