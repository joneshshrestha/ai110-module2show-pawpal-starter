from datetime import date

from pawpal_system import CareTask, DailyScheduler, OwnerProfile, Pet


def test_task_completion_marks_task_as_completed() -> None:
    task = CareTask(
        task_id="t-complete",
        title="Medication",
        category="health",
        duration_minutes=5,
        priority=4,
    )

    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet(name="Mochi", species="dog", age=3, care_notes="Friendly")
    initial_count = len(pet.tasks)

    pet.add_task(
        CareTask(
            task_id="t-add",
            title="Evening Walk",
            category="exercise",
            duration_minutes=20,
            priority=3,
        )
    )

    assert len(pet.tasks) == initial_count + 1


def test_complete_task_creates_next_daily_occurrence() -> None:
    owner = OwnerProfile(owner_name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog", age=3, care_notes="")
    task = CareTask(
        task_id="daily-walk",
        title="Daily Walk",
        category="exercise",
        duration_minutes=20,
        priority=3,
        frequency="daily",
        due_date=date(2026, 3, 30),
    )
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = DailyScheduler(owner_profile=owner)

    next_task = scheduler.complete_task("daily-walk")

    assert task.is_completed is True
    assert next_task is not None
    assert next_task.task_id.startswith("daily-walk-next-")
    assert next_task.due_date == date(2026, 3, 31)
    assert next_task.is_completed is False


def test_complete_task_creates_next_weekly_occurrence() -> None:
    owner = OwnerProfile(owner_name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Nori", species="cat", age=2, care_notes="")
    task = CareTask(
        task_id="weekly-groom",
        title="Weekly Grooming",
        category="grooming",
        duration_minutes=30,
        priority=2,
        frequency="weekly",
        due_date=date(2026, 3, 30),
    )
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = DailyScheduler(owner_profile=owner)

    next_task = scheduler.complete_task("weekly-groom")

    assert task.is_completed is True
    assert next_task is not None
    assert next_task.due_date == date(2026, 4, 6)
    assert next_task.frequency == "weekly"


def test_complete_task_non_recurring_returns_none() -> None:
    owner = OwnerProfile(owner_name="Jordan", available_minutes_per_day=60)
    task = CareTask(
        task_id="one-off",
        title="Vet Visit",
        category="health",
        duration_minutes=45,
        priority=5,
        frequency="once",
    )
    scheduler = DailyScheduler(owner_profile=owner, tasks=[task])

    next_task = scheduler.complete_task("one-off", completed_on=date(2026, 3, 30))

    assert task.is_completed is True
    assert next_task is None


def test_detect_time_conflicts_returns_warning_message() -> None:
    owner = OwnerProfile(owner_name="Jordan", available_minutes_per_day=60)
    dog = Pet(name="Mochi", species="dog", age=3, care_notes="")
    cat = Pet(name="Nori", species="cat", age=2, care_notes="")

    dog.add_task(
        CareTask(
            task_id="dog-1",
            title="Dog Feeding",
            category="feeding",
            duration_minutes=10,
            priority=2,
            scheduled_time="08:00",
        )
    )
    cat.add_task(
        CareTask(
            task_id="cat-1",
            title="Cat Feeding",
            category="feeding",
            duration_minutes=10,
            priority=2,
            scheduled_time="08:00",
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = DailyScheduler(owner_profile=owner)

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Warning:" in warnings[0]
