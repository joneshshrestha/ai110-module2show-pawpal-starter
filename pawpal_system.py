from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OwnerProfile:
    owner_name: str
    available_minutes_per_day: int
    preferred_time_windows: List[str] = field(default_factory=list)

    def update_availability(self, minutes: int) -> None:
        pass

    def set_time_preferences(self, windows: List[str]) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    care_notes: str

    def update_profile(
        self, name: str, species: str, age: int, care_notes: str
    ) -> None:
        pass

    def get_summary(self) -> str:
        pass


@dataclass
class CareTask:
    title: str
    category: str
    duration_minutes: int
    priority: int
    preferred_window: Optional[str] = None
    is_required: bool = False

    def update_task(self, **kwargs) -> None:
        pass

    def fits_window(self, window: str) -> bool:
        pass

    def priority_score(self) -> float:
        pass


@dataclass
class DailyScheduler:
    tasks: List[CareTask]
    owner_profile: OwnerProfile
    pet: Pet

    def generate_plan(self) -> List[CareTask]:
        pass

    def explain_plan(self) -> str:
        pass

    def get_unscheduled_tasks(self) -> List[CareTask]:
        pass
