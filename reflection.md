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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
