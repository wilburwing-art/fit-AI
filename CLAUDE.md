# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fit Agent is an AI-powered fitness tracking web application for 2-3 users. It leverages frontier generative AI models (Claude 4.x, GPT-5, Gemini 2.x) to provide personalized workout planning, nutrition guidance, and adaptive long-term coaching.

**Current Status**: Early development - project structure initialized, comprehensive plan in place (`fit_agent_plan.md`).

## Technology Stack

- **Backend**: FastAPI (async Python)
- **Database**: PostgreSQL (planned) with SQLModel ORM
- **AI**: Multi-model strategy via PydanticAI
  - Claude Opus 4.1 for deep planning/reasoning
  - Claude Sonnet 4.5 for conversational coaching and analysis
  - Claude Haiku 4.5 for high-volume validation
  - GPT-5-mini for structured data extraction
  - Gemini 2.5 Pro for long-context analysis (1M tokens)
- **Frontend**: HTMX + Alpine.js + Tailwind CSS
- **Deployment**: Fly.io (target platform)
- **Caching**: Redis (planned for Phase 2)
- **Observability**: Pydantic Logfire

## Development Commands

### Project Setup
```bash
# Install dependencies and sync environment
uv sync

# Run the application (when FastAPI is implemented)
uv run uvicorn src.main:app --reload

# Run tests (when implemented)
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

### Linting & Formatting
```bash
# Fix linting errors
uvx ruff check --fix .

# Format code
uvx ruff format .

# Run both (recommended before commits)
uvx ruff check --fix . && uvx ruff format .
```

**Note**: VSCode is configured to auto-format on save using Ruff (see `.vscode/settings.json`). Ensure the Ruff extension is installed.

### Database Management (when implemented)
```bash
# Run database migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Rollback migration
uv run alembic downgrade -1
```

### Local Development Environment
```bash
# Start PostgreSQL (Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16

# Start Redis (Docker, for Phase 2+)
docker run -d -p 6379:6379 redis:7-alpine
```

## Architecture Guidelines

### AI Agent Strategy

The application uses a **multi-model approach** to optimize cost and performance:

1. **Planning Agent** (Claude Opus 4.1)
   - Generates 4-12 week workout programs
   - Deep reasoning for complex program design
   - Triggered: onboarding, weekly review, user-requested changes
   - Cost-optimized: runs infrequently

2. **Analysis Agent** (Claude Sonnet 4.5)
   - Identifies trends and patterns in user data
   - Progress summaries and risk flags
   - Triggered: weekly automated, dashboard views

3. **Conversational Agent** (Claude Sonnet 4.5)
   - Answers coaching questions
   - Context-aware with full user history
   - User-initiated chat interactions

4. **Data Extraction Agent** (GPT-5-mini)
   - Parses natural language into structured data
   - Fast, cost-effective extraction
   - Use `reasoning_effort='minimal'` for speed

5. **Long-Context Analysis** (Gemini 2.5 Pro)
   - 1M token context enables complete history analysis
   - Can include 2+ years of workouts, nutrition, research papers
   - Eliminates need for complex RAG in many cases

### PydanticAI Usage Pattern

```python
from pydantic_ai import Agent
from pydantic import BaseModel

# Define structured output
class WorkoutPlan(BaseModel):
    weeks: int
    phases: list[dict]
    rationale: str

# Create agent with specific model
planning_agent = Agent(
    'anthropic:claude-opus-4-1-20250805',
    result_type=WorkoutPlan,
    system_prompt="""You are an expert strength coach..."""
)

# Use with context
result = await planning_agent.run(
    user_id=user_id,
    deps={'user_data': user_context}
)
```

### Cost Optimization Strategies

1. **Tiered model usage** - use cheapest appropriate model for each task
2. **Caching layer** (Redis) - cache AI-generated plans (TTL: 7 days)
3. **Batching** - weekly analysis runs once, not per-view
4. **Prompt optimization** - minimize tokens, use structured outputs
5. **Monitor with Logfire** - track costs per user/endpoint

Target: $10-20/month for 2-3 users

### Database Schema Principles

- Use SQLModel for type-safe ORM (combines SQLAlchemy + Pydantic)
- JSONB columns for flexible data (workout plans, exercise sets)
- Proper indexing on query-heavy columns (user_id, dates)
- Versioned plans (track plan changes over time)
- Separate tables for time-series data (workouts, meals, weight)

Key tables:
- `users` + `user_profiles` - auth and traits
- `workout_plans` - AI-generated programs (versioned)
- `workout_sessions` + `exercise_logs` - actual performance data
- `meal_logs` + `nutrition_targets` - nutrition tracking
- `weight_logs` - body metrics over time
- `analysis_cache` - cached AI analysis results

### Frontend Architecture

- **Server-rendered** with HTMX for dynamic updates
- **Alpine.js** for lightweight client-side interactions
- **Tailwind CSS** for styling
- **Mobile-first** design
- Avoid heavy JavaScript frameworks - keep it simple

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2) - MVP
- FastAPI setup with authentication (FastAPI-Users)
- PostgreSQL schema + SQLModel models
- Basic UI for logging (weight, meals, workouts)
- Simple AI integration (workout plan generation)
- Deploy to Fly.io

### Phase 2: AI Agents (Week 3-4)
- PydanticAI agent orchestration
- Background scheduling (APScheduler)
- Redis caching
- Natural language logging
- Logfire observability

### Phase 3: UX Polish (Week 5-6)
- Data visualizations (Chart.js)
- Mobile optimization
- Enhanced features (exercise library, timers)
- Testing and refinement

### Phase 4: Advanced AI (Week 7+) - Optional
- RAG with exercise science papers
- Multi-modal (photo/video analysis)
- Advanced analytics (predictive modeling)
- External integrations

## Development Patterns

### Adding New AI Agents

1. Define Pydantic model for structured output
2. Create agent with appropriate model selection
3. Write system prompt with clear instructions
4. Add context injection (user data, history)
5. Implement caching strategy
6. Add Logfire instrumentation for cost tracking
7. Test with mock responses (don't burn credits)

### Adding API Endpoints

1. Define route in appropriate module
2. Add Pydantic models for request/response validation
3. Implement business logic in service layer
4. Add authentication/authorization checks
5. Write unit tests with TestClient
6. Document in docstring

### Database Migrations

1. Modify SQLModel models
2. Generate migration: `uv run alembic revision --autogenerate -m "description"`
3. Review generated migration (check for data loss)
4. Test migration: `uv run alembic upgrade head`
5. Test rollback: `uv run alembic downgrade -1`

## Environment Configuration

Required environment variables:
```bash
DATABASE_URL=postgresql://user:pass@localhost/fitgent
REDIS_URL=redis://localhost:6379  # Phase 2+
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...  # For Gemini models

# Observability
LOGFIRE_TOKEN=...
```

## Key Design Decisions

1. **PostgreSQL from day 1** - avoid migration pain later
2. **Multi-model AI strategy** - optimize cost vs capability
3. **Server-rendered UI** - simpler than SPA, better for small team
4. **Fly.io hosting** - free tier for MVP, easy scaling
5. **PydanticAI** - type-safe agent orchestration
6. **HTMX over React** - less complexity, faster development

## Security Considerations

- Health data is sensitive - encrypt at rest and in transit
- Never commit API keys (use `.env`, Fly.io secrets)
- Password requirements: min 12 chars
- Session timeout: 7 days
- Data export and deletion (GDPR compliance)
- Rate limiting on AI endpoints to prevent cost spirals

## Cost Monitoring

Critical to track AI costs given multi-model usage:

```python
import logfire

@logfire.span("ai_plan_generation")
async def generate_plan(user_id: int):
    result = await planning_agent.run(user_id)
    logfire.info(
        "plan_generated",
        user_id=user_id,
        tokens=result.usage.total_tokens,
        cost_usd=estimate_cost(result.usage, model)
    )
    return result
```

Set alerts:
- Email if AI cost > $50/day
- Weekly usage reports
- Per-user cost tracking

## Testing Strategy

- **Unit tests**: Business logic, model validation
- **Integration tests**: API endpoints, database operations
- **AI tests**: Mock responses (don't burn credits in CI)
- **Manual validation**: AI output quality
- **E2E tests** (optional): Playwright for critical flows

## Reference Documents

- `fit_agent_plan.md` - Comprehensive project plan with:
  - Detailed architecture
  - AI model selection rationale
  - Database schema
  - Cost estimates
  - Risk mitigation
  - Full roadmap
  - **Current status tracking** (living document)

Read this plan when you need context on design decisions, model capabilities, or implementation details.

## Living Documentation Rule

**After any significant codebase change, update `fit_agent_plan.md` to reflect current status.**

**What qualifies as "significant":**
- Completing or starting a Phase 1/2/3/4 task
- Fixing a blocker or critical issue
- Adding/removing major features or components
- Changing architecture decisions
- Completing milestones (e.g., first deployment, tests passing)
- Discovering new technical debt or issues

**How to update:**
1. **Update Phase progress** in "CURRENT STATUS UPDATE" section
   - Move items between ✅/⚠️/❌ status
   - Update completion percentage
   - Add/remove items from task lists

2. **Update task checklists** in Phase 1/2/3/4 sections
   - Mark completed items with ✅
   - Mark partial items with ⚠️ and add notes
   - Mark blockers with ❌ **BLOCKER**

3. **Update Technical Debt section**
   - Remove fixed issues
   - Add newly discovered issues with priority level
   - Update impact assessments

4. **Update Success Metrics**
   - Mark criteria as passing/failing/N/A
   - Add notes explaining current state

5. **Update Immediate Next Steps**
   - Remove completed items
   - Re-prioritize remaining work
   - Adjust time estimates based on actual progress

**When NOT to update:**
- Minor bug fixes or typos
- Refactoring that doesn't change functionality
- Documentation-only changes
- Dependency updates

**Example workflow:**
```bash
# After fixing HTMX auth bug:
# 1. Edit fit_agent_plan.md
#    - Move "Fix HTMX JWT bug" from ❌ to ✅
#    - Update Phase 1 progress: 70% → 75%
#    - Remove from "Critical Issues" section
#    - Update "Can log weight, meals, workouts" from ❌ to ✅
# 2. Commit with message: "Fix HTMX auth bug, update plan to 75% Phase 1"
```

This ensures the plan remains an accurate snapshot of project state, useful for onboarding, context switching, and progress tracking.
- always update the readme after significant changes to the codebase, similar to how we update the implementation plan