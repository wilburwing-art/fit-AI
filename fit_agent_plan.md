# Fit Agent - AI-Powered Fitness Tracking Platform

## Executive Summary

A Python-based fitness tracking web application for 2-3 users that leverages cutting-edge generative AI to provide personalized workout planning, nutrition guidance, and adaptive long-term coaching based on individual progress and traits.

**Core Value Proposition**: Unlike marketplace fitness apps, this platform uses the latest frontier AI models (Claude 4.5 Sonnet, GPT-5 series, Gemini 2.5 Pro) to provide truly personalized, adaptive coaching that evolves with your progress - capabilities not yet widely available in commercial products.

---

## Architecture Overview

### Technology Stack

```
┌─────────────────────────────────────────┐
│  Frontend: HTMX + Alpine.js + Tailwind  │
│  Mobile-first, server-rendered          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Backend: FastAPI (async Python)        │
│  ├─ FastAPI-Users (auth)                │
│  ├─ SQLModel (type-safe ORM)            │
│  ├─ APScheduler (background jobs)       │
│  └─ Pydantic for validation             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  AI Layer: Multi-Model Strategy         │
│  ├─ PydanticAI (agent orchestration)    │
│  ├─ Claude 4.5 Sonnet (coding/agents)   │
│  ├─ Claude Opus 4.1 (deep reasoning)    │
│  ├─ Claude Haiku 4.5 (high-volume)      │
│  ├─ GPT-5 series (structured data)      │
│  ├─ Gemini 2.5 Pro (1M context window)  │
│  └─ Logfire (observability/costs)       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Data: PostgreSQL + Redis               │
│  ├─ PostgreSQL (primary data)           │
│  └─ Redis (AI response caching)         │
└─────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Infrastructure: Fly.io                 │
│  ├─ Multi-region deployment             │
│  ├─ Managed Postgres                    │
│  └─ Free tier → $0/month hosting        │
└─────────────────────────────────────────┘
```

**Cost Estimate:**
- **MVP (2-3 users)**: $5-15/month (AI APIs only, free hosting)
- **Scaled (20 users)**: $100-200/month (hosting + AI)

---

## Core Features

### 1. User Profile & Goal Setting
- **Onboarding flow**: Capture age, fitness level, injuries, preferences, equipment access
- **Goal tracking**: Weight loss, muscle gain, endurance, sport-specific performance
- **Trait-based personalization**: Work schedule, recovery capacity, food preferences, dietary restrictions
- **Progress milestones**: Define short/medium/long-term objectives

### 2. Workout Management
- **AI-generated programs**: Periodized training plans based on goals and constraints
- **Exercise library**: Searchable database with form cues and progressions
- **Workout logging**: Sets, reps, weight, RPE, notes
- **Performance analytics**: Volume trends, strength progression, frequency patterns
- **Adaptive adjustments**: AI modifies intensity/volume based on recovery signals

### 3. Nutrition Tracking
- **Meal logging**: Quick entry with macro calculation
- **Macro targets**: AI-recommended protein/carbs/fats based on goals and activity
- **Food database**: Common foods with nutritional info (USDA integration optional)
- **Meal suggestions**: AI-generated meal ideas meeting macro targets
- **Weekly nutrition review**: AI analyzes adherence and suggests adjustments

### 4. Body Metrics
- **Weight tracking**: Daily/weekly logging with trend smoothing
- **Body composition**: Optional measurements (waist, arms, etc.)
- **Progress visualization**: Charts showing trends over time
- **Correlation analysis**: AI identifies patterns (e.g., sleep vs performance)

### 5. AI Coaching Agent
- **Conversational interface**: Ask questions about technique, nutrition, programming
- **Weekly analysis**: Automated review of progress with plan adjustments
- **Context-aware**: Agent has full access to your history and traits
- **Proactive suggestions**: "Your bench volume is down 15% - adjust or deload?"
- **Knowledge grounding**: RAG with fitness research, exercise science papers

---

## AI Agent Architecture

### Agent Roles & Responsibilities

#### 1. **Planning Agent** (Claude Opus 4.1)
**Purpose**: Generate and adjust workout/nutrition plans

**Model choice**: Claude Opus 4.1 offers the deepest reasoning for complex program design, balancing recovery, progression, and individual constraints.

**Inputs**:
- User goals, traits, constraints
- Historical performance data
- Current fitness level
- Equipment availability

**Outputs**:
- 4-12 week periodized workout programs
- Weekly macro targets
- Exercise selection and progression scheme

**Trigger**:
- Initial onboarding
- Weekly automated review
- User-requested plan change

**Prompt Strategy**:
```python
system_prompt = """
You are an expert strength coach and sports nutritionist.
Analyze the user's progress data and create optimized training plans.

Context:
- User: {age} years old, {experience_level}, goals: {goals}
- Constraints: {injuries}, {time_availability}, {equipment}
- Recent performance: {last_4_weeks_summary}

Guidelines:
1. Prioritize safety and sustainable progress
2. Respect recovery constraints (sleep, stress, age)
3. Progressive overload with appropriate deloads
4. Exercise variety balanced with specificity
"""
```

#### 2. **Analysis Agent** (Claude 4.5 Sonnet)
**Purpose**: Identify trends, correlations, and insights

**Model choice**: Claude 4.5 Sonnet excels at agentic tasks and analyzing structured data patterns efficiently.

**Inputs**:
- Time-series data (weight, performance, macros)
- Subjective feedback (energy, soreness, sleep quality)

**Outputs**:
- Progress summaries
- Pattern identification (e.g., "performance drops when protein < 150g")
- Risk flags (overtraining, underrecovery)

**Trigger**:
- Weekly automated
- User dashboard view
- Pre-plan adjustment

#### 3. **Conversational Agent** (Claude 4.5 Sonnet)
**Purpose**: Answer questions and provide coaching

**Model choice**: Claude 4.5 Sonnet provides natural, context-aware responses with extended thinking for complex coaching questions.

**Inputs**:
- User question
- Full user context (goals, current plan, recent logs)

**Outputs**:
- Contextual answers
- Form cues
- Technique explanations
- Motivation and accountability

**Trigger**: User-initiated chat

**RAG Integration**:
- Vector database with exercise science literature
- Technique guides and form videos
- Nutrition research summaries

#### 4. **Data Extraction Agent** (GPT-5-mini)
**Purpose**: Parse natural language input into structured data

**Model choice**: GPT-5-mini provides excellent structured extraction at low cost. For critical extraction requiring maximum accuracy, GPT-5 can be used with higher reasoning levels.

**Inputs**:
- "Bench 225x5x3 @RPE 8, felt good"
- "Chicken breast, rice, broccoli - ~40p/50c/10f"

**Outputs**:
- Structured workout log entry
- Parsed meal with macros

**Trigger**: User input via chat or form

**Configuration**:
```python
extraction_agent = Agent(
    'openai:gpt-5-mini',
    reasoning_effort='minimal',  # Fast, cost-effective
    result_type=WorkoutLog
)
```

**Advantages**:
- Structured output mode ensures reliable JSON parsing
- Four reasoning levels: use 'minimal' for fast extraction, 'high' for critical data
- 45% less hallucination than GPT-4o (GPT-5 series)

### AI Cost Optimization Strategy

1. **Tiered model usage**:
   - **Claude Opus 4.1**: Deep reasoning for workout/nutrition planning (weekly/bi-weekly)
   - **Claude 4.5 Sonnet**: Conversational coaching, progress analysis (daily interactions)
   - **Claude Haiku 4.5**: Simple queries, data validation, high-volume tasks (10x cheaper than Sonnet for input)
   - **GPT-5-mini**: Fast, cost-effective structured data extraction
   - **Gemini 2.5 Flash**: Alternative for high-volume, low-latency tasks

2. **Caching layer** (Redis):
   - Cache AI-generated plans (TTL: 7 days)
   - Cache exercise library lookups
   - Cache common Q&A responses

3. **Batching**:
   - Weekly analysis runs once, not per-view
   - Consolidate user queries when possible

4. **Prompt optimization**:
   - Minimize token usage in context
   - Use structured outputs to reduce parsing
   - Iterative prompt refinement based on Logfire metrics

---

## Current AI Model Capabilities (November 2025)

### Model Selection Rationale

#### **Anthropic Claude 4.x Series**

**Claude Opus 4.1** (API: `claude-opus-4-1-20250805`)
- **Best for**: Deep reasoning, complex workout programming, strategic planning
- **Strengths**:
  - World-class coding model (74.5% on SWE-bench Verified)
  - Extended thinking mode for self-checking and refinement
  - Superior at balancing multiple constraints (injuries, goals, equipment, time)
- **Context window**: 200K tokens
- **Use case in app**: Weekly/bi-weekly program generation and major plan adjustments
- **Cost**: Higher, but used sparingly for critical decisions

**Claude 4.5 Sonnet** (API: `claude-sonnet-4-5-20250929`)
- **Best for**: Agentic tasks, conversational coaching, real-time analysis
- **Strengths**:
  - Excellent for coding and agent workflows
  - Computer Use capabilities (can interact with UIs)
  - Natural, contextual responses for coaching conversations
  - Strong creative writing (better tone/style control than GPT models)
- **Context window**: 200K tokens (1M tokens in beta)
- **Use case in app**: Daily coaching interactions, progress analysis, Q&A
- **Cost**: Mid-range, suitable for frequent use

#### **OpenAI GPT-5 Series**

**GPT-5** (API: `gpt-5`)
- **Best for**: Structured data extraction, JSON output, adaptive reasoning
- **Strengths**:
  - 94.6% on AIME 2025 (math reasoning)
  - 74.9% on SWE-bench Verified (coding)
  - 45% less hallucination than GPT-4o
  - 80% less hallucination when using high reasoning mode
  - Adaptive reasoning levels (minimal, low, medium, high)
- **Context window**: 200K tokens
- **Use case in app**: Critical extraction tasks requiring maximum accuracy
- **Cost**: Premium, but extremely reliable for critical decisions

**GPT-5-mini** (API: `gpt-5-mini`)
- **Best for**: High-volume, low-latency structured extraction
- **Strengths**:
  - Significantly cheaper than GPT-5
  - Fast response times
  - Maintains strong structured output capabilities
  - Supports reasoning levels (minimal, low, medium, high)
- **Context window**: 128K-200K tokens
- **Use case in app**: Parsing natural language workout/meal logs into structured data
- **Cost**: Low, ideal for high-frequency operations

**GPT-5-nano** (API: `gpt-5-nano`)
- **Best for**: Ultra-fast, simple tasks with minimal reasoning
- **Strengths**:
  - Very low cost
  - Fast response times
  - Good for simple classification and validation
- **Use case in app**: Simple classification, tag generation, data validation
- **Cost**: Very low

#### **Google Gemini 2.x Series**

**Gemini 2.5 Pro** (API: `gemini-2.5-pro`)
- **Best for**: Large context analysis, multimodal understanding, video processing
- **Strengths**:
  - **1,000,000 token context window** - revolutionary for fitness tracking
    - Can analyze months/years of workout history in single context
    - Entire exercise library + user history + research papers in one prompt
  - Native multimodal (text, images, video, audio)
  - Deep Think mode for complex reasoning
  - Computer Use capabilities
- **Context window**: 1M tokens
- **Use case in app**:
  - Long-term trend analysis (entire training history at once)
  - Meal photo analysis
  - Form check videos
  - Correlation discovery across massive datasets
- **Cost**: Moderate, excellent value given 1M context

**Gemini 2.5 Flash** (API: `gemini-2.5-flash`)
- **Best for**: Efficient, fast multimodal tasks
- **Strengths**:
  - Ranked #2 on LMarena leaderboard (after 2.5 Pro)
  - 22% efficiency gains over previous version
  - Fast response times
  - Good balance of performance and cost
- **Context window**: Likely 128K-1M tokens
- **Use case in app**: Quick image analysis, real-time suggestions
- **Cost**: Low

**Gemini 2.5 Flash-Lite** (API: `gemini-2.5-flash-lite`)
- **Best for**: High-volume, cost-sensitive tasks
- **Strengths**: Most cost-efficient model in Google's lineup
- **Use case in app**: Simple queries, data validation
- **Cost**: Very low

### Model API Implementation Examples

#### PydanticAI Configuration

```python
from pydantic_ai import Agent
from pydantic import BaseModel

# Planning agent with Claude Opus 4.1
class WorkoutPlan(BaseModel):
    weeks: int
    phases: list[dict]
    rationale: str

planning_agent = Agent(
    'anthropic:claude-opus-4-1-20250805',
    result_type=WorkoutPlan,
    system_prompt="""You are an expert strength coach creating
    periodized training programs..."""
)

# Conversational agent with Claude 4.5 Sonnet
coaching_agent = Agent(
    'anthropic:claude-sonnet-4-5-20250929',
    system_prompt="""You are a supportive fitness coach..."""
)

# Data validation with Claude Haiku 4.5 (cost-effective for high volume)
validation_agent = Agent(
    'anthropic:claude-haiku-4-5-20251001',
    system_prompt="""Validate and normalize exercise names and data..."""
)

# Data extraction with GPT-5-mini
class WorkoutLog(BaseModel):
    exercise: str
    sets: list[dict]
    rpe: int
    notes: str

extraction_agent = Agent(
    'openai:gpt-5-mini',
    result_type=WorkoutLog,
    reasoning_effort='minimal',  # Fast extraction without deep reasoning
    system_prompt="""Extract workout data from natural language..."""
)

# Long-term analysis with Gemini 2.5 Pro (1M context!)
analysis_agent = Agent(
    'google:gemini-2.5-pro',
    system_prompt="""Analyze the user's complete training history
    and identify patterns, correlations, and insights..."""
)
```

#### Direct API Usage (Alternative to PydanticAI)

```python
# Anthropic SDK
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Using dated endpoint for stability
response = await client.messages.create(
    model="claude-opus-4-1-20250805",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}]
)

# OpenAI SDK with reasoning levels
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = await client.chat.completions.create(
    model="gpt-5-mini",  # or "gpt-5", "gpt-5-nano"
    messages=[{"role": "user", "content": prompt}],
    reasoning_effort="minimal",  # minimal, low, medium, high
    response_format={"type": "json_object"}
)

# Google Generative AI SDK
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')

# Can pass enormous context (1M tokens!)
response = await model.generate_content_async(
    [all_workout_history, all_nutrition_logs, user_profile, prompt]
)
```

### Gemini 2.5 Pro: Game-Changer for Fitness Tracking

The **1 million token context window** is revolutionary for this use case:

**Traditional approach (200K context)**:
- Summarize workout history → lose details
- Query database for relevant data → miss patterns
- Process in chunks → lose long-term trends

**With Gemini 2.5 Pro (1M context)**:
- Include complete 2-year workout history (~400K tokens)
- Include complete nutrition logs (~200K tokens)
- Include full exercise library (~50K tokens)
- Include research papers (~300K tokens)
- Still have room for prompt and response

**Example use case**:
```python
# Build massive context with ALL user data
context = {
    "workout_history": fetch_all_workouts(user_id),  # 2 years
    "nutrition_logs": fetch_all_meals(user_id),      # 2 years
    "weight_logs": fetch_all_weights(user_id),       # 2 years
    "goals": user.goals,
    "injuries": user.injuries,
    "exercise_library": all_exercises,
    "research": fitness_science_papers
}

prompt = """
Given this user's COMPLETE training and nutrition history,
identify:
1. Which exercises produce best strength gains?
2. Optimal training frequency for this individual?
3. Nutrition patterns that correlate with performance?
4. Early warning signs of overtraining?
5. Personalized recommendations for next 12 weeks?
"""

# Single API call with EVERYTHING
response = await gemini_2_5_pro.generate(context + prompt)
```

This eliminates the need for:
- Vector databases (for most use cases)
- Complex RAG pipelines
- Data summarization
- Lossy compression of user history

**Cost consideration**: While Gemini 2.5 Pro costs more per token, you save on:
- No vector database hosting
- Fewer API calls (one comprehensive call vs many small ones)
- No RAG infrastructure
- Simplified architecture

### Recommended Model Strategy

**Phase 1 (MVP)**: Start with single-model simplicity
- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) for everything
- Proves concept with minimal complexity
- Easy to test and iterate

**Phase 2 (Optimized)**: Multi-model for cost/performance
- **Claude Opus 4.1** (`claude-opus-4-1-20250805`): Weekly program generation
- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`): Daily coaching, Q&A
- **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`): Data validation, simple tasks
- **GPT-5-mini** (with `reasoning_effort='minimal'`): Data extraction from logs
- **Gemini 2.5 Flash**: Quick image analysis

**Phase 3 (Advanced)**: Leverage each model's strengths
- **Gemini 2.5 Pro**: Deep analysis with full history (weekly, 1M context)
- **Claude Opus 4.1**: Strategic planning decisions
- **Claude Sonnet 4.5**: Real-time coaching (1M context beta)
- **Claude Haiku 4.5**: High-volume validation and classification
- **GPT-5-nano** (with `reasoning_effort='minimal'`): Ultra-fast simple tasks

### API Cost Estimates (Approximate, November 2025)

**Input Pricing** (per 1M tokens):
- Claude Opus 4.1: $15
- Claude Sonnet 4.5: $3
- Claude Haiku 4.5: $1
- GPT-5: $1.25
- GPT-5-mini: $0.25
- GPT-5-nano: $0.05
- Gemini 2.5 Pro: $1.25
- Gemini 2.5 Flash: $0.075

**Output Pricing** (per 1M tokens):
- Claude Opus 4.1: $75
- Claude Sonnet 4.5: $15
- Claude Haiku 4.5: $5
- GPT-5: $10
- GPT-5-mini: $2
- GPT-5-nano: $0.40
- Gemini 2.5 Pro: $5
- Gemini 2.5 Flash: $0.30

**Monthly cost for 2-3 users** (estimated Phase 2):
- Daily coaching (Claude Sonnet 4.5): $4-8
- Weekly planning (Claude Opus 4.1): $3-5
- Data extraction (GPT-5-mini minimal): $1-2
- Data validation (Claude Haiku 4.5): $0.50-1
- Deep analysis (Gemini 2.5 Pro): $2-3
- **Total: $10.50-19/month**

**Scaling to 20 users**: $75-125/month

---

## Database Schema

### Core Tables

```sql
-- Users and authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User profiles and traits
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    age INTEGER,
    sex VARCHAR(10),
    experience_level VARCHAR(50), -- beginner, intermediate, advanced
    equipment_access TEXT[], -- ['barbell', 'dumbbells', 'squat_rack']
    injuries TEXT,
    time_availability INTEGER, -- minutes per week
    preferences JSONB, -- sleep schedule, food preferences, etc.
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Goals
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    goal_type VARCHAR(50), -- weight_loss, muscle_gain, strength, endurance
    target_value NUMERIC,
    target_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, abandoned
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI-generated workout plans (versioned)
CREATE TABLE workout_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    version INTEGER,
    start_date DATE,
    end_date DATE,
    plan_data JSONB, -- full program structure
    ai_rationale TEXT, -- why this plan was chosen
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, version)
);

-- Exercise library
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50), -- compound, isolation, cardio
    muscle_groups TEXT[], -- ['chest', 'triceps', 'shoulders']
    equipment_required TEXT[], -- ['barbell', 'bench']
    difficulty VARCHAR(20),
    form_cues TEXT,
    video_url VARCHAR(500)
);

-- Workout sessions
CREATE TABLE workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    workout_plan_id INTEGER REFERENCES workout_plans(id),
    scheduled_date DATE,
    completed_date DATE,
    duration_minutes INTEGER,
    overall_rpe INTEGER, -- 1-10
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual exercise logs
CREATE TABLE exercise_logs (
    id SERIAL PRIMARY KEY,
    workout_session_id INTEGER REFERENCES workout_sessions(id),
    exercise_id INTEGER REFERENCES exercises(id),
    sets_data JSONB, -- [{"set": 1, "reps": 5, "weight": 225, "rpe": 8}]
    notes TEXT
);

-- Body metrics
CREATE TABLE weight_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    weight_lbs NUMERIC(5,1),
    body_fat_pct NUMERIC(4,1),
    measurements JSONB, -- {"waist": 32, "arms": 15}
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Meal logs
CREATE TABLE meal_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    meal_type VARCHAR(20), -- breakfast, lunch, dinner, snack
    description TEXT,
    protein_g NUMERIC(5,1),
    carbs_g NUMERIC(5,1),
    fat_g NUMERIC(5,1),
    calories INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Nutrition targets (AI-generated)
CREATE TABLE nutrition_targets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    start_date DATE,
    end_date DATE,
    daily_protein_g INTEGER,
    daily_carbs_g INTEGER,
    daily_fat_g INTEGER,
    daily_calories INTEGER,
    ai_rationale TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI analysis results (cached)
CREATE TABLE analysis_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    analysis_type VARCHAR(50), -- weekly_review, progress_summary
    analysis_date DATE,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled jobs tracking
CREATE TABLE scheduled_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_type VARCHAR(50), -- weekly_review, plan_adjustment
    schedule_expression VARCHAR(100), -- cron format
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Indexing Strategy

```sql
-- Performance optimization
CREATE INDEX idx_workout_sessions_user_date ON workout_sessions(user_id, completed_date);
CREATE INDEX idx_exercise_logs_session ON exercise_logs(workout_session_id);
CREATE INDEX idx_weight_logs_user_date ON weight_logs(user_id, date);
CREATE INDEX idx_meal_logs_user_date ON meal_logs(user_id, date);
CREATE INDEX idx_goals_user_active ON goals(user_id) WHERE status = 'active';

-- JSONB indexes for plan queries
CREATE INDEX idx_workout_plans_data ON workout_plans USING GIN (plan_data);
```

---

## Implementation Roadmap

---

## **CURRENT STATUS UPDATE** (2026-03-04)

### **Phase 1 Progress: ~95% Complete**

**✅ Completed:**
- Project setup (uv + Python 3.13)
- FastAPI app structure with async SQLAlchemy
- SQLModel models (User, WorkoutSession, MealLog, WeightLog, ExerciseLog, AIAnalysisCache)
- FastAPI-Users authentication (JWT + cookie dual backend)
- UI templates (10 pages: index, login, register, dashboard, workouts, nutrition, exercises, exercise detail, preferences, calendar)
- API endpoints for weight/meal/workout logging (POST/GET)
- PydanticAI agents (Planning, Nutrition, Analysis)
- HTMX + Alpine.js + Tailwind frontend (cookie auth, working forms)
- Alembic migrations configured with initial migration + exercise library migration
- Deployment configs (Dockerfile, fly.toml, docker-compose.yml)
- Test suite: 90 tests passing (auth, data, AI with mocks, exercises, cache, NL parser, analytics, coaching, export)
- Custom exception hierarchy and error handling
- Rate limiting on AI endpoints (slowapi)
- Input validation (Pydantic schemas with from_attributes)
- Ruff linting and formatting
- Static assets directory

**⚠️ Remaining:**
- Tailwind CDN (not compiled for production)
- Live deployment to Fly.io (configs exist, not yet deployed)
- End-to-end AI test with real API key (automated tests use mocks)

### **Phase 2 Progress: ~90% Complete**

**✅ Completed:**
- Logfire instrumentation (conditional on LOGFIRE_TOKEN, no-op in tests)
- Redis caching layer with graceful degradation (src/services/cache.py)
- Multi-model AI strategy — configurable model names via env vars:
  - Planning: Claude Opus 4.1 (default)
  - Analysis/Coaching: Claude Sonnet 4.5 (default)
  - Validation: Claude Haiku 4.5 (default)
  - Extraction: GPT-4o-mini (default)
  - Long-context: Gemini 2.5 Pro (default)
- Cache integration in AI service functions (workout plans, nutrition targets)
- Natural language parsing service (src/services/nl_parser.py) with two endpoints:
  - POST /api/ai/parse-workout
  - POST /api/ai/parse-meal
- Background scheduling with APScheduler 3.x (weekly analysis job, Monday 6 AM UTC)
- Cache invalidation on data writes (weight, meal, workout)
- Rate limiting uses Redis when REDIS_ENABLED=true, falls back to memory

**⚠️ Remaining:**
- Redis not yet provisioned in production (all cache code is no-op without it)
- Logfire token not configured (instrumentation is no-op without it)
- OpenAI/Google API keys needed for extraction and long-context agents

**📊 Metrics:**
- Test suite: 90 tests, all passing
- AI: Multi-model strategy configured (Opus, Sonnet, Haiku, GPT-4o-mini, Gemini 2.5 Pro)

### **Phase 3 Progress: ~95% Complete**

**✅ Completed:**
- Exercise library (800+ exercises from free-exercise-db)
  - Restructured Exercise model with full fields (force, mechanic, equipment, muscles, instructions, images)
  - UserExercisePreference model (favorite/exclude per user)
  - Import script for seeding database from free-exercise-db JSON
  - Browse/search/filter page with HTMX (name search, muscle/equipment/category/difficulty filters)
  - Exercise detail page (images, instructions, muscles, metadata)
  - User preference toggles (favorite, exclude)
  - "Exercises" nav link added
  - Alembic migration for schema changes
- Per-exercise set logging within workouts (weight x reps @RPE per set, multiple exercises per workout)
- Training preferences page (goal, split, days/week, session duration, volume target, cardio target)
- Data visualizations:
  - Weight trend chart (30 days, Chart.js line chart)
  - Workout activity chart (30 days, Chart.js bar chart)
  - Training volume over time (sets, reps, total weight)
  - Macro adherence stacked bar chart (protein, carbs, fat — 30 days)
  - Weekly targets radar chart (workouts, volume, duration vs targets)
- Muscle recovery tracking (72h full recovery model, 48h ready threshold, per-muscle status)
- Strength scores (Epley 1RM estimation, bodyweight-ratio strength levels)
- Weekly targets progress (workouts, sets, active minutes vs user preferences)
- Calendar view with workout badges (monthly grid, workout count, duration, exercise names per day)
- Dark theme (Tailwind dark: classes, localStorage toggle, all templates updated)
- Mobile optimization (bottom nav bar, touch targets 44px+, 16px mobile inputs, responsive layouts)
- Analytics API with 10 endpoints (recovery, strength, weekly, calendar, macros, volume, preferences GET/PUT, PRs, session PRs)
- Workout timer & rest period tracking (frontend-only Alpine.js component)
  - Stopwatch and rest countdown modes
  - Rest presets (1:00, 1:30, 2:00, 3:00)
  - AudioContext beep + navigator.vibrate on rest expiry
  - Auto-start rest on reps input change
  - Progress bar for rest countdown
- PR tracking & celebrations
  - Epley 1RM-based PR detection across all sessions (GET /api/analytics/prs)
  - Per-session PR check (GET /api/analytics/prs/session/{id})
  - Toast notifications on workout submit when PRs detected
  - PR badges on dashboard strength scores (last 30 days)
- Conversational AI coaching
  - PydanticAI coaching agent (uses coaching_model, Sonnet by default)
  - POST /api/ai/coach endpoint with rate limiting (20/hour)
  - Context injection: last 14 days workouts, 30 days weights, 7 days meals, profile
  - Chat UI template (coach.html) with Alpine.js component
  - "Coach" nav link in desktop and mobile nav
- Data export (CSV, JSON)
  - GET /api/export/json — structured JSON download with all data types
  - GET /api/export/csv — sectioned CSV with weight, meal, workout data
  - Configurable date range (1-365 days)
  - Export UI in preferences page with time range dropdown
- 90 tests (26 exercises + 27 analytics + 4 coaching + 5 export + 28 existing)

**⚠️ Remaining:**
- Video form guides (deferred)
- Correlation heatmaps (deferred)
- PWA / offline support (deferred)

---

### Phase 1: Foundation (Week 1-2) - **MVP**

**Goal**: Working app with manual data entry and basic AI

**Tasks**:
1. **Project setup** ✅
   - `uv init` with Python 3.13
   - FastAPI + dependencies in `pyproject.toml`
   - Docker configuration for Fly.io ✅
   - Environment management (.env.example) ✅

2. **Database** ✅
   - PostgreSQL schema implementation ✅
   - SQLModel models matching schema ✅
   - Alembic migrations setup ✅
   - Seed data (exercise library) ✅ (import script from free-exercise-db, 800+ exercises)

3. **Authentication** ✅
   - FastAPI-Users integration ✅
   - User registration/login forms ✅
   - JWT + cookie dual auth backends ✅
   - Protected routes ✅
   - Cookie auth for HTMX pages ✅ (localStorage bug fixed)

4. **Basic UI (HTMX + Tailwind)** ✅
   - Dashboard layout ✅
   - Weight logging form ✅
   - Meal logging form ✅
   - Workout logging form ✅
   - Data display with HTMX dynamic loading ✅

5. **First AI integration** ✅
   - PydanticAI agent setup ✅
   - "Generate workout plan" endpoint ✅
   - "Generate nutrition plan" endpoint ✅
   - Structured output validation ✅
   - Rate limiting (5/day per endpoint) ✅
   - Test suite with mocked agents ✅

6. **Deployment** ⚠️
   - Dockerfile ✅
   - fly.toml ✅
   - docker-compose.yml ✅
   - Postgres provisioning ❌
   - Initial deploy ❌

**Success Criteria**:
- Can register, login ✅
- Can log weight, meals, workouts ✅
- Can ask AI for workout plan ✅ (tested with mocks)
- Deployed and accessible from phone ❌

**Remaining Work for Phase 1 MVP:**
1. Compile Tailwind CSS (remove CDN)
2. Deploy to Fly.io (provision DB, set secrets, deploy)

---

### Phase 2: AI Agents (Week 3-4)

**Goal**: Automated analysis and adaptive planning

**Tasks**:
1. **PydanticAI integration** ✅
   - Agent definitions for Planning, Analysis, Long-Context ✅
   - Structured outputs with Pydantic models ✅
   - Multi-model strategy (Opus, Sonnet, Haiku, GPT-4o-mini, Gemini) ✅
   - Configurable model names via environment variables ✅

2. **Background scheduling** ✅
   - APScheduler 3.x AsyncIOScheduler ✅
   - Weekly analysis job (Monday 6 AM UTC) ✅
   - Results persisted to DB + Redis ✅
   - Skipped in test environment ✅

3. **AI caching layer** ✅
   - Redis client with graceful degradation ✅
   - Cache strategy for plans/analysis (7-day TTL) ✅
   - Cache invalidation on new data writes ✅
   - Rate limiter backed by Redis when available ✅

4. **Enhanced AI features** ✅
   - Natural language workout parsing (POST /api/ai/parse-workout) ✅
   - Natural language meal parsing (POST /api/ai/parse-meal) ✅
   - Conversational Q&A with context ✅ (implemented in Phase 3 — POST /api/ai/coach, chat UI)
   - Progress summaries via analysis agent ✅

5. **Observability** ✅
   - Pydantic Logfire integration (conditional on LOGFIRE_TOKEN) ✅
   - @logfire.instrument on all AI and cache service functions ✅
   - instrument_fastapi + instrument_pydantic_ai ✅
   - Cost tracking per user ❌ (needs Logfire token in production)

**Success Criteria**:
- AI automatically reviews progress weekly ✅
- Can log workouts via natural language ✅
- AI costs tracked in Logfire ⚠️ (instrumented, needs production token)

---

### Phase 3: UX Polish (Week 5-6)

**Goal**: Delightful user experience

**Tasks**:
1. **Data visualization** ✅
   - Chart.js integration ✅
   - Weight trend graphs ✅
   - Performance progression charts ✅ (training volume over time)
   - Macro adherence visualizations ✅ (stacked bar chart, 30 days)
   - Weekly targets radar chart ✅
   - Correlation heatmaps (AI-driven) ❌ (deferred)

2. **Mobile optimization** ✅
   - Touch-friendly forms ✅ (44px touch targets, 16px mobile font)
   - Responsive layouts ✅ (bottom nav, padding, grid adjustments)
   - Offline data entry (PWA features) ❌ (deferred)
   - Quick-entry shortcuts ❌ (deferred)

3. **Enhanced features**
   - Exercise library browser ✅ (800+ exercises, search/filter, detail pages, user preferences)
   - Per-exercise set logging ✅ (weight x reps @RPE, multiple exercises per workout)
   - Training preferences ✅ (goal, split, days/week, duration, volume, cardio targets)
   - Muscle recovery tracking ✅ (72h model, per-muscle status)
   - Strength scores ✅ (Epley 1RM, bodyweight-ratio levels)
   - Calendar view ✅ (monthly grid, workout badges, exercise names)
   - Video form guides ❌ (deferred)
   - Workout timer ✅ (stopwatch + rest countdown, beep alerts, auto-start)
   - Rest period tracking ✅ (presets 1:00/1:30/2:00/3:00, progress bar)
   - PR tracking and celebrations ✅ (Epley 1RM detection, toast notifications, dashboard badges)

4. **Personalization**
   - Dark mode ✅ (Tailwind dark: classes, localStorage toggle)
   - Custom dashboard widgets ❌ (deferred)
   - Notification preferences ❌ (deferred)
   - Export data (CSV, JSON) ✅ (JSON + CSV download, configurable date range, UI in preferences)

5. **Testing & refinement**
   - 90 tests passing ✅ (26 exercises + 27 analytics + 4 coaching + 5 export + 28 existing)
   - Prompt optimization based on feedback ❌ (deferred)
   - Performance optimization ❌ (deferred)

**Success Criteria**:
- Mobile experience feels native
- Logging takes < 30 seconds per session
- Visualizations provide insights
- Users report high satisfaction

---

### Phase 4: Advanced AI (Week 7+) - **Optional**

**Goal**: Cutting-edge AI capabilities

**Tasks**:
1. **RAG implementation**
   - Vector database (pgvector or Pinecone)
   - Exercise science paper ingestion
   - Semantic search
   - Grounded responses with citations

2. **Multi-modal AI**
   - **GPT-5** or **Gemini 2.5 Pro** for meal photo analysis (native multimodal)
   - Form check via video upload using Gemini's video understanding
   - Progress photos comparison with visual reasoning

3. **Advanced analytics**
   - Predictive modeling (when will I hit goal?)
   - Anomaly detection (injury risk, overtraining)
   - Personalized exercise recommendations
   - Social comparison (anonymized)

4. **Integrations**
   - Apple Health import (iOS Shortcuts)
   - MyFitnessPal integration
   - Wearable data (Whoop, Oura)
   - Calendar sync for scheduling

**Success Criteria**:
- AI provides research-backed explanations
- Photo-based meal logging works
- Predictive insights are accurate

---

## Security & Privacy Considerations

### Data Protection

1. **Health data is sensitive**
   - Encrypt at rest (Postgres TDE)
   - Encrypt in transit (HTTPS only)
   - Regular backups with encryption
   - Data retention policy (7 years or user deletion)

2. **API key management**
   - Never commit secrets
   - Use Fly.io secrets management
   - Rotate keys quarterly
   - Rate limiting on AI endpoints

3. **User privacy**
   - Data export capability (GDPR compliance)
   - Account deletion removes all data
   - No data sharing with third parties
   - Transparent AI usage disclosure

4. **Authentication hardening**
   - Password requirements (min 12 chars)
   - Optional 2FA (TOTP)
   - Session timeout (7 days)
   - Login attempt limiting

### HIPAA Considerations

**Note**: This app is for personal use (2-3 users), not a covered entity. However, health data best practices apply:

- **Access control**: Only user can see their data
- **Audit logs**: Track data access/modifications
- **Secure disposal**: Proper data deletion on account removal
- **Business associate agreements**: If using cloud providers, review BAAs

---

## Development Workflow

### Local Development Setup

```bash
# Clone and setup
git clone <repo>
cd fit-agent
uv sync

# Database
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16
uv run alembic upgrade head

# Redis (optional for Phase 2+)
docker run -d -p 6379:6379 redis:7-alpine

# Environment
cp .env.example .env
# Edit .env with API keys

# Run
uv run uvicorn src.main:app --reload
```

### Environment Variables

```bash
# .env.example
DATABASE_URL=postgresql://user:pass@localhost/fitgent
REDIS_URL=redis://localhost:6379
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# AI providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Observability
LOGFIRE_TOKEN=...

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

### Testing Strategy

1. **Unit tests**
   - SQLModel model validation
   - Business logic functions
   - Prompt template rendering

2. **Integration tests**
   - API endpoint testing (FastAPI TestClient)
   - Database operations
   - Auth flows

3. **AI testing**
   - Mock AI responses in tests (don't burn credits)
   - Snapshot testing for prompt consistency
   - Manual validation of AI outputs

4. **E2E tests** (optional)
   - Playwright for critical user flows
   - Automated on deploy

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=src
```

### Git Workflow

```bash
# Feature branches
git checkout -b feature/workout-logging

# Commits
git commit -m "Add workout session logging endpoint"

# Deploy triggers on main
git push origin main  # Auto-deploys to Fly.io
```

---

## Deployment Guide

### Fly.io Setup

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize app
fly launch
# Choose app name: fit-agent
# Choose region: nearest to you
# PostgreSQL: Yes (shared-cpu-1x, 256MB)
# Redis: No initially (add in Phase 2)

# Set secrets
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set SECRET_KEY=$(openssl rand -hex 32)

# Deploy
fly deploy

# Check status
fly status
fly logs
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy app
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Run migrations and start app
CMD uv run alembic upgrade head && \
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### fly.toml

```toml
app = "fit-agent"
primary_region = "sea"

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0 # Scale to zero when idle

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

---

## Monitoring & Observability

### Key Metrics to Track

1. **AI Usage**
   - Cost per user per week
   - Token usage by endpoint
   - Response latency (p50, p95, p99)
   - Error rates

2. **Application Performance**
   - API response times
   - Database query performance
   - Background job completion time
   - Cache hit rates

3. **User Engagement**
   - Daily active users
   - Logging frequency (workouts, meals, weight)
   - AI chat interactions
   - Feature usage

### Pydantic Logfire Setup

```python
import logfire

logfire.configure()

# Instrument FastAPI
app = FastAPI()
logfire.instrument_fastapi(app)

# Track AI costs
@logfire.span("ai_plan_generation")
async def generate_plan(user_id: int):
    result = await planning_agent.run(user_id)
    logfire.info(
        "plan_generated",
        user_id=user_id,
        tokens=result.usage.total_tokens,
        cost_usd=result.usage.total_tokens * 0.00003  # Example rate
    )
    return result
```

### Alerting

- Email alert if AI cost > $50/day
- Slack webhook for errors
- Weekly usage report

---

## Future Enhancements

### Potential Features (Post-MVP)

1. **Social Features**
   - Share workouts with training partner
   - Compare progress (anonymized)
   - Public workout templates

2. **Advanced Integrations**
   - Strava for cardio
   - Strong app import
   - Calendar sync
   - Zapier webhooks

3. **AI Improvements**
   - Voice interaction (Whisper API)
   - Real-time form feedback (video analysis)
   - Genetic algorithm for program optimization
   - Multi-agent debate for plan decisions

4. **Mobile Apps**
   - React Native or Flutter
   - Native push notifications
   - Offline-first architecture
   - Watch app for workout logging

5. **Marketplace**
   - Share/sell workout programs
   - Coach dashboard (multi-client management)
   - Subscription tiers

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI costs spiral | Medium | High | Rate limiting, caching, cost alerts |
| Fly.io downtime | Low | Medium | Multi-region deployment, backups |
| Poor AI output quality | Medium | High | Prompt engineering, human review, feedback loops |
| Data loss | Low | Critical | Daily backups, point-in-time recovery |
| Security breach | Low | Critical | Encryption, audits, minimal data collection |

### Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI advice is harmful | Low | Critical | Disclaimers, conservative recommendations, medical review |
| Users don't trust AI | Medium | High | Transparency, explain reasoning, human override |
| Feature creep | High | Medium | Stick to roadmap, prioritize ruthlessly |
| Maintenance burden | Medium | Medium | Automated testing, good docs, simple architecture |

---

## Success Metrics

### MVP Success (End of Phase 1)
- ✅ Both users can log workouts, meals, weight daily
- ✅ AI generates initial workout plan (tested with mocks, needs real API key verification)
- ❌ App accessible from phone (not yet deployed)
- N/A Zero downtime over 1 week (not deployed yet)

### Long-term Success (6 months)
- ✅ Both users log ≥4 workouts/week
- ✅ Measurable progress toward goals
- ✅ AI plan adjustments are helpful (user survey)
- ✅ AI costs < $20/user/month
- ✅ Zero critical bugs

### Stretch Goals (1 year)
- ✅ 10+ active users (friends/beta testers)
- ✅ Mobile app launched
- ✅ Advanced AI features (RAG, vision)
- ✅ Profitability (subscription revenue > costs)

---

## Questions & Decisions

### Open Questions
1. **Macro tracking**: Full nutritional database or simple manual entry?
2. **Exercise library**: Pre-seed with how many exercises? (500+?)
3. **AI model selection**: Start with Claude only or multi-model from day 1?
4. **Email notifications**: Priority feature or Phase 3?
5. **Data export**: What formats? (CSV, JSON, PDF report?)

### Decisions Made
- ✅ Python + FastAPI (leverages your strengths)
- ✅ Simple web app first (mobile app later)
- ✅ Fly.io for hosting (free tier)
- ✅ PostgreSQL from day 1 (no migration pain)
- ✅ PydanticAI for agent orchestration
- ✅ HTMX for frontend (avoid JS complexity)

---

## Getting Started

### Next Steps
1. Review this plan and adjust based on your preferences
2. Decide on MVP scope (all of Phase 1 or subset?)
3. Set up development environment
4. Implement Phase 1, Task 1: Project setup
5. Daily standups to track progress

### Estimated Timeline
- **Phase 1 (MVP)**: 2 weeks
- **Phase 2 (AI Agents)**: 2 weeks
- **Phase 3 (Polish)**: 2 weeks
- **Total to production-ready**: 6 weeks

### Resource Requirements
- **Time**: ~10-15 hours/week from each person
- **Cost**: $10-20/month (AI APIs)
- **Tools**: GitHub, Fly.io account, Anthropic API key

---

## Technical Debt & Known Issues (2026-03-02)

### ✅ Resolved (previously critical)

1. ~~**HTMX Authorization Header Bug**~~ **FIXED**
   - Switched from localStorage JWT to cookie-based auth
   - Removed broken localStorage redirect scripts from dashboard, workouts, nutrition templates
   - Server-side auth in `pages.py` handles redirects

2. ~~**No Database Migrations**~~ **FIXED**
   - Alembic configured with initial migration

3. ~~**AI Integration Untested**~~ **FIXED**
   - 4 AI tests with mocked agents (no API credits burned)
   - Fixed slowapi + Pydantic model incompatibility (return JSONResponse)

4. ~~**No Error Handling**~~ **FIXED**
   - Custom exception hierarchy (`src/exceptions.py`)
   - Global exception handlers in `main.py`

5. ~~**No Test Suite**~~ **FIXED**
   - 19 tests across auth, data, and AI endpoints

6. ~~**Missing Static Assets Directory**~~ **FIXED**
   - `src/static/` directory created with `.gitkeep`

7. ~~**No Deployment Configuration**~~ **FIXED**
   - Dockerfile, fly.toml, docker-compose.yml exist

### ⚠️ Remaining Issues

8. **Tailwind CDN in Production**
   - Using `<script src="https://cdn.tailwindcss.com"></script>`
   - Console warning: "should not be used in production"
   - Fix: Use Tailwind CLI to compile CSS

9. **Only Sonnet 4.5 Integrated**
   - Multi-model strategy now implemented ✅
   - Models configurable via env vars (PLANNING_MODEL, ANALYSIS_MODEL, etc.)

10. **Hardcoded Dates in Forms**
    - JavaScript sets `value = new Date().toISOString()` client-side
    - Better to default on server-side for timezone accuracy

### 🔮 Future Considerations (Phase 3+)

11. **Redis Not Yet Provisioned**
    - Cache code handles Redis being down gracefully
    - Need to provision Redis in production and set REDIS_ENABLED=true

12. **Logfire Not Yet Configured**
    - All instrumentation in place but needs LOGFIRE_TOKEN in production
    - Cost tracking per user requires production setup

13. **Conversational Q&A**
    - Chat-style coaching with full user context
    - Deferred to Phase 3

---

## Immediate Next Steps (Priority Order)

### To finish Phase 1:
1. **Compile Tailwind CSS** (1 hour)
   - Install Tailwind CLI
   - Build production CSS
   - Remove CDN script tag

2. **Deploy to Fly.io** (2-3 hours)
   - Provision Postgres on Fly.io
   - Set environment secrets (ANTHROPIC_API_KEY, SECRET_KEY, DATABASE_URL)
   - Deploy and smoke test

3. **Manual AI verification** (30 min)
   - Test `/api/ai/generate-workout-plan` with real API key
   - Test `/api/ai/generate-nutrition-plan` with real API key

### Phase 2 complete. Phase 3 priorities:
4. ~~Chart.js visualizations~~ ✅ Done (weight trend, workout activity, volume, macros, radar)
5. ~~Exercise library browser~~ ✅ Done
6. ~~Per-exercise set logging~~ ✅ Done
7. ~~Training preferences~~ ✅ Done
8. ~~Muscle recovery tracking~~ ✅ Done
9. ~~Strength scores~~ ✅ Done
10. ~~Weekly targets~~ ✅ Done
11. ~~Calendar view~~ ✅ Done
12. ~~Dark theme~~ ✅ Done
13. ~~Mobile optimization~~ ✅ Done
14. ~~Conversational Q&A coaching~~ ✅ Done (POST /api/ai/coach, chat UI, context injection)
15. ~~Workout timer and PR tracking~~ ✅ Done (timer, rest presets, PR detection, toast celebrations)
16. ~~Data export~~ ✅ Done (JSON + CSV, preferences UI)

---

## Conclusion

This plan balances rapid development with cutting-edge AI capabilities. By starting with a simple MVP and iterating based on real usage, you'll build a fitness tracking app that provides value from day 1 while leaving room for sophisticated AI features.

**Current Status**: Phase 1 ~95% complete, Phase 2 ~90% complete, Phase 3 ~95% complete. Multi-model AI, caching, scheduling, NL parsing, observability, exercise library (800+ exercises), per-exercise set logging, training preferences, muscle recovery, strength scores, weekly targets, calendar view, dark theme, mobile optimization, workout timer with rest tracking, PR detection with celebrations, conversational AI coaching, and data export (JSON/CSV) are all implemented. 90 tests passing. Remaining work: production provisioning (Redis, Logfire token, deploy), video form guides, PWA/offline support.

The key differentiator is the AI-powered long-term planning and adaptation - something marketplace apps can't offer with the latest models. Focus on making the AI coaching genuinely helpful, and the rest will follow.

**Let's build something great! 🏋️‍♂️🤖**
