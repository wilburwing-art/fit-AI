# Conventions

## Code Style

### Python
- Python 3.12+
- Type hints required
- Ruff for linting and formatting
- VSCode auto-formats on save

### Naming
| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `workout_service.py` |
| Classes | PascalCase | `WorkoutService` |
| Functions | snake_case | `generate_workout_plan` |
| Templates | kebab-case | `workout-log.html` |
| Routes | kebab-case | `/workout-sessions` |

### Imports
```python
# Standard library
from datetime import datetime

# Third-party
from fastapi import APIRouter
from pydantic_ai import Agent

# Local
from src.agents.planning import planning_agent
from src.models.workout import WorkoutPlan
```

## SQLModel Patterns

### Single model for ORM + Pydantic
```python
from sqlmodel import SQLModel, Field

class Workout(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    date: date
    notes: str | None = None
```

### Use JSONB for flexible data
```python
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class WorkoutPlan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    plan_data: dict = Field(sa_column=Column(JSONB))  # Flexible structure
```

## PydanticAI Patterns

### Define structured outputs
```python
from pydantic import BaseModel
from pydantic_ai import Agent

class WorkoutPlanOutput(BaseModel):
    weeks: int
    phases: list[dict]
    rationale: str

planning_agent = Agent(
    'anthropic:claude-opus-4-1-20250805',
    result_type=WorkoutPlanOutput,
    system_prompt="You are an expert strength coach..."
)
```

### Always use context injection
```python
result = await planning_agent.run(
    user_prompt,
    deps={'user_profile': profile, 'history': recent_workouts}
)
```

### Cache AI responses
```python
@cached(ttl=7*24*60*60)  # 7 days
async def generate_plan(user_id: int, goals: str) -> WorkoutPlanOutput:
    return await planning_agent.run(goals, deps=get_user_context(user_id))
```

## HTMX Patterns

### Return partials, not full pages
```python
@router.post("/workouts", response_class=HTMLResponse)
async def log_workout(request: Request, data: WorkoutCreate):
    workout = await service.create(data)
    return templates.TemplateResponse(
        "partials/workout-row.html",  # Just the new row
        {"workout": workout}
    )
```

### Use hx-swap for updates
```html
<button hx-post="/workouts"
        hx-target="#workout-list"
        hx-swap="beforeend">
    Add Workout
</button>
```

## Frontend Conventions

### Alpine.js for local state only
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>
```

### Tailwind utility classes
```html
<!-- YES - utility classes -->
<div class="p-4 bg-white rounded-lg shadow-md">

<!-- NO - custom CSS -->
<div class="card">  <!-- Avoid custom classes -->
```

## Error Handling

### Log with Logfire
```python
import logfire

@logfire.span("generate_workout_plan")
async def generate_plan(user_id: int):
    try:
        result = await planning_agent.run(...)
        logfire.info("plan_generated", user_id=user_id, tokens=result.usage.total_tokens)
        return result
    except Exception as e:
        logfire.error("plan_generation_failed", user_id=user_id, error=str(e))
        raise
```

## Cost Tracking

### Track AI costs per call
```python
def estimate_cost(usage, model: str) -> float:
    rates = {
        "claude-opus-4-1": {"input": 0.015, "output": 0.075},
        "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
        "gpt-5-mini": {"input": 0.0001, "output": 0.0004},
    }
    rate = rates.get(model, {"input": 0, "output": 0})
    return (usage.input_tokens * rate["input"] +
            usage.output_tokens * rate["output"]) / 1000
```

## Git

### Commit format
```
type: description

Co-authored notes if pair programming
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## Documentation

### Update fit_agent_plan.md after significant changes
- Phase completion/progress
- Blockers discovered
- Architecture decisions
- Technical debt items

## Anti-Patterns (DO NOT)

- ❌ Use React/Vue (keep it HTMX + Alpine)
- ❌ Run expensive AI models for simple tasks
- ❌ Skip caching for AI responses
- ❌ Burn API credits in tests (use mocks)
- ❌ Store API keys in code
- ❌ Skip cost tracking on AI calls
