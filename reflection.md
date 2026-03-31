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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
