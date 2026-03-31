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

AI was used at every phase, but for different purposes:

- **Phase 1 (Design):** Used AI to generate a first-draft Mermaid UML given a plain-English description of the four classes. The diagram came back immediately with reasonable relationships, which I then refined — for example, moving tasks onto `Pet` rather than `Owner`, and adding `ScheduledItem` as its own class.
- **Phase 2 (Implementation):** Used AI to scaffold method bodies once the class structure was decided. The most useful prompt pattern was "given this method signature and these rules, implement the body" — short, constrained, and verifiable.
- **Phase 4 (Algorithms):** Asked AI to suggest a lightweight conflict-detection strategy. It proposed grouping tasks by time with `defaultdict`, which was exactly the right tool. It also showed how to use a lambda key with `sorted()` for HH:MM string comparison.
- **Phase 5 (Testing):** Used AI to generate test stubs from method signatures. The prompt "write pytest tests for `check_conflicts` covering: no conflict, exact-time match, untimed tasks, cross-pet" produced test skeletons that only needed minor adjustment to match the actual return types.

The most effective prompt pattern throughout: **provide the method signature + the contract it must satisfy**, then ask for an implementation. Vague "write me a scheduler" prompts produced over-engineered code that needed heavy editing.

**b. Judgment and verification**

When generating conflict detection, AI initially suggested comparing tasks using overlapping time *ranges* (start + duration), which would require tasks to have both a start time and an end time. That was more complex than needed — the current design uses a simple exact-match on `HH:MM` strings, which is sufficient for this scenario and much easier to test.

I rejected the range-based version and kept the simpler string-grouping approach. To verify the decision was sound, I wrote five explicit test cases for `check_conflicts` and confirmed they all passed. The tradeoff (exact-match only, no duration overlap) is documented in `reflection.md` section 2b so a future developer knows the limitation is intentional, not an oversight.

---

## 4. Testing and Verification

**a. What you tested**

32 tests across 8 groups (`TestTask`, `TestPet`, `TestOwner`, `TestScheduler`, `TestSortByTime`, `TestRecurrence`, `TestConflictDetection`, `TestFilterTasks`):

- `mark_complete` / `reset` flip `completed` correctly; default priority is `"medium"`
- `add_task` increases count; `get_tasks` returns a defensive copy; `pending_tasks` excludes completed
- `get_all_tasks` aggregates across every pet, not just the first
- Schedule: total duration ≤ budget; high priority first; completed tasks excluded; zero budget → empty; preferred-category ordering; multi-pet support
- Sorting: chronological HH:MM order; untimed tasks last; empty list; already-sorted list
- Recurrence: daily advances `due_date` by 1 day and stays pending; weekly advances by 7 days; `"once"` stays `completed=True`; no `due_date` defaults to today
- Conflict detection: different times → no warning; same time → flagged with that slot; untimed tasks → never flagged; cross-pet and per-pet scoping
- Filtering: by pet name; by completion status; no-args returns all

These tests matter because the scheduler's core promise — right tasks, right order, no conflicts — would silently break without them.

**b. Confidence**

⭐⭐⭐⭐ (4/5) — High confidence in all tested paths. Edge cases to tackle next:
- Duration-overlap conflicts (task A at 08:00 for 30 min, task B at 08:15 — not flagged today)
- Tasks added after a schedule is generated (stale schedule detection)
- Owner with no pets, or pet with no pending tasks
- `sort_by_time` with malformed time strings (e.g. `"8:5"` instead of `"08:05"`)

---

## 5. Reflection

**a. What went well**

The "CLI-first" workflow was the best decision of the project. Building and verifying all logic in `pawpal_system.py` and `main.py` before touching Streamlit meant the UI integration (Phase 3) took under 30 minutes — the backend was already proven. The 32-test suite also gave real confidence: every time a new feature was added in Phase 4, running `pytest` immediately caught any regressions.

The `ScheduledItem` dataclass was also a good early call. It kept the scheduler's output typed and self-documenting, which made it trivial to render as a table in the Streamlit UI without any extra parsing.

**b. What you would improve**

The conflict detection only catches tasks that share the exact same `HH:MM` string. A duration-aware check — flagging any two tasks whose time windows overlap — would be significantly more useful in practice. Implementing it requires tracking `(start, start + duration)` intervals and checking for intersection, which is a well-known interval overlap problem.

I would also add a "mark task complete" button directly in the Streamlit schedule view, so users can check off tasks as they do them throughout the day without having to reload or re-enter anything.

**c. Key takeaway**

The most important lesson: **AI accelerates the translation of a clear spec into code, but it cannot replace the spec itself.** Every time a prompt was vague ("build a scheduler"), the output was over-engineered and hard to adapt. Every time a prompt was precise ("given this method signature and these three rules, implement the body and write two edge-case tests"), the output was immediately usable. The human's job is to hold the design intent clearly enough to write those precise prompts — and to know when to reject output that technically works but adds unnecessary complexity.
