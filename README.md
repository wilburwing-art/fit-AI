# Fit Agent

AI-powered fitness tracking for a small group (2-3 users). Uses a multi-model strategy across Claude, GPT, and Gemini to generate periodized workout programs, nutrition targets, and adaptive coaching — without the $50+/month API bill that a single-model approach would incur.

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
  │  (JWT)     (weight,          (workout plan,    (Jinja2        │
  │             meals,            nutrition plan)    templates)    │
  │             workouts)                                         │
  └──────────┬───────────────────────┬───────────────────────────┘
             │                       │
  ┌──────────▼──────────┐  ┌────────▼────────────────────────────┐
  │   PostgreSQL 16     │  │   PydanticAI Multi-Model Strategy   │
  │   + SQLModel ORM    │  │                                     │
  │                     │  │   Planning ─── Claude Opus 4.1      │
  │   users             │  │   Analysis ─── Claude Sonnet 4.5    │
  │   profiles          │  │   Coaching ─── Claude Sonnet 4.5    │
  │   workout_plans     │  │   Extraction ─ GPT-5-mini           │
  │   workout_sessions  │  │   Long-ctx ─── Gemini 2.5 Pro (1M) │
  │   exercise_logs     │  │                                     │
  │   meal_logs         │  │   Target: $10-20/month              │
  │   weight_logs       │  │   for 2-3 users                     │
  │   nutrition_targets │  └─────────────────────────────────────┘
  └─────────────────────┘
```

### Multi-Model AI Strategy

Each model is matched to its strength to optimize cost and quality:

| Agent | Model | Trigger | Why This Model |
|-------|-------|---------|----------------|
| **Planning** | Claude Opus 4.1 | Onboarding, weekly review | Deep reasoning for periodized program design |
| **Analysis** | Claude Sonnet 4.5 | Weekly automated job | Trend detection at moderate cost |
| **Coaching** | Claude Sonnet 4.5 | User chat | Conversational, context-aware responses |
| **Extraction** | GPT-5-mini | Every log entry | Fast, cheap NL-to-structured-data parsing |
| **Long-Context** | Gemini 2.5 Pro | Deep analysis | 1M tokens = 2+ years of history without RAG |

## Features

- **Workout plan generation** — AI-generated periodized programs (4-12 weeks) adapted to equipment, experience, injuries, and time constraints
- **Nutrition targets** — Macro calculations and meal suggestions based on goals and body composition
- **Data logging** — Track weight, meals, and workouts through a server-rendered UI
- **Progress analysis** — Automated weekly trend detection and coaching adjustments
- **JWT authentication** — Secure registration and login via FastAPI-Users
- **Rate-limited AI** — Per-user limits prevent cost spirals (5 AI requests/day)

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

### Deploy to Fly.io

```bash
fly launch
fly secrets set ANTHROPIC_API_KEY=sk-ant-... SECRET_KEY=$(openssl rand -hex 32)
fly deploy
```

Configured for 512MB VM with auto-scaling (0-25 connections) in `fly.toml`.

## Project Structure

```
src/
├── api/
│   ├── auth.py       # Registration, login, password reset (FastAPI-Users)
│   ├── data.py       # Weight, meal, workout logging endpoints
│   ├── ai.py         # Workout plan + nutrition plan generation
│   └── pages.py      # Server-rendered HTML routes (Jinja2)
├── models/
│   ├── user.py       # User, UserProfile, Goal (SQLModel)
│   ├── workout.py    # WorkoutPlan, WorkoutSession, ExerciseLog
│   └── nutrition.py  # WeightLog, MealLog, NutritionTarget
├── services/
│   └── ai.py         # PydanticAI agent definitions + orchestration
├── templates/        # HTMX + Alpine.js templates
├── config.py         # Pydantic Settings (env vars)
├── database.py       # Async PostgreSQL connection
├── auth.py           # JWT strategy, user manager
├── schemas.py        # Request/response validation
└── main.py           # FastAPI app factory
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
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `SECRET_KEY` | Yes | JWT signing key (`openssl rand -hex 32`) |
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `OPENAI_API_KEY` | Phase 2 | GPT-5-mini for data extraction |
| `GOOGLE_API_KEY` | Phase 2 | Gemini 2.5 Pro for long-context analysis |
| `REDIS_URL` | Phase 2 | Caching AI responses (7-day TTL) |
| `LOGFIRE_TOKEN` | Phase 2 | Pydantic Logfire observability |

## Tech Stack

Python 3.13+ / FastAPI / PostgreSQL 16 / SQLModel / PydanticAI / Claude + GPT + Gemini / HTMX + Alpine.js + Tailwind CSS / FastAPI-Users (JWT) / Alembic / Fly.io

## Roadmap

**Phase 1 (current)** — Core logging, auth, basic AI generation, Fly.io deployment
**Phase 2** — Multi-model orchestration, Redis caching, background scheduling, NL logging
**Phase 3** — Chart.js visualizations, exercise library, workout timer, PR tracking
**Phase 4** — RAG with exercise science papers, photo/video analysis, predictive modeling
