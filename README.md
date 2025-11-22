# Fit Agent - AI-Powered Fitness Tracking

An intelligent fitness tracking web application that leverages cutting-edge AI models to provide personalized workout planning, nutrition guidance, and adaptive coaching.

## Project Status

**Phase 1 (MVP): 70% Complete** - Core infrastructure built, critical bugs blocking completion

See [implementation_status.md](implementation_status.md) for detailed status and next steps.

## Features

### Implemented ✅

- **User Authentication**: Secure registration and login with FastAPI-Users
- **Type-Safe Database**: PostgreSQL with SQLModel ORM for full type safety
- **Database Migrations**: Alembic with initial schema migration
- **Modern UI**: Clean, responsive interface built with HTMX, Alpine.js, and Tailwind CSS
- **AI Integration Framework**: PydanticAI agents configured with Claude Sonnet 4.5
- **API Endpoints**: Full REST API for data logging and AI features
- **Deployment Configuration**: Dockerfile and fly.toml ready

### In Progress ⚠️

- **Data Logging**: API endpoints functional but HTMX auth bug blocks UI (401 errors)
- **AI Features**: Agents implemented but untested end-to-end
- **Frontend Data Display**: History sections show placeholders, not fetching real data

### Known Issues 🚨

1. **HTMX Authorization Bug** (BLOCKER) - JWT tokens not sent with HTMX requests → 401 on all data logging
2. **AI Endpoints Untested** - Never tested with real API calls
3. **Tailwind CDN** - Using CDN in development, needs production build
4. **No Test Suite** - Zero tests written

### Future Features 🚀

**Workout Calendar Visualization**
- Interactive calendar with color-coded days indicating workout completion
- Hover/click to view workout duration and summary
- Fun volume comparison feature: total weight lifted converted to random object equivalents
  - Examples: "You lifted 50 refrigerators today!" or "That's 2.5 pickup trucks!"
  - Randomized objects from a large pool (never repeats)
  - Shareable workout achievements

**Workout Plan Database**
- Pre-built library of proven workout programs from trusted sources
- Curated plans from:
  - [LiftVault.com](https://liftvault.com) - comprehensive collection of strength programs
  - nSuns LP, 5/3/1 variations, GZCL programs
  - Reddit PPL, Starting Strength, StrongLifts 5x5
  - Bodybuilding.com program database
  - Renaissance Periodization templates
- Program features:
  - Full exercise breakdowns with sets/reps/intensity
  - Progression schemes and deload protocols
  - Equipment variations (barbell/dumbbell/bodyweight)
  - Experience level filtering (beginner/intermediate/advanced)
  - Goal-based selection (strength/hypertrophy/powerlifting)
- One-click program import with AI-powered customization to user's:
  - Available equipment
  - Training frequency
  - Experience level
  - Specific goals and injuries
- Program tracking with built-in periodization and auto-regulation

**AI-Powered Body Measurements**
- See [body-measurement-feature-plan.md](body-measurement-feature-plan.md) for detailed plan on AI-powered body measurement analysis (mobile feature using pose estimation and depth sensing)

## Tech Stack

- **Backend**: FastAPI (async Python)
- **Database**: PostgreSQL with SQLModel ORM
- **AI**: PydanticAI with Claude Sonnet 4.5
- **Frontend**: HTMX + Alpine.js + Tailwind CSS
- **Auth**: FastAPI-Users (JWT)
- **Migrations**: Alembic
- **Observability**: Pydantic Logfire (ready for Phase 2)

## Quick Start

### Prerequisites

- Python 3.13+
- Docker and Docker Compose (recommended)
- Anthropic API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd fit-agent
   ```

2. **Install dependencies with `uv`:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   # DATABASE_URL will be: postgresql+asyncpg://fituser:dev@localhost:5432/fitgent
   ```

4. **Start database services with Docker Compose:**
   ```bash
   docker-compose up -d
   ```
   This starts PostgreSQL and Redis. See the [Docker Compose](#docker-compose-setup) section below for details.

5. **Run database migrations:**
   ```bash
   uv run alembic upgrade head
   ```

6. **Start the application:**
   ```bash
   uv run uvicorn src.main:app --reload
   ```

7. **Open your browser** to http://localhost:8000

### Alternative: Manual PostgreSQL Setup

If you prefer not to use Docker Compose, you can run PostgreSQL manually:

```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=fituser \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=fitgent \
  --name fitgent-db \
  postgres:16-alpine
```

## Docker Compose Setup

The project includes a `docker-compose.yml` file that simplifies local development by managing all required services.

### What's Included

**PostgreSQL (db service)**
- **Purpose**: Primary database for storing all application data
- **Image**: `postgres:16-alpine` (lightweight PostgreSQL 16)
- **Port**: 5432 (accessible from host machine)
- **Credentials**:
  - User: `fituser`
  - Password: `dev` (development only!)
  - Database: `fitgent`
- **Data Persistence**: Uses named volume `postgres_data` so your data survives container restarts
- **Health Check**: Ensures database is ready before dependent services start

**Redis (redis service)**
- **Purpose**: Caching layer for AI-generated plans and analysis results (Phase 2+)
- **Image**: `redis:7-alpine` (lightweight Redis 7)
- **Port**: 6379 (accessible from host machine)
- **Data Persistence**: Uses named volume `redis_data` with AOF (Append-Only File) enabled
- **Current Status**: Not actively used in Phase 1 MVP, but ready for Phase 2 caching implementation

**Optional App Service (commented out)**
- The compose file includes a commented-out `app` service for running the FastAPI application in Docker
- By default, run the app locally with `uv run uvicorn` for faster development (hot-reloading)
- Uncomment if you prefer a fully containerized environment

### Common Commands

```bash
# Start all services in background
docker-compose up -d

# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f db

# Stop all services (keeps data)
docker-compose down

# Stop and remove all data (⚠️ WARNING: deletes everything)
docker-compose down -v

# Restart a specific service
docker-compose restart db

# Check service status
docker-compose ps

# Execute command in running container
docker-compose exec db psql -U fituser -d fitgent
```

### Database Connection Strings

When services are running, use these connection strings:

**From host machine (running app with `uv run`):**
```bash
DATABASE_URL=postgresql+asyncpg://fituser:dev@localhost:5432/fitgent
REDIS_URL=redis://localhost:6379/0
```

**From within Docker (if using app service):**
```bash
DATABASE_URL=postgresql+asyncpg://fituser:dev@db:5432/fitgent
REDIS_URL=redis://redis:6379/0
```

### Troubleshooting

**Port already in use:**
```bash
# Check what's using port 5432
sudo lsof -i :5432

# Stop existing PostgreSQL
sudo systemctl stop postgresql
```

**Permission denied errors:**
```bash
# Reset volume permissions
docker-compose down -v
docker volume prune
docker-compose up -d
```

**Database connection refused:**
```bash
# Wait for health check to pass
docker-compose ps

# Should show "healthy" status for db service
```

## Project Structure

```
fit-agent/
├── src/
│   ├── api/           # API routes
│   │   ├── auth.py    # Authentication endpoints
│   │   ├── data.py    # Data logging endpoints
│   │   ├── ai.py      # AI-powered endpoints
│   │   └── pages.py   # HTML page routes
│   ├── models/        # SQLModel database models
│   │   ├── user.py    # User and profile models
│   │   ├── workout.py # Workout-related models
│   │   ├── nutrition.py # Nutrition and weight models
│   │   └── ai.py      # AI cache and jobs
│   ├── services/      # Business logic
│   │   └── ai.py      # PydanticAI agents
│   ├── templates/     # HTML templates
│   ├── static/        # Static assets
│   ├── config.py      # Configuration
│   ├── database.py    # Database connection
│   ├── auth.py        # Authentication setup
│   ├── schemas.py     # Pydantic schemas
│   └── main.py        # FastAPI application
├── alembic/           # Database migrations
│   └── versions/      # Migration scripts
├── tests/             # Tests (to be added)
├── Dockerfile         # Container definition
├── docker-compose.yml # Local development services
├── fly.toml           # Fly.io deployment config
└── pyproject.toml     # Project dependencies
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/jwt/login` - Login (returns JWT)
- `POST /auth/jwt/logout` - Logout
- `GET /auth/users/me` - Get current user

### Data Logging
- `POST /api/weight` - Log weight and measurements
- `GET /api/weight` - Get weight history
- `POST /api/meals` - Log meal
- `GET /api/meals` - Get meal history
- `POST /api/workouts` - Log workout session
- `GET /api/workouts` - Get workout history

### AI Features
- `POST /api/ai/generate-workout-plan` - Generate personalized workout plan
- `POST /api/ai/generate-nutrition-plan` - Generate nutrition targets

## Development

### Running Tests
```bash
uv run pytest
```

### Creating Database Migrations
```bash
# Generate migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Code Formatting
```bash
uv run ruff format src/
```

## Deployment

### Fly.io Deployment

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly:**
   ```bash
   fly auth login
   ```

3. **Create app and provision PostgreSQL:**
   ```bash
   fly launch
   # Follow prompts to create app and database
   ```

4. **Set secrets:**
   ```bash
   fly secrets set ANTHROPIC_API_KEY=sk-ant-...
   fly secrets set SECRET_KEY=$(openssl rand -hex 32)
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

## Environment Variables

See `.env.example` for all configuration options.

### Key Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `SECRET_KEY` | Secret key for JWT tokens (generate with `openssl rand -hex 32`) | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | ✅ Yes |
| `REDIS_URL` | Redis connection string | Phase 2+ |
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Phase 2+ |
| `GOOGLE_API_KEY` | Google API key for Gemini models | Phase 2+ |
| `LOGFIRE_TOKEN` | Pydantic Logfire observability token | Phase 2+ |

### Example .env File

```bash
# Core required variables for Phase 1
DATABASE_URL=postgresql+asyncpg://fituser:dev@localhost:5432/fitgent
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional Phase 2+ variables
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
LOGFIRE_TOKEN=...
```

## Current Development Focus

### Week 1: Fix Blockers (8-10 hours)

1. **Debug HTMX Auth Bug** (2-3 hours)
   - Fix JavaScript in `base.html`
   - Test weight/meal/workout logging
   - Verify 200 responses and data persists

2. **Test AI Endpoints** (1-2 hours)
   - Call `/api/ai/generate-workout-plan` manually
   - Verify structured output works
   - Document API usage

3. **Add Basic Error Handling** (2-3 hours)
   - Wrap routes in try/except
   - Return user-friendly messages
   - Show success/error in UI

### Week 2: Polish MVP (8-11 hours)

4. **Fetch and Display Real Data** (3-4 hours)
   - Load recent activity on dashboard
   - Show workout/meal history on respective pages
   - Replace placeholder text

5. **Add Pytest Suite** (2-3 hours)
   - Test auth flow
   - Mock AI responses
   - Test data logging endpoints

6. **Compile Tailwind CSS** (1 hour)
   - Remove CDN script
   - Build production CSS

7. **Deploy to Fly.io** (2-3 hours)
   - Test deployment configuration
   - Provision database
   - Deploy and test

## Roadmap

### Phase 2: AI Agents (Next)
- Multi-model AI strategy (Claude Opus, GPT-5-mini, Gemini)
- Background scheduling for weekly analysis
- Redis caching layer
- Natural language logging
- Enhanced observability with Logfire

### Phase 3: UX Polish
- Data visualizations (Chart.js)
- Mobile optimization
- Exercise library
- Workout timer
- PR tracking

### Phase 4: Advanced AI
- RAG with exercise science papers
- Multi-modal (photo/video analysis)
- Predictive modeling
- External integrations

## Contributing

This is a personal project for 2-3 users. Contributions are not currently being accepted.

## License

Private - All Rights Reserved
