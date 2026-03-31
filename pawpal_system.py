from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import List, Literal, Optional


TimeWindow = Literal["morning", "afternoon", "evening", "night"]


@dataclass
class OwnerProfile:
    owner_name: str
    available_minutes_per_day: int
    preferred_time_windows: List[TimeWindow] = field(default_factory=list)
    pets: List["Pet"] = field(default_factory=list)

    def update_availability(self, minutes: int) -> None:
        """Update the owner's daily available minutes."""
        if minutes < 0:
            raise ValueError("available_minutes_per_day cannot be negative")
        self.available_minutes_per_day = minutes

    def set_time_preferences(self, windows: List[TimeWindow]) -> None:
        """Set preferred scheduling windows in priority order."""
        valid_windows = {"morning", "afternoon", "evening", "night"}
        if any(window not in valid_windows for window in windows):
            raise ValueError("Invalid time window in preferences")
        # Preserve first-seen order while removing duplicates.
        self.preferred_time_windows = list(dict.fromkeys(windows))

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet to the owner's profile."""
        if any(existing.name == pet.name for existing in self.pets):
            raise ValueError(f"Pet '{pet.name}' already exists for this owner")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name from the owner's profile."""
        self.pets = [pet for pet in self.pets if pet.name != pet_name]

    def get_all_tasks(self) -> List["CareTask"]:
        """Return a combined list of tasks from all owned pets."""
        tasks: List[CareTask] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


@dataclass
class Pet:
    name: str
    species: str
    age: int
    care_notes: str
    tasks: List["CareTask"] = field(default_factory=list)

    def update_profile(
        self, name: str, species: str, age: int, care_notes: str
    ) -> None:
        """Update this pet's profile fields."""
        if age < 0:
            raise ValueError("age cannot be negative")
        self.name = name
        self.species = species
        self.age = age
        self.care_notes = care_notes

    def get_summary(self) -> str:
        """Return a short text summary of the pet."""
        return (
            f"{self.name} ({self.species}, {self.age}y)" f" - {len(self.tasks)} task(s)"
        )

    def add_task(self, task: "CareTask") -> None:
        """Add a task to this pet and set task ownership if missing."""
        if any(existing.task_id == task.task_id for existing in self.tasks):
            raise ValueError(
                f"Task '{task.task_id}' already exists for pet '{self.name}'"
            )
        if not task.pet_name:
            task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by task ID."""
        self.tasks = [task for task in self.tasks if task.task_id != task_id]


@dataclass
class CareTask:
    task_id: str
    title: str
    category: str
    duration_minutes: int
    priority: int
    preferred_window: Optional[TimeWindow] = None
    is_required: bool = False
    frequency: str = "daily"
    due_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    is_completed: bool = False
    pet_name: Optional[str] = None

    def update_task(self, **kwargs) -> None:
        """Update editable task fields with validation."""
        allowed_fields = {
            "title",
            "category",
            "duration_minutes",
            "priority",
            "preferred_window",
            "is_required",
            "frequency",
            "due_date",
            "scheduled_time",
            "is_completed",
            "pet_name",
        }
        invalid_fields = [key for key in kwargs if key not in allowed_fields]
        if invalid_fields:
            raise ValueError(f"Unsupported fields: {', '.join(invalid_fields)}")

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")
        if self.priority < 1:
            raise ValueError("priority must be at least 1")

    def fits_window(self, window: TimeWindow) -> bool:
        """Return whether this task can be scheduled in the given window."""
        return self.preferred_window is None or self.preferred_window == window

    def priority_score(self) -> float:
        """Compute a sortable score for scheduling priority."""
        if self.is_completed:
            return 0.0

        score = float(self.priority)
        if self.is_required:
            score += 5.0
        # Slightly prefer shorter tasks when priorities are close.
        score += 1.0 / max(self.duration_minutes, 1)
        return score

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.is_completed = True

    def recurrence_delta(self) -> Optional[timedelta]:
        """Return a recurrence interval for supported frequencies.

        Supported values:
        - daily -> 1 day
        - weekly -> 1 week
        Any other value returns None (non-recurring).
        """
        normalized_frequency = self.frequency.strip().lower()
        if normalized_frequency == "daily":
            return timedelta(days=1)
        if normalized_frequency == "weekly":
            return timedelta(weeks=1)
        return None


@dataclass
class DailyScheduler:
    owner_profile: OwnerProfile
    tasks: List[CareTask] = field(default_factory=list)
    pet: Optional[Pet] = None
    last_generated_plan: List[CareTask] = field(default_factory=list)
    last_unscheduled_tasks: List[CareTask] = field(default_factory=list)

    def _collect_unique_tasks(self) -> List[CareTask]:
        """Return all scheduler-visible tasks deduplicated by task_id.

        Tasks can come from:
        - scheduler.tasks
        - owner_profile pets
        - optional standalone scheduler.pet
        """
        collected_tasks: List[CareTask] = []
        collected_tasks.extend(self.tasks)
        collected_tasks.extend(self.owner_profile.get_all_tasks())
        if self.pet and self.pet not in self.owner_profile.pets:
            collected_tasks.extend(self.pet.tasks)

        unique_tasks: List[CareTask] = []
        seen_task_ids = set()
        for task in collected_tasks:
            if task.task_id in seen_task_ids:
                continue
            seen_task_ids.add(task.task_id)
            unique_tasks.append(task)
        return unique_tasks

    def _find_task_by_id(self, task_id: str) -> Optional[CareTask]:
        """Find and return a task by task_id, or None when not found."""
        for task in self._collect_unique_tasks():
            if task.task_id == task_id:
                return task
        return None

    def _build_next_task_id(self, current_task_id: str, next_due_date: date) -> str:
        """Create a unique task_id for the next recurring task instance."""
        base_id = f"{current_task_id}-next-{next_due_date.isoformat()}"
        existing_ids = {task.task_id for task in self._collect_unique_tasks()}

        if base_id not in existing_ids:
            return base_id

        suffix = 2
        candidate = f"{base_id}-{suffix}"
        while candidate in existing_ids:
            suffix += 1
            candidate = f"{base_id}-{suffix}"
        return candidate

    def _attach_task_to_source(self, source_task: CareTask, new_task: CareTask) -> None:
        """Attach a generated recurring task to the same source collection.

        Priority of attachment:
        1. scheduler.tasks
        2. matching pet in owner_profile
        3. scheduler.pet
        4. fallback to scheduler.tasks
        """
        if source_task in self.tasks:
            self.tasks.append(new_task)
            return

        if source_task.pet_name:
            pet = next(
                (
                    candidate
                    for candidate in self.owner_profile.pets
                    if candidate.name == source_task.pet_name
                ),
                None,
            )
            if pet is not None:
                pet.add_task(new_task)
                return

        if self.pet and source_task in self.pet.tasks:
            self.pet.add_task(new_task)
            return

        self.tasks.append(new_task)

    def complete_task(
        self,
        task_id: str,
        completed_on: Optional[date] = None,
    ) -> Optional[CareTask]:
        """Mark a task complete and optionally create its next recurring task.

        A new task is created only when frequency is daily or weekly.
        The next due_date is computed as:
        - completed_on + recurrence interval, if completed_on is provided
        - otherwise task.due_date + recurrence interval, if due_date exists
        - otherwise date.today() + recurrence interval

        Returns:
        - CareTask: the newly created next occurrence
        - None: for non-recurring frequencies
        """
        task = self._find_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Task '{task_id}' was not found")

        task.mark_complete()

        recurrence = task.recurrence_delta()
        if recurrence is None:
            return None

        base_date = completed_on or task.due_date or date.today()
        next_due_date = base_date + recurrence
        next_task_id = self._build_next_task_id(task.task_id, next_due_date)

        next_task = replace(
            task,
            task_id=next_task_id,
            due_date=next_due_date,
            is_completed=False,
        )
        self._attach_task_to_source(task, next_task)
        return next_task

    @staticmethod
    def _parse_hhmm(value: str) -> tuple[int, int]:
        """Parse and validate a 24-hour HH:MM time string.

        Raises ValueError when the format is invalid or out of range.
        """
        parts = value.split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("scheduled_time must be in HH:MM format")

        hour, minute = (int(part) for part in parts)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("scheduled_time must be a valid 24-hour HH:MM time")
        return hour, minute

    def filter_tasks(
        self,
        is_completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
        tasks: Optional[List[CareTask]] = None,
    ) -> List[CareTask]:
        """Filter tasks by completion state and/or pet name.

        Args:
        - is_completed: True for completed, False for open, None for no status filter
        - pet_name: case-insensitive pet filter; None for no pet filter
        - tasks: optional input list; defaults to all scheduler-visible tasks
        """
        source_tasks = self._collect_unique_tasks() if tasks is None else list(tasks)
        normalized_pet_name = pet_name.strip().lower() if pet_name else None

        def matches(task: CareTask) -> bool:
            if is_completed is not None and task.is_completed != is_completed:
                return False
            if normalized_pet_name is None:
                return True
            return (
                task.pet_name is not None
                and task.pet_name.lower() == normalized_pet_name
            )

        return [task for task in source_tasks if matches(task)]

    def generate_plan(self) -> List[CareTask]:
        """Build a daily schedule from available and pending tasks."""
        available_minutes = self.owner_profile.available_minutes_per_day
        preferred_windows = self.owner_profile.preferred_time_windows

        deduped_tasks = self._collect_unique_tasks()

        pending_tasks = [task for task in deduped_tasks if not task.is_completed]

        """Define a ranking function for time windows based on owner preferences."""

        def window_rank(task: CareTask) -> int:
            if not preferred_windows:
                return 0
            if task.preferred_window is None:
                return len(preferred_windows)
            if task.preferred_window in preferred_windows:
                return preferred_windows.index(task.preferred_window)
            return len(preferred_windows) + 1

        sorted_tasks = sorted(
            pending_tasks,
            key=lambda task: (
                -task.priority_score(),
                window_rank(task),
                task.duration_minutes,
                task.title.lower(),
            ),
        )

        scheduled: List[CareTask] = []
        unscheduled: List[CareTask] = []
        remaining_minutes = available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= remaining_minutes:
                scheduled.append(task)
                remaining_minutes -= task.duration_minutes
            else:
                unscheduled.append(task)

        self.last_generated_plan = scheduled
        self.last_unscheduled_tasks = unscheduled
        return list(self.last_generated_plan)

    def sort_by_time(self, tasks: Optional[List[CareTask]] = None) -> List[CareTask]:
        """Return tasks sorted by scheduled_time (HH:MM).

        If tasks is omitted, sorts the last generated plan.
        Tasks without scheduled_time are placed at the end.
        """
        tasks_to_sort = self.last_generated_plan if tasks is None else list(tasks)

        return sorted(
            tasks_to_sort,
            key=lambda task: (
                task.scheduled_time is None,
                (
                    (24, 60)
                    if task.scheduled_time is None
                    else self._parse_hhmm(task.scheduled_time)
                ),
                task.title.lower(),
            ),
        )

    def detect_time_conflicts(
        self,
        tasks: Optional[List[CareTask]] = None,
    ) -> List[str]:
        """Return lightweight warning messages for exact same-time conflicts.

        This method does not raise on conflicts. It also returns warnings for
        invalid scheduled_time values instead of stopping execution.
        """
        source_tasks = self._collect_unique_tasks() if tasks is None else list(tasks)
        warnings: List[str] = []
        tasks_by_time: dict[tuple[int, int], List[CareTask]] = {}
        time_labels: dict[tuple[int, int], str] = {}

        for task in source_tasks:
            if task.scheduled_time is None:
                continue
            try:
                parsed_time = self._parse_hhmm(task.scheduled_time)
            except ValueError:
                warnings.append(
                    "Warning: "
                    f"Task '{task.title}' has invalid time '{task.scheduled_time}'."
                )
                continue

            tasks_by_time.setdefault(parsed_time, []).append(task)
            # Keep first-seen HH:MM label for user-facing warnings.
            if parsed_time not in time_labels:
                time_labels[parsed_time] = task.scheduled_time

        for parsed_time, time_group in sorted(
            tasks_by_time.items(),
        ):
            if len(time_group) < 2:
                continue

            scheduled_time = time_labels[parsed_time]
            pet_names = {task.pet_name or "Unknown pet" for task in time_group}
            task_labels = ", ".join(
                f"{task.title} ({task.pet_name or 'Unknown pet'})"
                for task in time_group
            )
            if len(pet_names) == 1:
                pet_name = next(iter(pet_names))
                warnings.append(
                    f"Warning: Conflict at {scheduled_time} for {pet_name}: {task_labels}."
                )
            else:
                warnings.append(
                    f"Warning: Conflict at {scheduled_time} across pets: {task_labels}."
                )

        return warnings

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the current plan."""
        if not self.last_generated_plan and not self.last_unscheduled_tasks:
            return "No plan generated yet. Call generate_plan() first."

        lines: List[str] = []
        if self.last_generated_plan:
            lines.append("Scheduled tasks:")
            for index, task in enumerate(self.last_generated_plan, start=1):
                pet_label = f" for {task.pet_name}" if task.pet_name else ""
                window_label = (
                    task.preferred_window
                    if task.preferred_window is not None
                    else "anytime"
                )
                lines.append(
                    f"{index}. {task.title}{pet_label}"
                    f" ({task.duration_minutes} min, priority {task.priority}, {window_label})"
                )

        if self.last_unscheduled_tasks:
            lines.append("Unscheduled tasks (insufficient time):")
            for task in self.last_unscheduled_tasks:
                pet_label = f" for {task.pet_name}" if task.pet_name else ""
                lines.append(f"- {task.title}{pet_label} ({task.duration_minutes} min)")

        return "\n".join(lines)

    def get_unscheduled_tasks(self) -> List[CareTask]:
        """Return tasks not scheduled in the last generated plan."""
        return list(self.last_unscheduled_tasks)
