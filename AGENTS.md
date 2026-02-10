# Fit Agent

AI-powered fitness tracking for 2-3 users. Personalized workout planning, nutrition guidance, and adaptive coaching via multi-model AI strategy.

**Status**: Early development - structure initialized, plan in `fit_agent_plan.md`.

## Build & Test

```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest
uv run pytest --cov=src

# Lint & format (run before commits)
uvx ruff check --fix . && uvx ruff format .

# Database migrations
uv run alembic upgrade head                          # Apply
uv run alembic revision --autogenerate -m "message"  # Generate
uv run alembic downgrade -1                          # Rollback

# Local services
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16
docker run -d -p 6379:6379 redis:7-alpine  # Phase 2+
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (async Python) |
| Database | PostgreSQL + SQLModel ORM |
| AI | PydanticAI multi-model orchestration |
| Frontend | HTMX + Alpine.js + Tailwind CSS |
| Deploy | Fly.io |
| Cache | Redis (Phase 2+) |
| Observability | Pydantic Logfire |

## AI Agent Strategy

| Agent | Model | Purpose | Trigger |
|-------|-------|---------|---------|
| Planning | Claude Opus 4.1 | 4-12 week programs | Onboarding, weekly review |
| Analysis | Claude Sonnet 4.5 | Trends, progress, risk flags | Weekly automated |
| Conversational | Claude Sonnet 4.5 | Coaching Q&A | User chat |
| Data Extraction | GPT-5-mini | NL → structured data | Logging |
| Long-Context | Gemini 2.5 Pro | 1M token history analysis | Deep analysis |

Target cost: $10-20/month for 2-3 users.

## Architecture

```
src/
├── api/          # FastAPI routes
├── models/       # SQLModel ORM + Pydantic schemas
├── services/     # Business logic
├── agents/       # PydanticAI agent definitions
└── core/         # Config, database, auth
```

### Key Tables
- `users`, `user_profiles` - Auth and traits
- `workout_plans` - AI-generated programs (versioned)
- `workout_sessions`, `exercise_logs` - Performance data
- `meal_logs`, `nutrition_targets` - Nutrition tracking
- `weight_logs` - Body metrics
- `analysis_cache` - Cached AI results

## Code Patterns

### Adding AI Agents
1. Define Pydantic output model
2. Create agent with model selection
3. Write system prompt
4. Add context injection (user data)
5. Implement caching (Redis, TTL 7 days)
6. Add Logfire instrumentation
7. Test with mocks (don't burn credits)

### Adding Endpoints
1. Define route in appropriate module
2. Add Pydantic request/response models
3. Implement service layer logic
4. Add auth checks
5. Write unit tests

## Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@localhost/fitgent
REDIS_URL=redis://localhost:6379
SECRET_KEY=<openssl rand -hex 32>
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
LOGFIRE_TOKEN=...
```

## Security

- Health data encrypted at rest and in transit
- Never commit API keys
- Password min 12 chars
- Session timeout 7 days
- Rate limiting on AI endpoints
- GDPR: data export and deletion

## Documentation Rules

After significant changes, update:
1. `fit_agent_plan.md` - Phase progress, task checklists, technical debt
2. `README.md` - User-facing documentation

See CLAUDE.md for detailed documentation workflow.

## Reference

- `fit_agent_plan.md` - Comprehensive plan with architecture, costs, roadmap
- `.vscode/settings.json` - Auto-format on save with Ruff
