import streamlit as st
from pawpal_system import CareTask, DailyScheduler, OwnerProfile, Pet

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])


def task_to_row(task: CareTask) -> dict:
    return {
        "task_id": task.task_id,
        "pet": task.pet_name or "-",
        "title": task.title,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "scheduled_time": task.scheduled_time or "-",
    }


if "owner_profile" not in st.session_state or not isinstance(
    st.session_state["owner_profile"], OwnerProfile
):
    st.session_state["owner_profile"] = OwnerProfile(
        owner_name=owner_name,
        available_minutes_per_day=120,
    )

owner_profile: OwnerProfile = st.session_state["owner_profile"]
owner_profile.owner_name = owner_name

if st.button("Add pet"):
    existing_pet = next(
        (pet for pet in owner_profile.pets if pet.name == pet_name.strip()),
        None,
    )
    try:
        if existing_pet:
            existing_pet.update_profile(
                name=pet_name.strip(),
                species=species,
                age=existing_pet.age,
                care_notes=existing_pet.care_notes,
            )
        else:
            owner_profile.add_pet(
                Pet(name=pet_name.strip(), species=species, age=0, care_notes="")
            )
    except ValueError as exc:
        st.warning(str(exc))
    else:
        st.success(f"Saved pet: {pet_name.strip()}")

if owner_profile.pets:
    st.caption("Current pets")
    st.table(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "tasks": len(pet.tasks),
            }
            for pet in owner_profile.pets
        ]
    )

st.markdown("### Tasks")
st.caption(
    "Add a few tasks. In your final version, these should feed into your scheduler."
)

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    scheduled_time = st.text_input("Scheduled time", value="08:00")

priority_map = {"low": 1, "medium": 2, "high": 3}

if st.button("Add task"):
    # Use the current pet fields as the target pet for this task.
    selected_pet = next(
        (pet for pet in owner_profile.pets if pet.name == pet_name.strip()),
        None,
    )
    if selected_pet is None:
        selected_pet = Pet(name=pet_name.strip(), species=species, age=0, care_notes="")
        owner_profile.add_pet(selected_pet)

    task = CareTask(
        task_id=f"{selected_pet.name}-{len(selected_pet.tasks) + 1}",
        title=task_title.strip(),
        category="general",
        duration_minutes=int(duration),
        priority=priority_map[priority],
        scheduled_time=scheduled_time.strip() or None,
    )
    selected_pet.add_task(task)
    st.session_state.tasks.append(
        {
            "pet": selected_pet.name,
            "title": task.title,
            "duration_minutes": task.duration_minutes,
            "priority": priority,
            "scheduled_time": task.scheduled_time or "-",
        }
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduler = DailyScheduler(owner_profile=owner_profile)
    open_tasks = scheduler.filter_tasks(is_completed=False)
    plan = scheduler.generate_plan()
    if not plan:
        st.warning("No tasks could be scheduled. Add tasks first.")
    else:
        st.caption("Open tasks (filtered)")
        st.table([task_to_row(task) for task in scheduler.sort_by_time(open_tasks)])

        sorted_plan = scheduler.sort_by_time(plan)
        unscheduled = scheduler.get_unscheduled_tasks()
        conflict_warnings = scheduler.detect_time_conflicts(sorted_plan)

        st.success(f"Schedule generated: {len(sorted_plan)} task(s) scheduled.")
        st.table([task_to_row(task) for task in sorted_plan])

        if unscheduled:
            st.warning(f"{len(unscheduled)} task(s) could not fit in available time.")
            st.table([task_to_row(task) for task in unscheduled])
        else:
            st.success("All open tasks fit into today's available time.")

        if conflict_warnings:
            for warning in conflict_warnings:
                st.warning(warning)
        else:
            st.success("No time conflicts detected in the scheduled tasks.")

        with st.expander("Plan explanation"):
            st.text(scheduler.explain_plan())
