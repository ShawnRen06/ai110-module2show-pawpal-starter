import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Session-state initialisation — pre-load demo data on first run
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    from datetime import date
    _jordan = Owner(name="Jordan", available_minutes=90, preferences=["exercise", "feeding"])
    _mochi  = Pet(name="Mochi", species="dog", age=3)
    _luna   = Pet(name="Luna",  species="cat", age=5, special_needs="daily eye drops")
    _mochi.add_task(Task("Morning walk",    "exercise",   30, "high",   time="08:00", frequency="daily",  due_date=date.today()))
    _mochi.add_task(Task("Breakfast",       "feeding",    10, "high",   time="08:30", frequency="daily",  due_date=date.today()))
    _mochi.add_task(Task("Enrichment game", "enrichment", 20, "medium", time="10:00", frequency="once"))
    _mochi.add_task(Task("Brush coat",      "grooming",   15, "low",    time="17:00", frequency="weekly", due_date=date.today()))
    _luna.add_task(Task("Eye drops",  "medical",    5,  "high",   time="08:00", frequency="daily",  due_date=date.today()))
    _luna.add_task(Task("Wet food",   "feeding",    5,  "high",   time="08:30", frequency="daily",  due_date=date.today()))
    _luna.add_task(Task("Laser play", "enrichment", 10, "medium", time="10:00", frequency="once"))
    _luna.add_task(Task("Nail trim",  "grooming",   10, "low",    time="17:00", frequency="weekly", due_date=date.today()))
    _jordan.add_pet(_mochi)
    _jordan.add_pet(_luna)
    st.session_state.owner = _jordan

# ---------------------------------------------------------------------------
# Sidebar — stats + architecture
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Smart pet care scheduling")
    st.divider()

    if st.session_state.owner:
        owner_s: Owner = st.session_state.owner
        all_pairs = owner_s.get_all_tasks()
        total_tasks = len(all_pairs)
        done_tasks  = sum(1 for _, t in all_pairs if t.completed)
        st.metric("Owner",        owner_s.name)
        st.metric("Pets",         len(owner_s.get_pets()))
        st.metric("Tasks",        total_tasks)
        st.metric("Completed",    f"{done_tasks}/{total_tasks}")
        st.metric("Time budget",  f"{owner_s.available_minutes} min")
        st.divider()

    with st.expander("📐 System Architecture (Mermaid UML)"):
        st.code("""
classDiagram
    class Task {
        +title: str
        +category: str
        +duration_minutes: int
        +priority: str
        +time: str
        +frequency: str
        +due_date: date|None
        +completed: bool
        +mark_complete()
        +reset()
    }
    class Pet {
        +name: str
        +species: str
        +tasks: list[Task]
        +add_task(task)
        +get_tasks()
        +pending_tasks()
    }
    class Owner {
        +name: str
        +available_minutes: int
        +preferences: list[str]
        +pets: list[Pet]
        +add_pet(pet)
        +get_all_tasks()
    }
    class Scheduler {
        +owner: Owner
        +generate_schedule(pet?)
        +sort_by_time(tasks)
        +filter_tasks(pet_name?, completed?)
        +check_conflicts(pet?)
        +explain_plan(schedule)
    }
    Owner "1" --> "many" Pet : owns
    Pet  "1" --> "many" Task : has
    Scheduler --> Owner : uses
        """, language="text")

st.title("🐾 PawPal+")
st.caption("Smart daily care scheduling for your pets")

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.header("1️⃣ Owner Info")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name", value="Jordan")
    with col2:
        available_minutes = st.number_input(
            "Time available today (min)", min_value=5, max_value=480, value=90
        )
    preferences_input = st.text_input(
        "Preferred task categories (comma-separated)",
        value="exercise, feeding",
        help="e.g. exercise, feeding, medical",
    )
    save_owner = st.form_submit_button("💾 Save owner", use_container_width=True)

if save_owner:
    prefs = [p.strip() for p in preferences_input.split(",") if p.strip()]
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            preferences=prefs,
        )
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
        st.session_state.owner.preferences = prefs
    st.success(f"Owner **{owner_name}** saved — {available_minutes} min available today.")

if st.session_state.owner is None:
    st.info("Fill in your name above and click **Save owner** to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2️⃣ Pets")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    special_needs = st.text_input("Special needs (optional)", value="")
    add_pet = st.form_submit_button("➕ Add pet", use_container_width=True)

if add_pet:
    existing_names = [p.name for p in owner.get_pets()]
    if pet_name in existing_names:
        st.warning(f"A pet named **{pet_name}** already exists. Choose a different name.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs))
        st.success(f"Added **{pet_name}** the {species}!")

pets = owner.get_pets()
if pets:
    pet_cols = st.columns(len(pets))
    for col, p in zip(pet_cols, pets):
        icon = "🐶" if p.species == "dog" else "🐱" if p.species == "cat" else "🐾"
        pending = len(p.pending_tasks())
        col.metric(f"{icon} {p.name}", f"{p.species}, age {p.age}",
                   delta=f"{pending} task(s) pending")
else:
    st.info("No pets yet. Add one above.")
    st.stop()

# ---------------------------------------------------------------------------
# Section 3 — Tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3️⃣ Tasks")

pet_names = [p.name for p in pets]
selected_pet_name = st.selectbox("Add task to pet", pet_names)
selected_pet = next(p for p in pets if p.name == selected_pet_name)

with st.form("task_form"):
    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox(
            "Category",
            ["exercise", "feeding", "medical", "grooming", "enrichment", "other"],
        )
        task_time = st.text_input(
            "Preferred time (HH:MM, optional)", value="",
            help="e.g. 08:00 — used for sorting and conflict detection"
        )
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    notes = st.text_input("Notes (optional)", value="")
    add_task = st.form_submit_button("➕ Add task", use_container_width=True)

if add_task:
    selected_pet.add_task(
        Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
            notes=notes,
            time=task_time.strip(),
            frequency=frequency,
        )
    )
    st.success(f"Added **{task_title}** to {selected_pet.name}.")

# All-tasks table
all_pairs = owner.get_all_tasks()
if all_pairs:
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    rows = [
        {
            "Pet": p.name,
            "Task": t.title,
            "Category": t.category,
            "Time": t.time or "—",
            "Duration (min)": t.duration_minutes,
            "Priority": f"{priority_icon.get(t.priority, '')} {t.priority}",
            "Frequency": t.frequency,
            "Status": "✅ Done" if t.completed else "⏳ Pending",
        }
        for p, t in all_pairs
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Conflict detection
    scheduler_check = Scheduler(owner)
    conflicts = scheduler_check.check_conflicts()
    if conflicts:
        st.subheader("⚠️ Time Conflicts Detected")
        for warning in conflicts:
            st.warning(f"**Conflict:** {warning}")
        st.caption("Two or more tasks share the same start time. Update their times to resolve.")
    else:
        st.success("✅ No time conflicts detected among timed tasks.")
else:
    st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section 4 — Generate Schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4️⃣ Generate Schedule")

schedule_scope = st.radio(
    "Schedule for", ["All pets", *pet_names], horizontal=True
)

if st.button("🗓️ Generate schedule", type="primary", use_container_width=True):
    scheduler = Scheduler(owner)

    if schedule_scope == "All pets":
        schedule = scheduler.generate_schedule()
    else:
        target = next(p for p in pets if p.name == schedule_scope)
        schedule = scheduler.generate_schedule(pet=target)

    # Surface any conflicts as warnings before showing the plan
    conflicts = scheduler.check_conflicts(
        pet=None if schedule_scope == "All pets"
            else next(p for p in pets if p.name == schedule_scope)
    )
    for warning in conflicts:
        st.warning(f"⚠️ {warning}")

    if not schedule:
        st.warning(
            "No tasks could be scheduled. Either all tasks are complete, "
            "or the total duration exceeds your available time."
        )
    else:
        total = sum(item.task.duration_minutes for item in schedule)
        remaining = owner.available_minutes - total
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Tasks scheduled", len(schedule))
        col_b.metric("Time used",       f"{total} min")
        col_c.metric("Buffer left",     f"{remaining} min")

        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        rows = [
            {
                "Start time": f"{(8*60 + item.start_minute) // 60:02d}:{(8*60 + item.start_minute) % 60:02d}",
                "Pet": item.pet.name,
                "Task": item.task.title,
                "Priority": f"{priority_icon.get(item.task.priority, '')} {item.task.priority}",
                "Freq": item.task.frequency,
                "Duration (min)": item.task.duration_minutes,
                "Why scheduled": item.reason,
            }
            for item in schedule
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.success(f"Schedule generated — {total} min of care planned for today.")

# ---------------------------------------------------------------------------
# Section 5 — Filter & Sort
# ---------------------------------------------------------------------------
st.divider()
st.header("5️⃣ Filter & Sort Tasks")

col_pet, col_status = st.columns(2)
with col_pet:
    filter_pet = st.selectbox("Filter by pet", ["All pets", *pet_names], key="filter_pet")
with col_status:
    filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"], key="filter_status")

if st.button("🔍 Apply filter", use_container_width=True):
    scheduler_f = Scheduler(owner)
    pet_filter = None if filter_pet == "All pets" else filter_pet
    completed_filter: bool | None = None
    if filter_status == "Pending":
        completed_filter = False
    elif filter_status == "Completed":
        completed_filter = True

    filtered = scheduler_f.filter_tasks(pet_name=pet_filter, completed=completed_filter)

    if not filtered:
        st.info("No tasks match the selected filters.")
    else:
        sorted_tasks = Scheduler.sort_by_time([t for _, t in filtered])
        pet_lookup = {id(t): p for p, t in filtered}
        st.success(f"**{len(filtered)} task(s) found — sorted chronologically by preferred time.**")
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        rows = [
            {
                "Time": t.time or "—",
                "Pet": pet_lookup[id(t)].name,
                "Task": t.title,
                "Category": t.category,
                "Priority": f"{priority_icon.get(t.priority, '')} {t.priority}",
                "Duration (min)": t.duration_minutes,
                "Frequency": t.frequency,
                "Status": "✅ Done" if t.completed else "⏳ Pending",
            }
            for t in sorted_tasks
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
