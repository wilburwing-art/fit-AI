# Architecture

## System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Browser        │────▶│  FastAPI         │────▶│  PostgreSQL     │
│  (HTMX/Alpine)  │◀────│  + Jinja2        │◀────│  (SQLModel)     │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ Claude   │      │ OpenAI   │      │ Gemini   │
        │ (Plan/   │      │ (Extract)│      │ (Long    │
        │  Coach)  │      │          │      │  Context)│
        └──────────┘      └──────────┘      └──────────┘
```

## Multi-Model AI Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                        PydanticAI Orchestration                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Planning    │  │ Analysis    │  │ Conversation│             │
│  │ Agent       │  │ Agent       │  │ Agent       │             │
│  │             │  │             │  │             │             │
│  │ Claude Opus │  │ Claude      │  │ Claude      │             │
│  │ 4.1         │  │ Sonnet 4.5  │  │ Sonnet 4.5  │             │
│  │             │  │             │  │             │             │
│  │ Trigger:    │  │ Trigger:    │  │ Trigger:    │             │
│  │ Weekly/     │  │ Weekly      │  │ User chat   │             │
│  │ Onboarding  │  │ automated   │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Extraction  │  │ Long-Context│                               │
│  │ Agent       │  │ Agent       │                               │
│  │             │  │             │                               │
│  │ GPT-5-mini  │  │ Gemini 2.5  │                               │
│  │             │  │ Pro (1M)    │                               │
│  │ Trigger:    │  │             │                               │
│  │ NL logging  │  │ Trigger:    │                               │
│  │             │  │ Deep review │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Map

```
src/
├── main.py                 # FastAPI app, lifespan
├── api/
│   ├── routes/             # HTMX endpoints
│   │   ├── dashboard.py
│   │   ├── workouts.py
│   │   ├── nutrition.py
│   │   └── chat.py
│   └── dependencies.py     # Auth, user context
├── agents/                 # PydanticAI agent definitions
│   ├── planning.py         # Workout program generation
│   ├── analysis.py         # Progress analysis
│   ├── conversation.py     # Coaching chat
│   └── extraction.py       # NL → structured data
├── services/               # Business logic
│   ├── workout_service.py
│   ├── nutrition_service.py
│   └── analysis_service.py
├── models/                 # SQLModel (ORM + Pydantic)
│   ├── user.py
│   ├── workout.py
│   ├── nutrition.py
│   └── cache.py            # AI response cache
├── templates/              # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   └── components/         # HTMX partials
└── core/
    ├── config.py
    ├── database.py
    └── cache.py            # Redis caching
```

## Data Model

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users     │────▶│  user_profiles   │     │  workout_plans   │
│              │     │  (traits, goals) │     │  (AI-generated)  │
└──────────────┘     └──────────────────┘     └──────────────────┘
       │                                              │
       │         ┌──────────────────┐                │
       └────────▶│ workout_sessions │◀───────────────┘
                 │ (actual workouts)│
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │  exercise_logs   │
                 │ (sets, reps, wt) │
                 └──────────────────┘

┌──────────────┐     ┌──────────────────┐
│  meal_logs   │     │  weight_logs     │
│              │     │  (body metrics)  │
└──────────────┘     └──────────────────┘
```

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   HTMX      │  │  Alpine.js  │  │  Tailwind   │             │
│  │             │  │             │  │             │             │
│  │ • Partial   │  │ • Local     │  │ • Utility   │             │
│  │   updates   │  │   state     │  │   classes   │             │
│  │ • Form      │  │ • Toggles   │  │ • Mobile-   │             │
│  │   handling  │  │ • Modals    │  │   first     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  No build step • Server-rendered • Progressive enhancement      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Multi-model AI | Cost optimization ($10-20/mo for 2-3 users) |
| PydanticAI | Type-safe agent orchestration |
| SQLModel | Single source for ORM + Pydantic schemas |
| HTMX over React | Simpler, faster dev for small team |
| Redis caching | 7-day TTL on AI-generated plans |
| Fly.io | Free tier for MVP, easy scaling |
