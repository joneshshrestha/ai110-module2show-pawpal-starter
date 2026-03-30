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
            frequency="daily",
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)

    return DailyScheduler(owner_profile=owner)


def main() -> None:
    scheduler = build_demo_scheduler()
    plan = scheduler.generate_plan()

    print("Today's Schedule")
    print("-" * 16)
    if not plan:
        print("No tasks were scheduled.")
    else:
        for index, task in enumerate(plan, start=1):
            pet_label = f" for {task.pet_name}" if task.pet_name else ""
            time_label = task.preferred_window if task.preferred_window else "anytime"
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
