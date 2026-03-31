# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- My initial UML design separated data models from scheduling behavior so each class had a focused responsibility.
- `OwnerProfile` stores owner constraints (name, available daily minutes, and preferred time windows) and provides methods to update availability/preferences.
- `Pet` stores the pet's profile (name, species, age, care notes) and provides profile update/summary behavior.
- `CareTask` represents one care activity (title, category, duration, priority, preferred window, required flag) and is responsible for task-level checks/scoring methods.
- `DailyScheduler` coordinates planning by using the owner profile, pet profile, and task list to generate a plan, explain decisions, and report unscheduled tasks.

**b. Design changes**

- Yes. I made three small UML-level changes to reduce ambiguity without adding new classes.
- I introduced a shared `TimeWindow` type (`morning`, `afternoon`, `evening`, `night`) and used it in both `OwnerProfile` and `CareTask`. This makes the relationship between owner preferences and task windows explicit and consistent.
- I added a `task_id` field to `CareTask` so tasks have a stable identity beyond mutable fields like title/category. This helps with traceability when tasks are edited or reordered.
- I added `last_generated_plan` and `last_unscheduled_tasks` to `DailyScheduler` so plan results are represented as scheduler state. This clarifies how `generate_plan()` relates to `get_unscheduled_tasks()` in the system design.

**c. Core user actions**

- The user can add and manage a pet profile so the app knows who needs care and what that pet's needs are.
- The user can create, edit, and prioritize care tasks (like walks, feeding, medication, and grooming) with time estimates.
- The user can generate and review today's care plan, including a clear explanation of why certain tasks were scheduled first.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- The scheduler considers three constraints: the owner's `available_minutes_per_day` as a hard budget, each task's `priority_score()` (which combines numeric priority, a required-task bonus, and a slight preference for shorter tasks), and the owner's `preferred_time_windows` as a soft tiebreaker for ordering.
- Time budget had to be the hardest constraint because my initial UML already put `available_minutes_per_day` on `OwnerProfile` as the central planning limit. Priority came next because during the second implementation phase I added `is_required` and `frequency` fields, and required recurring tasks like medication clearly need to come before optional ones. Window preferences rank last because they shape convenience, not necessity.

**b. Tradeoffs**

- One tradeoff is that my conflict checker only flags exact matching `scheduled_time` values (for example, both tasks at `07:45`) instead of detecting duration overlaps (for example, one task from `07:30-08:00` and another from `07:45-08:15`).
- This is reasonable for the current scope because it keeps the algorithm lightweight, easy to understand, and stable for beginner-level scheduling logic while still catching the most obvious conflicts a pet owner would notice.
- Another tradeoff is that `generate_plan()` uses a greedy packing approach — it walks tasks in priority order and takes each one if it fits the remaining minutes. A knapsack-style optimizer could fit more total value, but greedy was easy to reason about and matched the way a real person would plan: do the most important thing first, then the next, until time runs out.

---

## 3. AI Collaboration

**a. How you used AI**

- I used VS Code Copilot across separate chat sessions for each project phase. The first session focused on drafting the initial UML and generating class skeletons from it. A second session handled the core implementation — filling in method bodies for `OwnerProfile`, `Pet`, `CareTask`, and the first version of `generate_plan()` and `explain_plan()`. A third session added the second wave of features: `filter_tasks`, `sort_by_time`, `complete_task` with recurrence, and `detect_time_conflicts`. A final session wired everything into the Streamlit UI and debugged the app end-to-end.
- Keeping sessions separate helped me stay organized. Each session had a clear scope, so the AI's suggestions stayed focused instead of drifting across unrelated parts of the codebase. When I started the UI session, I could describe the backend as "already done" and focus purely on integration.
- Copilot's inline completions were most effective when I already had a method signature and docstring written — for example, once `_collect_unique_tasks` had its docstring explaining the three task sources, the deduplication logic came out almost exactly right. Chat mode was more useful for bigger-picture work like reviewing the whole app for bugs or asking how data flows between classes.

**b. Judgment and verification**

- When I moved from my initial UML to the updated UML, Copilot suggested making `DailyScheduler` accept all its fields through `__init__` parameters. I rejected that and switched `DailyScheduler` to a `@dataclass` with `owner_profile` as the only required field and `tasks`/`pet` as optional. My reasoning was that the scheduler should work with just an owner profile (pulling tasks from the owner's pets), and forcing callers to always pass a separate task list and pet felt rigid.
- Later, when I asked the AI to audit the app for bugs, it flagged four issues ranging from a real crash to cosmetic inconsistencies. I only applied the one fix that was actually necessary — `sort_by_time` crashing on invalid time input — and told it to skip the rest. I verified the fix was consistent by checking that `detect_time_conflicts` already handled the same scenario with try/except, so I knew the pattern was right for this codebase.

---

## 4. Testing and Verification

**a. What you tested**

- I wrote six focused tests in `tests/test_pawpal.py` targeting the behaviors I was least confident about after implementation.
- `test_task_completion_marks_task_as_completed` and `test_adding_task_increases_pet_task_count` verify the basic building blocks — if `mark_complete` or `add_task` broke, everything downstream would silently produce wrong results.
- `test_complete_task_creates_next_daily_occurrence` and `test_complete_task_creates_next_weekly_occurrence` check that recurring tasks get the correct next `due_date` (one day or one week later) and a fresh `task_id`. I wrote these because the recurrence logic in `complete_task` touches `replace()`, `_build_next_task_id`, and `_attach_task_to_source` all at once, so it was the most error-prone path.
- `test_complete_task_non_recurring_returns_none` confirms that a one-off task (frequency `"once"`) does not accidentally spawn a next occurrence.
- `test_detect_time_conflicts_returns_warning_message` sets up two pets with tasks at the same `scheduled_time` and checks that the conflict detector produces exactly one warning mentioning that time. This was important because the conflict logic distinguishes same-pet vs. cross-pet warnings, and I wanted to make sure the cross-pet path worked.

**b. Confidence**

- I am fairly confident the scheduler handles normal usage correctly. The priority scoring, greedy packing, recurrence, and conflict detection all have direct test coverage.
- With more time I would test edge cases like: a task whose duration exactly equals the remaining budget, an owner with zero available minutes, duplicate `task_id` collisions when the same recurring task is completed twice on the same day, and what happens when `scheduled_time` contains an invalid string in the full UI flow (which I already patched in `sort_by_time` but did not add a test for).

---

## 5. Reflection

**a. What went well**

- I am most satisfied with how the UML-first approach paid off. Starting with a clear initial diagram, then evolving it into the final version with `task_id`, `TimeWindow`, `pets` on `OwnerProfile`, and `tasks` on `Pet`, meant that by the time I started coding I already knew how the pieces connected. The second implementation phase (sorting, filtering, recurrence, conflicts) slotted in without restructuring anything because the data model was solid from the start.
- Breaking the work into phased commits also helped. The skeleton commit gave me something runnable immediately, and each subsequent commit added a coherent slice of functionality that I could test before moving on.

**b. What you would improve**

- The UI still stores tasks in two places — `st.session_state.tasks` (for display) and the actual `Pet.tasks` objects (for scheduling). If I had another iteration I would remove the session-state copy and build the display table directly from the pet data so they never drift apart.
- I would also add a UI control for `available_minutes_per_day` instead of hardcoding it to 120, and add input validation on the scheduled time field so users cannot type something that would have crashed `sort_by_time` before I patched it.
- On the backend side, I would extend the conflict checker to detect duration overlaps, not just exact time matches.

**c. Key takeaway**

- The most important thing I learned is that AI works best when I stay in the architect role. Across every phase of this project - UML design, skeleton generation, implementation, UI wiring, debugging - the best results came when I gave the AI a clear, scoped task and then reviewed what it produced against my own understanding of the design. When I asked vague questions I got generic answers, but when I asked specific ones like "how does the task know which pet it belongs to?" I got insights that led to real improvements. The AI is a powerful collaborator, but it needs me to set the direction and decide what is worth keeping.
