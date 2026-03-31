import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state initialisation
# Keep the Owner object alive across every Streamlit re-run.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner: Owner | None = None

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner Info")

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
    save_owner = st.form_submit_button("Save owner")

if save_owner:
    prefs = [p.strip() for p in preferences_input.split(",") if p.strip()]
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            preferences=prefs,
        )
    else:
        # Update existing owner in-place so pets are preserved
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
        st.session_state.owner.preferences = prefs
    st.success(f"Owner **{owner_name}** saved ({available_minutes} min available).")

if st.session_state.owner is None:
    st.info("Fill in your name and save to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Pets")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    special_needs = st.text_input("Special needs (optional)", value="")
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    existing_names = [p.name for p in owner.get_pets()]
    if pet_name in existing_names:
        st.warning(f"A pet named **{pet_name}** already exists.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs))
        st.success(f"Added **{pet_name}** the {species}!")

pets = owner.get_pets()
if pets:
    st.write(f"**{owner.name}'s pets:** " + ", ".join(f"{p.name} ({p.species})" for p in pets))
else:
    st.info("No pets yet. Add one above.")
    st.stop()

# ---------------------------------------------------------------------------
# Section 3 — Add tasks to a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Tasks")

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
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    notes = st.text_input("Notes (optional)", value="")
    add_task = st.form_submit_button("Add task")

if add_task:
    selected_pet.add_task(
        Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
            notes=notes,
        )
    )
    st.success(f"Added **{task_title}** to {selected_pet.name}.")

# Show all tasks across every pet
all_pairs = owner.get_all_tasks()
if all_pairs:
    st.write("**All tasks:**")
    rows = [
        {
            "Pet": p.name,
            "Task": t.title,
            "Category": t.category,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Done": "✓" if t.completed else "○",
        }
        for p, t in all_pairs
    ]
    st.table(rows)
else:
    st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Generate Schedule")

schedule_scope = st.radio(
    "Schedule for", ["All pets", *pet_names], horizontal=True
)

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner)

    if schedule_scope == "All pets":
        schedule = scheduler.generate_schedule()
    else:
        target = next(p for p in pets if p.name == schedule_scope)
        schedule = scheduler.generate_schedule(pet=target)

    if not schedule:
        st.warning(
            "No tasks could be scheduled. Either all tasks are complete, "
            "or the total duration exceeds your available time."
        )
    else:
        st.success(f"Scheduled {len(schedule)} task(s) for today.")

        rows = [
            {
                "Time": f"{(8*60 + item.start_minute) // 60:02d}:{(8*60 + item.start_minute) % 60:02d}",
                "Pet": item.pet.name,
                "Task": item.task.title,
                "Priority": item.task.priority,
                "Duration (min)": item.task.duration_minutes,
                "Reason": item.reason,
            }
            for item in schedule
        ]
        st.table(rows)

        total = sum(item.task.duration_minutes for item in schedule)
        remaining = owner.available_minutes - total
        st.caption(
            f"Total scheduled: **{total} min** | "
            f"Buffer remaining: **{remaining} min** | "
            f"Budget: {owner.available_minutes} min"
        )
