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
| **Coaching** | Claude Sonnet 4.5 | Conversational Q&A with user context | User request |
| **Analysis** | Claude Sonnet 4.5 | Progress trend detection and coaching | Weekly (scheduled) |
| **NL Parser** | GPT-4o-mini | Parse "225x5x3" into structured data | User request |
| **Long-context** | Gemini 2.5 Pro | Longitudinal analysis over months of data | On demand |

All model names are configurable via environment variables.

## Features

- **Exercise library** — 800+ exercises from free-exercise-db with search, filter by muscle/equipment/category/difficulty, detail pages with images and instructions, and user preference toggles (favorite/exclude)
- **Per-exercise set logging** — Log weight x reps @RPE per set, multiple exercises per workout session
- **Workout timer** — Stopwatch and rest countdown modes with 1:00/1:30/2:00/3:00 presets, beep + vibrate alerts, auto-start on reps input
- **PR tracking** — Automatic personal record detection via Epley 1RM, toast celebrations on workout submit, PR badges on dashboard
- **Training preferences** — Goal, split, days/week, session duration, volume and cardio targets
- **Muscle recovery tracking** — 72h recovery model with per-muscle status (fresh/ready/recovering)
- **Strength scores** — Estimated 1RM via Epley formula, bodyweight-ratio strength levels
- **Weekly targets** — Track workouts, sets, and active minutes against personal targets with radar chart
- **Calendar view** — Monthly calendar with workout badges, exercise names, and duration per day
- **Data visualizations** — Weight trends, workout activity, training volume, macro adherence charts (Chart.js)
- **AI coaching** — Conversational Q&A at `/coach` with context from recent workouts, weight, meals, and profile
- **Dark theme** — Tailwind dark mode with localStorage toggle, all pages supported
- **Mobile-first UI** — Bottom navigation bar, 44px touch targets, responsive layouts
- **Workout plan generation** — AI-generated periodized programs adapted to equipment, experience, injuries, and time constraints
- **Nutrition targets** — Macro calculations and meal suggestions based on goals and body composition
- **Natural language logging** — Parse "Squats 225x5x3 @RPE8" or "chicken breast 8oz with rice" into structured data
- **Data logging** — Track weight, meals, and workouts through a server-rendered UI
- **Data export** — Download fitness data as JSON or CSV with configurable date range (1-365 days)
- **Automated progress analysis** — Weekly scheduled analysis for all active users
- **Redis caching** — 7-day TTL on AI responses, cache invalidation on new data, graceful degradation when Redis is down
- **Observability** — Logfire instrumentation on all AI and cache operations
- **JWT authentication** — Secure registration and login via FastAPI-Users
- **Rate-limited AI** — Per-user limits prevent cost spirals (5 plan requests/day, 20 coaching/hour, 30 NL parses/hour)

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

# Seed exercise library (800+ exercises)
uv run python -m src.scripts.import_exercises

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
│   ├── exercises.py  # Exercise library search/filter/detail/preferences
│   ├── analytics.py  # Recovery, strength, weekly, calendar, macros, volume, preferences, PRs
│   ├── ai.py         # Plan generation, NL parsing, coaching endpoints
│   ├── export.py     # JSON and CSV data export
│   └── pages.py      # Server-rendered HTML routes (Jinja2)
├── models/
│   ├── user.py       # User, UserProfile, Goal (SQLModel)
│   ├── workout.py    # WorkoutPlan, Exercise, WorkoutSession, ExerciseLog, UserExercisePreference
│   ├── nutrition.py  # WeightLog, MealLog, NutritionTarget
│   └── ai.py         # AnalysisCache, ScheduledJob
├── services/
│   ├── ai.py         # Multi-model PydanticAI agents + cache integration
│   ├── cache.py      # Redis caching with graceful degradation
│   ├── nl_parser.py  # Natural language workout/meal parsing
│   └── scheduler.py  # APScheduler background jobs (weekly analysis)
├── scripts/
│   └── import_exercises.py  # Seed 800+ exercises from free-exercise-db
├── templates/
│   ├── exercises/    # Exercise library browse + detail pages
│   └── ...           # Other HTMX + Alpine.js templates
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
POST /api/workouts          # Log workout session (with exercise_logs)
GET  /api/recent-activity   # Combined activity feed
```

### Exercises
```
GET  /api/exercises              # Search/filter (q, muscle, equipment, category, difficulty)
GET  /api/exercises/filters      # Distinct values for filter dropdowns
GET  /api/exercises/{id}         # Exercise detail
POST /api/exercises/preferences  # Set favorite/excluded (auth required)
DELETE /api/exercises/preferences/{id}  # Remove preference
GET  /api/exercises/preferences  # List user preferences
```

### Analytics
```
GET  /api/analytics/recovery            # Muscle recovery status
GET  /api/analytics/strength            # Strength scores (1RM estimates)
GET  /api/analytics/weekly              # Weekly progress vs targets
GET  /api/analytics/calendar            # Monthly workout calendar (?year=&month=)
GET  /api/analytics/macros              # Daily macro totals (?days=30)
GET  /api/analytics/volume              # Training volume over time (?days=90)
GET  /api/analytics/prs                 # Personal records (?days=90)
GET  /api/analytics/prs/session/{id}    # PRs from a specific session
GET  /api/analytics/preferences         # Training preferences
PUT  /api/analytics/preferences         # Update training preferences
```

### AI
```
POST /api/ai/generate-workout-plan     # Periodized program generation
POST /api/ai/generate-nutrition-plan   # Macro targets + meal suggestions
POST /api/ai/parse-workout             # NL workout → structured data
POST /api/ai/parse-meal                # NL meal → structured data
POST /api/ai/coach                     # Conversational Q&A coaching (20/hour)
```

### Export
```
GET  /api/export/json                  # Download all data as JSON (?days=90)
GET  /api/export/csv                   # Download all data as CSV (?days=90)
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
# Run tests (90 tests: auth, data, AI, cache, NL parser, exercises, analytics, coaching, export)
uv run pytest -v

# Lint and format
uvx ruff check --fix . && uvx ruff format .
```

## Roadmap

**Phase 1 (~95%)** — Core logging, auth, AI generation, test suite, deployment configs
**Phase 2 (~90%)** — Multi-model AI, Redis caching, APScheduler, NL parsing, Logfire observability
**Phase 3 (~95%)** — Exercise library, set logging, training preferences, muscle recovery, strength scores, weekly targets, calendar, dark theme, mobile optimization, charts, workout timer, PR tracking with celebrations, AI coaching Q&A, data export (JSON/CSV)
**Phase 4** — RAG with exercise science papers, photo/video analysis, predictive modeling
