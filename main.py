from pawpal_system import CareTask, DailyScheduler, OwnerProfile, Pet


def build_demo_scheduler() -> DailyScheduler:
    owner = OwnerProfile(
        owner_name="Jordan",
        available_minutes_per_day=75,
        preferred_time_windows=["morning", "evening"],
    )

    dog = Pet(name="Mochi", species="dog", age=4, care_notes="Loves longer walks.")
    cat = Pet(name="Nori", species="cat", age=2, care_notes="Needs daily play time.")

    dog.add_task(
        CareTask(
            task_id="t1",
            title="Morning Walk",
            category="exercise",
            duration_minutes=30,
            priority=5,
            preferred_window="morning",
            scheduled_time="18:00",
            is_required=True,
            frequency="daily",
        )
    )
    dog.add_task(
        CareTask(
            task_id="t2",
            title="Dinner Feeding",
            category="feeding",
            duration_minutes=10,
            priority=4,
            preferred_window="evening",
            scheduled_time="07:45",
            is_required=True,
            frequency="daily",
        )
    )
    cat.add_task(
        CareTask(
            task_id="t3",
            title="Afternoon Play",
            category="enrichment",
            duration_minutes=20,
            priority=3,
            preferred_window="afternoon",
            scheduled_time="07:45",
            frequency="daily",
        )
    )
    cat.add_task(
        CareTask(
            task_id="t4",
            title="Medication",
            category="health",
            duration_minutes=15,
            priority=5,
            preferred_window="morning",
            scheduled_time="06:30",
            is_required=True,
            frequency="daily",
            is_completed=True,
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)

    return DailyScheduler(owner_profile=owner)


def main() -> None:
    scheduler = build_demo_scheduler()
    all_tasks = scheduler.filter_tasks()

    print("All Tasks (in insertion order)")
    print("-" * 29)
    for task in all_tasks:
        pet_label = f" for {task.pet_name}" if task.pet_name else ""
        time_label = task.scheduled_time if task.scheduled_time else "no-time"
        status_label = "done" if task.is_completed else "open"
        print(f"- {task.title}{pet_label} at {time_label} [{status_label}]")

    sorted_all_tasks = scheduler.sort_by_time(all_tasks)
    print("\nAll Tasks (sorted by HH:MM)")
    print("-" * 28)
    for task in sorted_all_tasks:
        pet_label = f" for {task.pet_name}" if task.pet_name else ""
        time_label = task.scheduled_time if task.scheduled_time else "no-time"
        print(f"- {time_label} | {task.title}{pet_label}")

    conflict_warnings = scheduler.detect_time_conflicts(all_tasks)
    print("\nConflict Warnings")
    print("-" * 17)
    if not conflict_warnings:
        print("None")
    else:
        for warning in conflict_warnings:
            print(f"- {warning}")

    completed_for_nori = scheduler.filter_tasks(is_completed=True, pet_name="Nori")
    print("\nCompleted Tasks For Nori")
    print("-" * 24)
    if not completed_for_nori:
        print("None")
    else:
        for task in scheduler.sort_by_time(completed_for_nori):
            time_label = task.scheduled_time if task.scheduled_time else "no-time"
            print(f"- {time_label} | {task.title}")

    plan = scheduler.generate_plan()

    print("\nToday's Schedule")
    print("-" * 16)
    if not plan:
        print("No tasks were scheduled.")
    else:
        for index, task in enumerate(plan, start=1):
            pet_label = f" for {task.pet_name}" if task.pet_name else ""
            time_label = task.scheduled_time if task.scheduled_time else "no-time"
            print(
                f"{index}. {task.title}{pet_label}"
                f" [{time_label}] - {task.duration_minutes} min"
            )

    unscheduled = scheduler.get_unscheduled_tasks()
    if unscheduled:
        print("\nUnscheduled Tasks")
        print("-" * 17)
        for task in unscheduled:
            print(f"- {task.title} ({task.duration_minutes} min)")


if __name__ == "__main__":
    main()
