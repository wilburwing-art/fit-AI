# Fit Agent

AI-powered fitness tracking for a small group (2-3 users). Multi-model AI via PydanticAI agents for workout programming, nutrition planning, natural language logging, and automated progress analysis. Server-rendered with HTMX for zero-JS-framework simplicity.

## Architecture

```
  ┌──────────────────────────────────────────────────────────────┐
  │                        Browser                                │
  │          HTMX 2.0 + Alpine.js + Tailwind CSS                 │
  └────────────────────────┬─────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────┐
  │                    FastAPI (async)                             │
  │                                                               │
  │  Auth ──── Data Logging ──── AI Endpoints ──── Page Routes   │
  │  (JWT)     (weight,          (plan gen,        (Jinja2        │
  │             meals,            NL parse,         templates)    │
  │             workouts)         analysis)                       │
  └──────────┬───────────┬──────────┬───────────────────────────┘
             │           │          │
  ┌──────────▼────────┐  │  ┌──────▼────────────────────────────┐
  │  PostgreSQL 16    │  │  │  PydanticAI Agents (multi-model)  │
  │  + SQLModel ORM   │  │  │                                   │
  │                   │  │  │  Planning ── Claude Opus 4.1      │
  │  users            │  │  │  Nutrition ─ Claude Sonnet 4.5    │
  │  profiles         │  │  │  Analysis ── Claude Sonnet 4.5    │
  │  workout_plans    │  │  │  Extraction  GPT-4o-mini          │
  │  workout_sessions │  │  │  Long-ctx ── Gemini 2.5 Pro      │
  │  meal_logs        │  │  └───────────────────────────────────┘
  │  weight_logs      │  │
  │  analysis_cache   │  ▼
  └───────────────────┘  Redis (optional)
                         ├── AI response cache (7d TTL)
                         ├── Rate limiting storage
                         └── Analysis result cache
```

### AI Agents

| Agent | Model (default) | Purpose | Trigger |
|-------|-----------------|---------|---------|
| **Planning** | Claude Opus 4.1 | Periodized workout programs (4-12 weeks) | User request |
| **Nutrition** | Claude Sonnet 4.5 | Macro targets and meal suggestions | User request |
| **Analysis** | Claude Sonnet 4.5 | Progress trend detection and coaching | Weekly (scheduled) |
| **NL Parser** | GPT-4o-mini | Parse "225x5x3" into structured data | User request |
| **Long-context** | Gemini 2.5 Pro | Longitudinal analysis over months of data | On demand |

All model names are configurable via environment variables.

## Features

- **Workout plan generation** — AI-generated periodized programs adapted to equipment, experience, injuries, and time constraints
- **Nutrition targets** — Macro calculations and meal suggestions based on goals and body composition
- **Natural language logging** — Parse "Squats 225x5x3 @RPE8" or "chicken breast 8oz with rice" into structured data
- **Data logging** — Track weight, meals, and workouts through a server-rendered UI
- **Automated progress analysis** — Weekly scheduled analysis for all active users
- **Redis caching** — 7-day TTL on AI responses, cache invalidation on new data, graceful degradation when Redis is down
- **Observability** — Logfire instrumentation on all AI and cache operations
- **JWT authentication** — Secure registration and login via FastAPI-Users
- **Rate-limited AI** — Per-user limits prevent cost spirals (5 plan requests/day, 30 NL parses/hour)

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 16 (or Docker)
- [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
git clone https://github.com/wilburwing-art/fit-AI.git
cd fit-AI

uv sync

cp .env.example .env
# Add DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY

# Start PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=fitgent postgres:16

# Run migrations
uv run alembic upgrade head

# Start the app
uv run uvicorn src.main:app --reload
```

Open http://localhost:8000

### Deployment

Not yet deployed. Local development only.

## Project Structure

```
src/
├── api/
│   ├── auth.py       # Registration, login, password reset (FastAPI-Users)
│   ├── data.py       # Weight, meal, workout logging + cache invalidation
│   ├── ai.py         # Plan generation + NL parsing endpoints
│   └── pages.py      # Server-rendered HTML routes (Jinja2)
├── models/
│   ├── user.py       # User, UserProfile, Goal (SQLModel)
│   ├── workout.py    # WorkoutPlan, WorkoutSession, ExerciseLog
│   ├── nutrition.py  # WeightLog, MealLog, NutritionTarget
│   └── ai.py         # AnalysisCache, ScheduledJob
├── services/
│   ├── ai.py         # Multi-model PydanticAI agents + cache integration
│   ├── cache.py      # Redis caching with graceful degradation
│   ├── nl_parser.py  # Natural language workout/meal parsing
│   └── scheduler.py  # APScheduler background jobs (weekly analysis)
├── templates/        # HTMX + Alpine.js templates
├── config.py         # Pydantic Settings (env vars, model selection)
├── database.py       # Async PostgreSQL connection
├── auth.py           # JWT strategy, user manager
├── schemas.py        # Request/response validation
├── rate_limit.py     # slowapi rate limiting (Redis or memory)
└── main.py           # FastAPI app + lifespan (logfire, redis, scheduler)
```

## API

### Auth
```
POST /auth/register         # Create account
POST /auth/jwt/login        # Login (returns JWT)
GET  /auth/users/me         # Current user profile
```

### Data Logging
```
POST /api/weight            # Log weight + measurements
POST /api/meals             # Log meal with macros
POST /api/workouts          # Log workout session
GET  /api/recent-activity   # Combined activity feed
```

### AI
```
POST /api/ai/generate-workout-plan     # Periodized program generation
POST /api/ai/generate-nutrition-plan   # Macro targets + meal suggestions
POST /api/ai/parse-workout             # NL workout → structured data
POST /api/ai/parse-meal                # NL meal → structured data
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `SECRET_KEY` | Yes | JWT signing key (`openssl rand -hex 32`) |
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `OPENAI_API_KEY` | No | GPT-4o-mini for NL extraction |
| `GOOGLE_API_KEY` | No | Gemini 2.5 Pro for long-context analysis |
| `REDIS_ENABLED` | No | Set `true` to enable Redis caching |
| `REDIS_URL` | No | Redis connection string (default: `redis://localhost:6379/0`) |
| `LOGFIRE_TOKEN` | No | Pydantic Logfire observability token |
| `PLANNING_MODEL` | No | Override planning agent model |
| `ANALYSIS_MODEL` | No | Override analysis agent model |
| `EXTRACTION_MODEL` | No | Override NL extraction model |

## Tech Stack

Python 3.13+ / FastAPI / PostgreSQL 16 / SQLModel / PydanticAI / Claude Opus + Sonnet + Haiku / GPT-4o-mini / Gemini 2.5 Pro / Redis / APScheduler / Logfire / HTMX + Alpine.js + Tailwind CSS / FastAPI-Users (JWT) / Alembic

## Development

```bash
# Run tests (28 tests: auth, data, AI, cache, NL parser)
uv run pytest -v

# Lint and format
uvx ruff check --fix . && uvx ruff format .
```

## Roadmap

**Phase 1 (~95%)** — Core logging, auth, AI generation, test suite, deployment configs
**Phase 2 (~90%)** — Multi-model AI, Redis caching, APScheduler, NL parsing, Logfire observability
**Phase 3** — Chart.js visualizations, exercise library, workout timer, PR tracking
**Phase 4** — RAG with exercise science papers, photo/video analysis, predictive modeling
