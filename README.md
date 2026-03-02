# Fit Agent

AI-powered fitness tracking for a small group (2-3 users). Uses Claude Sonnet via PydanticAI agents for workout programming, nutrition planning, and progress analysis. Server-rendered with HTMX for zero-JS-framework simplicity.

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
  │   PostgreSQL 16     │  │   PydanticAI Agents                 │
  │   + SQLModel ORM    │  │   (Claude Sonnet 4.5)               │
  │                     │  │                                     │
  │   users             │  │   Planning ─── workout programs     │
  │   profiles          │  │   Nutrition ── macro targets        │
  │   workout_plans     │  │   Analysis ─── progress trends      │
  │   workout_sessions  │  │                                     │
  │   exercise_logs     │  │                                     │
  │   meal_logs         │  │                                     │
  │   weight_logs       │  │                                     │
  │   nutrition_targets │  └─────────────────────────────────────┘
  └─────────────────────┘
```

### AI Agents

All agents currently run on Claude Sonnet 4.5 via PydanticAI:

| Agent | Purpose | Trigger |
|-------|---------|---------|
| **Planning** | Generate periodized workout programs (4-12 weeks) | Onboarding, user request |
| **Nutrition** | Macro targets and meal suggestions | User request |
| **Analysis** | Progress trend detection and coaching adjustments | Weekly, dashboard views |

## Features

- **Workout plan generation** — AI-generated periodized programs adapted to equipment, experience, injuries, and time constraints
- **Nutrition targets** — Macro calculations and meal suggestions based on goals and body composition
- **Data logging** — Track weight, meals, and workouts through a server-rendered UI
- **Progress analysis** — Trend detection and coaching adjustments
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

### Deployment

Not yet deployed. Local development only.

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

## Tech Stack

Python 3.13+ / FastAPI / PostgreSQL 16 / SQLModel / PydanticAI / Claude Sonnet / HTMX + Alpine.js + Tailwind CSS / FastAPI-Users (JWT) / Alembic

## Roadmap

**Phase 1 (current)** — Core logging, auth, AI generation with Claude Sonnet
**Phase 2** — Multi-model orchestration (GPT for extraction, Gemini for long-context), Redis caching, background scheduling, NL logging
**Phase 3** — Chart.js visualizations, exercise library, workout timer, PR tracking
**Phase 4** — RAG with exercise science papers, photo/video analysis, predictive modeling
