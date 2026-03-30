from dataclasses import dataclass, field
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


@dataclass
class DailyScheduler:
    owner_profile: OwnerProfile
    tasks: List[CareTask] = field(default_factory=list)
    pet: Optional[Pet] = None
    last_generated_plan: List[CareTask] = field(default_factory=list)
    last_unscheduled_tasks: List[CareTask] = field(default_factory=list)

    def generate_plan(self) -> List[CareTask]:
        """Build a daily schedule from available and pending tasks."""
        available_minutes = self.owner_profile.available_minutes_per_day
        preferred_windows = self.owner_profile.preferred_time_windows

        collected_tasks: List[CareTask] = []
        collected_tasks.extend(self.tasks)
        collected_tasks.extend(self.owner_profile.get_all_tasks())
        if self.pet and self.pet not in self.owner_profile.pets:
            collected_tasks.extend(self.pet.tasks)

        # Deduplicate by task_id while preserving first occurrence.
        deduped_tasks: List[CareTask] = []
        seen_task_ids = set()
        for task in collected_tasks:
            if task.task_id in seen_task_ids:
                continue
            seen_task_ids.add(task.task_id)
            deduped_tasks.append(task)

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
