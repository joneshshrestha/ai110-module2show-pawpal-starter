from pawpal_system import CareTask, Pet


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
