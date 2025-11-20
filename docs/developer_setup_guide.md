# Developer Setup & MVP Completion Guide

## Overview

This guide walks you through setting up the Fit Agent development environment and completing the critical blockers to reach MVP deployment.

---

## Part 1: Initial Setup

### Prerequisites

Install these on your machine:

- Python 3.13+
- PostgreSQL 16+ (or Docker)
- Git
- `uv` package manager

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Clone Repository

```bash
git clone <repo-url>
cd fit-AI
```

### Install Dependencies

```bash
# Install all Python dependencies
uv sync

# Verify installation
uv run python --version  # Should show Python 3.13+
```

### Start PostgreSQL

**Option 1: Docker (Recommended)**

```bash
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=fitgent \
  --name fitgent-db \
  postgres:16

# Verify it's running
docker ps | grep fitgent-db
```

**Option 2: Local PostgreSQL**

```bash
# macOS with Homebrew
brew install postgresql@16
brew services start postgresql@16

# Create database
createdb fitgent
```

### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Required values:
# - DATABASE_URL (default should work with Docker setup)
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)
```

Example `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/fitgent
SECRET_KEY=<run: openssl rand -hex 32>
ANTHROPIC_API_KEY=sk-ant-api03-...
DEBUG=true
ENVIRONMENT=development
```

### Verify Setup

```bash
# Start the application
uv run uvicorn src.main:app --reload

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy","environment":"development"}
```

Open browser to http://localhost:8000 - you should see the landing page.

---

## Part 2: Fix Critical Blockers

### Blocker 1: Fix HTMX Authorization Bug

**Problem**: HTMX requests don't include JWT token, causing 401 errors on all data logging.

**Location**: `src/templates/base.html:12-18`

**Steps to Fix**:

1. Open `src/templates/base.html`

2. Find the JavaScript block that adds Authorization header

3. Current broken code looks like:
```javascript
<script>
document.addEventListener('htmx:configRequest', (event) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        event.detail.headers['Authorization'] = `Bearer ${token}`;
    }
});
</script>
```

4. **Diagnose the issue**:
   - Open browser DevTools (F12)
   - Go to http://localhost:8000/dashboard
   - Check Console for JavaScript errors
   - Check Network tab when submitting weight/meal/workout form
   - Look for missing Authorization header

5. **Common fixes**:

   **If script runs before DOM loads**:
   ```javascript
   <script>
   document.addEventListener('DOMContentLoaded', () => {
       document.addEventListener('htmx:configRequest', (event) => {
           const token = localStorage.getItem('access_token');
           if (token) {
               event.detail.headers['Authorization'] = `Bearer ${token}`;
           }
       });
   });
   </script>
   ```

   **If token not stored after login**:
   - Check `src/templates/login.html` for login success handler
   - Ensure it saves token: `localStorage.setItem('access_token', response.access_token)`

   **If HTMX loads before script**:
   - Move script to `<head>` or before HTMX loads

6. **Test the fix**:
```bash
# Register new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123"}'

# Login
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"

# Copy access_token from response

# Test weight logging with token
curl -X POST http://localhost:8000/api/weight \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-11-19","weight_lbs":180.5}'

# Expected: 200 OK with created weight log
```

7. **Test in browser**:
   - Register at http://localhost:8000/register
   - Login at http://localhost:8000/login
   - Go to http://localhost:8000/dashboard
   - Open DevTools Network tab
   - Submit weight form
   - Verify request has `Authorization: Bearer ...` header
   - Verify response is 200 (not 401)

8. **Commit the fix**:
```bash
git add src/templates/base.html
git commit -m "Fix HTMX Authorization header bug

- Move event listener inside DOMContentLoaded
- Fixes 401 errors on data logging endpoints
- Verified weight/meal/workout logging works"
```

---

### Blocker 2: Set Up Alembic Migrations

**Problem**: Currently using auto-create tables in dev mode. Won't work in production.

**Steps**:

1. **Initialize Alembic**:
```bash
uv run alembic init alembic
```

This creates:
- `alembic/` directory with migrations
- `alembic.ini` configuration file

2. **Configure Alembic**:

Edit `alembic/env.py`:

```python
# Find the line that sets target_metadata
# Replace it with:

from src.database import Base
from src.models.user import User, UserProfile, Goal
from src.models.workout import WorkoutPlan, WorkoutSession, ExerciseLog, Exercise
from src.models.nutrition import WeightLog, MealLog, NutritionTarget
from src.models.ai import AIAnalysisCache, ScheduledJob

target_metadata = Base.metadata
```

Edit `alembic.ini`:

```ini
# Find sqlalchemy.url line, replace with:
sqlalchemy.url = postgresql+asyncpg://postgres:dev@localhost:5432/fitgent

# Or use environment variable:
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

**Better approach - Use environment variable**:

Edit `alembic/env.py` to read from config:

```python
from src.config import settings

# In run_migrations_offline() and run_migrations_online()
# Replace hardcoded URL with:
config.set_main_option("sqlalchemy.url", settings.database_url)
```

3. **Create initial migration**:

```bash
# Drop existing tables (development only!)
# Connect to PostgreSQL
psql -d fitgent -U postgres -h localhost

# In psql:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q

# Generate initial migration
uv run alembic revision --autogenerate -m "Initial schema: users, workouts, nutrition, AI cache"
```

This creates a file like `alembic/versions/abc123_initial_schema.py`

4. **Review the migration**:

Open the generated migration file in `alembic/versions/`

Check:
- All tables are created (users, user_profiles, goals, workout_plans, etc.)
- Indexes are added
- Foreign keys are correct
- No unexpected drops or modifications

5. **Run the migration**:

```bash
uv run alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema
```

6. **Verify tables exist**:

```bash
psql -d fitgent -U postgres -h localhost -c "\dt"
```

Should show all tables: users, user_profiles, goals, workout_plans, etc.

7. **Test rollback**:

```bash
# Rollback migration
uv run alembic downgrade -1

# Verify tables are gone
psql -d fitgent -U postgres -h localhost -c "\dt"

# Re-apply migration
uv run alembic upgrade head

# Verify tables are back
psql -d fitgent -U postgres -h localhost -c "\dt"
```

8. **Update startup code**:

Edit `src/main.py`:

Remove or comment out the auto-create code:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup: Create database tables (development only)
    # REMOVED: Now using Alembic migrations
    # if settings.debug:
    #     await create_db_and_tables()
    yield
    # Shutdown: Cleanup if needed
```

9. **Test the application**:

```bash
# Restart the app
uv run uvicorn src.main:app --reload

# Register and test (app should work same as before)
```

10. **Commit migrations**:

```bash
git add alembic/ alembic.ini src/main.py
git commit -m "Set up Alembic migrations

- Initialize Alembic with async PostgreSQL
- Create initial migration for all tables
- Remove auto-create tables from startup
- Migrations tested: upgrade and downgrade work"
```

---

### Blocker 3: Test AI Endpoints End-to-End

**Problem**: AI integration code exists but never tested with real API.

**Steps**:

1. **Verify API key is set**:

```bash
# Check .env has ANTHROPIC_API_KEY
grep ANTHROPIC_API_KEY .env

# Should show: ANTHROPIC_API_KEY=sk-ant-api03-...
# If not, add it now
```

2. **Test workout plan generation**:

Create test file `tests/manual/test_ai_real.py`:

```python
"""Manual tests for AI endpoints with real API calls

Run with: uv run python tests/manual/test_ai_real.py

WARNING: Uses real API credits. Run sparingly.
"""

import asyncio
from src.services.ai import generate_workout_plan, generate_nutrition_targets


async def test_workout_plan():
    """Test workout plan generation"""
    print("\n=== Testing Workout Plan Generation ===")

    result = await generate_workout_plan(
        user_goals="Build muscle and strength",
        experience_level="intermediate",
        equipment_access=["barbell", "squat rack", "dumbbells", "bench"],
        time_availability=240,  # 4 hours per week
        age=30,
        injuries=None
    )

    print(f"✓ Plan generated successfully")
    print(f"  Duration: {result.weeks} weeks")
    print(f"  Frequency: {result.frequency}x/week")
    print(f"  Exercises: {', '.join(result.exercises[:5])}...")
    print(f"  Rationale: {result.rationale[:150]}...")

    return result


async def test_nutrition_plan():
    """Test nutrition plan generation"""
    print("\n=== Testing Nutrition Plan Generation ===")

    result = await generate_nutrition_targets(
        user_goals="Build muscle",
        weight_lbs=180.0,
        activity_level="moderate",
        dietary_preferences="No restrictions"
    )

    print(f"✓ Nutrition plan generated successfully")
    print(f"  Daily calories: {result.daily_calories}")
    print(f"  Protein: {result.daily_protein_g}g")
    print(f"  Carbs: {result.daily_carbs_g}g")
    print(f"  Fats: {result.daily_fat_g}g")
    print(f"  Meal suggestions: {len(result.meal_suggestions)} provided")

    return result


async def main():
    """Run all AI tests"""
    print("Starting AI endpoint tests...")
    print("WARNING: This uses real API credits\n")

    try:
        workout_result = await test_workout_plan()
        nutrition_result = await test_nutrition_plan()

        print("\n=== All Tests Passed ===")
        print(f"✓ Workout plan: {workout_result.weeks} week program")
        print(f"✓ Nutrition: {nutrition_result.daily_calories} cal target")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

3. **Run the test**:

```bash
mkdir -p tests/manual
# Copy the test file above to tests/manual/test_ai_real.py

uv run python tests/manual/test_ai_real.py
```

Expected output:
```
Starting AI endpoint tests...
WARNING: This uses real API credits

=== Testing Workout Plan Generation ===
✓ Plan generated successfully
  Duration: 8 weeks
  Frequency: 4x/week
  Exercises: Squat, Bench Press, Deadlift, Overhead Press...
  Rationale: Based on your intermediate experience and muscle-building goals...

=== Testing Nutrition Plan Generation ===
✓ Nutrition plan generated successfully
  Daily calories: 2600
  Protein: 180g
  Carbs: 280g
  Fats: 70g
  Meal suggestions: 5 provided

=== All Tests Passed ===
✓ Workout plan: 8 week program
✓ Nutrition: 2600 cal target
```

4. **Test via HTTP endpoint**:

```bash
# Start server
uv run uvicorn src.main:app --reload

# In another terminal, call AI endpoint
curl -X POST http://localhost:8000/api/ai/generate-workout-plan \
  -H "Content-Type: application/json" \
  -d '{
    "user_goals": "Build strength",
    "experience_level": "beginner",
    "equipment_access": ["barbell", "bench"],
    "time_availability": 180,
    "age": 25
  }'
```

Expected: JSON response with workout plan

5. **Document costs**:

Check Anthropic dashboard for token usage:
- Login to https://console.anthropic.com/
- Check usage for today
- Document cost (should be ~$0.10-0.30 for both tests)

6. **Commit test**:

```bash
git add tests/manual/test_ai_real.py
git commit -m "Add manual AI endpoint tests

- Test workout plan generation with Claude Sonnet 4.5
- Test nutrition plan generation
- Verified structured outputs work correctly
- Cost: ~\$0.20 for both tests"
```

---

### Blocker 4: Add Basic Error Handling

**Problem**: API errors return raw 500s to users.

**Steps**:

1. **Create error schemas**:

File already exists: `src/schemas/error.py`

Review it:
```python
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_type: str | None = None
```

2. **Add exception handler**:

Edit `src/main.py`:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic_ai.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data",
            "errors": exc.errors()
        }
    )


@app.exception_handler(UserError)
async def ai_error_handler(request: Request, exc: UserError):
    """Handle AI agent errors"""
    logger.error(f"AI agent error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "AI service temporarily unavailable",
            "error_type": "ai_error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error_type": type(exc).__name__
        }
    )
```

3. **Add try-except to data endpoints**:

Edit `src/api/data.py`:

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


@router.post("/weight", response_model=WeightLogRead)
async def log_weight(
    weight_data: WeightLogCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Log body weight and measurements"""
    try:
        weight_log = WeightLog(**weight_data.model_dump(), user_id=user.id)
        session.add(weight_log)
        await session.commit()
        await session.refresh(weight_log)
        return weight_log
    except Exception as e:
        logger.error(f"Error logging weight for user {user.id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log weight. Please try again."
        )
```

Apply similar pattern to:
- `log_meal()`
- `log_workout()`
- All GET endpoints

4. **Add try-except to AI endpoints**:

Edit `src/api/ai.py`:

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


@router.post("/generate-workout-plan")
async def create_workout_plan(
    request: WorkoutPlanRequest,
    user: User = Depends(current_active_user),
):
    """Generate a personalized workout plan using AI"""
    try:
        plan = await generate_workout_plan(
            user_goals=request.user_goals,
            experience_level=request.experience_level,
            equipment_access=request.equipment_access,
            time_availability=request.time_availability,
            injuries=request.injuries,
            age=request.age,
        )
        return plan
    except Exception as e:
        logger.error(f"Error generating workout plan for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again in a few moments."
        )
```

5. **Update templates to show errors**:

Edit `src/templates/dashboard.html`:

Find the weight logging form, add error message div:

```html
<form hx-post="/api/weight" hx-target="#weight-message">
    <!-- form fields -->
</form>
<div id="weight-message" class="mt-2"></div>
```

Do the same for meals and workouts sections.

6. **Test error handling**:

```bash
# Test validation error (invalid data)
curl -X POST http://localhost:8000/api/weight \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"date":"invalid-date","weight_lbs":"not-a-number"}'

# Expected: 422 with validation details

# Test without auth
curl -X POST http://localhost:8000/api/weight \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-11-19","weight_lbs":180}'

# Expected: 401 Unauthorized

# Test AI error (invalid API key)
# Temporarily break ANTHROPIC_API_KEY in .env
curl -X POST http://localhost:8000/api/ai/generate-workout-plan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: 503 with friendly error message
```

7. **Commit error handling**:

```bash
git add src/main.py src/api/data.py src/api/ai.py src/templates/
git commit -m "Add comprehensive error handling

- Global exception handlers for validation, AI, and general errors
- Wrap data logging endpoints in try-except
- Wrap AI endpoints in try-except
- Add user-friendly error messages
- Add error display divs to templates
- Log all errors for debugging"
```

---

## Part 3: Polish for MVP

### Task 5: Fetch and Display Real Data

**Problem**: Dashboard shows placeholders, doesn't fetch actual logged data.

**Steps**:

1. **Update dashboard endpoint**:

Edit `src/api/pages.py`:

```python
from sqlalchemy import select, desc
from src.models.workout import WorkoutSession
from src.models.nutrition import WeightLog, MealLog


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Dashboard page with recent activity"""

    # Fetch recent weight logs (last 7)
    weight_result = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user.id)
        .order_by(desc(WeightLog.date))
        .limit(7)
    )
    recent_weights = weight_result.scalars().all()

    # Fetch recent meals (last 10)
    meal_result = await session.execute(
        select(MealLog)
        .where(MealLog.user_id == user.id)
        .order_by(desc(MealLog.created_at))
        .limit(10)
    )
    recent_meals = meal_result.scalars().all()

    # Fetch recent workouts (last 5)
    workout_result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(desc(WorkoutSession.completed_date))
        .limit(5)
    )
    recent_workouts = workout_result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "recent_weights": recent_weights,
            "recent_meals": recent_meals,
            "recent_workouts": recent_workouts,
        },
    )
```

2. **Update dashboard template**:

Edit `src/templates/dashboard.html`:

Replace placeholder sections with real data:

```html
<!-- Recent Weight section -->
<div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold mb-4">Recent Weight</h2>
    {% if recent_weights %}
        <div class="space-y-2">
        {% for weight in recent_weights %}
            <div class="flex justify-between">
                <span class="text-gray-600">{{ weight.date }}</span>
                <span class="font-semibold">{{ weight.weight_lbs }} lbs</span>
            </div>
        {% endfor %}
        </div>
    {% else %}
        <p class="text-gray-500">No weight logs yet. Log your first weight above!</p>
    {% endif %}
</div>

<!-- Recent Meals section -->
<div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold mb-4">Recent Meals</h2>
    {% if recent_meals %}
        <div class="space-y-3">
        {% for meal in recent_meals %}
            <div class="border-b pb-2">
                <div class="flex justify-between">
                    <span class="font-medium">{{ meal.meal_type }}</span>
                    <span class="text-sm text-gray-600">{{ meal.date }}</span>
                </div>
                <p class="text-sm text-gray-700">{{ meal.description }}</p>
                <div class="text-xs text-gray-500">
                    P: {{ meal.protein_g }}g | C: {{ meal.carbs_g }}g | F: {{ meal.fat_g }}g
                </div>
            </div>
        {% endfor %}
        </div>
    {% else %}
        <p class="text-gray-500">No meals logged yet.</p>
    {% endif %}
</div>

<!-- Recent Workouts section -->
<div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold mb-4">Recent Workouts</h2>
    {% if recent_workouts %}
        <div class="space-y-3">
        {% for workout in recent_workouts %}
            <div class="border-b pb-2">
                <div class="flex justify-between">
                    <span class="font-medium">Workout</span>
                    <span class="text-sm text-gray-600">{{ workout.completed_date }}</span>
                </div>
                <div class="text-sm text-gray-700">
                    Duration: {{ workout.duration_minutes }} min | RPE: {{ workout.overall_rpe }}/10
                </div>
                {% if workout.notes %}
                <p class="text-xs text-gray-600">{{ workout.notes }}</p>
                {% endif %}
            </div>
        {% endfor %}
        </div>
    {% else %}
        <p class="text-gray-500">No workouts logged yet.</p>
    {% endif %}
</div>
```

3. **Update workouts page**:

Edit `src/api/pages.py`:

```python
@router.get("/workouts", response_class=HTMLResponse)
async def workouts_page(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Workouts history page"""

    # Fetch all workouts for user
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(desc(WorkoutSession.completed_date))
    )
    workouts = result.scalars().all()

    return templates.TemplateResponse(
        "workouts.html",
        {
            "request": request,
            "user": user,
            "workouts": workouts,
        },
    )
```

Edit `src/templates/workouts.html`:

Add workout history table:

```html
<!-- After the logging form -->
<div class="bg-white p-6 rounded-lg shadow mt-6">
    <h2 class="text-xl font-semibold mb-4">Workout History</h2>

    {% if workouts %}
    <table class="min-w-full divide-y divide-gray-200">
        <thead>
            <tr>
                <th class="px-4 py-2 text-left">Date</th>
                <th class="px-4 py-2 text-left">Duration</th>
                <th class="px-4 py-2 text-left">RPE</th>
                <th class="px-4 py-2 text-left">Notes</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
        {% for workout in workouts %}
            <tr>
                <td class="px-4 py-2">{{ workout.completed_date }}</td>
                <td class="px-4 py-2">{{ workout.duration_minutes }} min</td>
                <td class="px-4 py-2">{{ workout.overall_rpe }}/10</td>
                <td class="px-4 py-2">{{ workout.notes or '-' }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p class="text-gray-500">No workouts logged yet.</p>
    {% endif %}
</div>
```

4. **Update nutrition page**:

Apply same pattern to `src/api/pages.py` nutrition route and `src/templates/nutrition.html`.

5. **Test data display**:

```bash
# Start app
uv run uvicorn src.main:app --reload

# Login and log some data:
# - Log weight 3 times with different dates
# - Log 5 meals
# - Log 2 workouts

# Visit pages:
# - http://localhost:8000/dashboard (should show recent data)
# - http://localhost:8000/workouts (should show workout table)
# - http://localhost:8000/nutrition (should show meal table)
```

6. **Commit**:

```bash
git add src/api/pages.py src/templates/
git commit -m "Fetch and display real data in UI

- Dashboard shows recent weights, meals, workouts
- Workouts page shows complete history table
- Nutrition page shows meal history table
- Empty states for users with no data yet"
```

---

### Task 6: Add Pytest Suite with Mocked AI

**Steps**:

1. **Install pytest dependencies**:

Edit `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",  # For TestClient
]
```

Install:
```bash
uv sync --extra dev
```

2. **Create pytest configuration**:

Create `pyproject.toml` pytest section:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"
```

3. **Create test structure**:

```bash
mkdir -p tests/{unit,integration}
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

4. **Create fixtures**:

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures"""

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_async_session, Base


# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Test HTTP client"""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_ai_workout_plan():
    """Mock AI workout plan response"""
    return {
        "weeks": 8,
        "phases": [{"name": "Phase 1", "weeks": 4}],
        "exercises": ["Squat", "Bench Press", "Deadlift"],
        "frequency": 4,
        "rationale": "Mock workout plan for testing"
    }


@pytest.fixture
def mock_ai_nutrition_plan():
    """Mock AI nutrition plan response"""
    return {
        "daily_protein_g": 180,
        "daily_carbs_g": 250,
        "daily_fat_g": 70,
        "daily_calories": 2500,
        "meal_suggestions": ["Meal 1", "Meal 2", "Meal 3"],
        "rationale": "Mock nutrition plan for testing"
    }
```

5. **Write unit tests**:

Create `tests/unit/test_models.py`:

```python
"""Test Pydantic models and validation"""

import pytest
from datetime import date
from pydantic import ValidationError

from src.schemas import WeightLogCreate, MealLogCreate, WorkoutSessionCreate


def test_weight_log_validation():
    """Test weight log validates correctly"""

    # Valid data
    data = WeightLogCreate(
        date=date.today(),
        weight_lbs=180.5
    )
    assert data.weight_lbs == 180.5

    # Invalid weight (negative)
    with pytest.raises(ValidationError):
        WeightLogCreate(
            date=date.today(),
            weight_lbs=-10.0
        )


def test_meal_log_validation():
    """Test meal log validates correctly"""

    # Valid data
    data = MealLogCreate(
        date=date.today(),
        meal_type="lunch",
        description="Chicken and rice",
        protein_g=40.0,
        carbs_g=60.0,
        fat_g=10.0
    )
    assert data.protein_g == 40.0

    # Invalid meal type
    with pytest.raises(ValidationError):
        MealLogCreate(
            date=date.today(),
            meal_type="invalid",
            description="Test",
            protein_g=10.0,
            carbs_g=20.0,
            fat_g=5.0
        )
```

6. **Write integration tests**:

Create `tests/integration/test_auth.py`:

```python
"""Test authentication flow"""

import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    """Test user registration"""

    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_login_user(client):
    """Test user login"""

    # Register first
    await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    # Login
    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client):
    """Test protected endpoints require authentication"""

    response = await client.get("/auth/users/me")

    assert response.status_code == 401
```

Create `tests/integration/test_data_logging.py`:

```python
"""Test data logging endpoints"""

import pytest
from datetime import date


async def get_auth_token(client):
    """Helper to register and login user"""
    await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )

    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )

    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_log_weight(client):
    """Test logging weight"""

    token = await get_auth_token(client)

    response = await client.post(
        "/api/weight",
        json={
            "date": str(date.today()),
            "weight_lbs": 180.5
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["weight_lbs"] == 180.5


@pytest.mark.asyncio
async def test_get_weight_history(client):
    """Test retrieving weight history"""

    token = await get_auth_token(client)

    # Log some weights
    await client.post(
        "/api/weight",
        json={"date": str(date.today()), "weight_lbs": 180.0},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get history
    response = await client.get(
        "/api/weight",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["weight_lbs"] == 180.0
```

7. **Write AI tests with mocks**:

Create `tests/integration/test_ai.py`:

```python
"""Test AI endpoints with mocked responses"""

import pytest
from unittest.mock import AsyncMock, patch
from src.services.ai import WorkoutPlanOutput, MealPlanOutput


@pytest.mark.asyncio
async def test_generate_workout_plan_mocked(mock_ai_workout_plan):
    """Test workout plan generation with mocked AI"""

    with patch('src.services.ai.Agent.run') as mock_run:
        # Setup mock
        mock_result = AsyncMock()
        mock_result.data = WorkoutPlanOutput(**mock_ai_workout_plan)
        mock_run.return_value = mock_result

        # Import after patching
        from src.services.ai import generate_workout_plan

        result = await generate_workout_plan(
            user_goals="Build muscle",
            experience_level="intermediate",
            equipment_access=["barbell"],
            time_availability=240
        )

        assert result.weeks == 8
        assert result.frequency == 4
        assert len(result.exercises) == 3
```

8. **Run tests**:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run with verbose output
uv run pytest -v
```

9. **Commit tests**:

```bash
git add tests/ pyproject.toml pytest.ini
git commit -m "Add comprehensive test suite

- Unit tests for Pydantic models and validation
- Integration tests for auth flow
- Integration tests for data logging endpoints
- AI tests with mocked responses (no API costs)
- pytest configuration with async support
- Test coverage setup"
```

---

### Task 7: Compile Tailwind CSS

**Steps**:

1. **Install Tailwind CLI**:

```bash
# Download standalone CLI (no npm required)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 /usr/local/bin/tailwindcss

# Or use npm if preferred
npm install -D tailwindcss
```

2. **Initialize Tailwind**:

```bash
cd src/static
tailwindcss init
```

This creates `src/static/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.html",
    "../static/**/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

3. **Create input CSS file**:

Create `src/static/css/input.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom styles */
body {
  @apply bg-gray-50;
}

.btn-primary {
  @apply bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700;
}
```

4. **Build CSS**:

```bash
# From project root
tailwindcss -i src/static/css/input.css -o src/static/css/output.css --minify

# For development (watch mode)
tailwindcss -i src/static/css/input.css -o src/static/css/output.css --watch
```

5. **Update base template**:

Edit `src/templates/base.html`:

Replace:
```html
<script src="https://cdn.tailwindcss.com"></script>
```

With:
```html
<link rel="stylesheet" href="/static/css/output.css">
```

6. **Add build script**:

Create `scripts/build.sh`:

```bash
#!/bin/bash
set -e

echo "Building Tailwind CSS..."
tailwindcss -i src/static/css/input.css -o src/static/css/output.css --minify

echo "Build complete!"
```

Make executable:
```bash
chmod +x scripts/build.sh
```

7. **Update .gitignore**:

```
# Tailwind output
src/static/css/output.css
```

8. **Test**:

```bash
# Build CSS
./scripts/build.sh

# Start app
uv run uvicorn src.main:app --reload

# Open browser, verify styles still work
# Check browser console - should have no Tailwind CDN warnings
```

9. **Document in README**:

Add to README.md development section:

```markdown
### Build Static Assets

```bash
# Build Tailwind CSS (production)
./scripts/build.sh

# Watch mode (development)
tailwindcss -i src/static/css/input.css -o src/static/css/output.css --watch
```
```

10. **Commit**:

```bash
git add src/static/ src/templates/base.html scripts/ .gitignore
git commit -m "Replace Tailwind CDN with compiled CSS

- Initialize Tailwind CLI build
- Create input.css with custom styles
- Build minified output.css for production
- Remove CDN script tag
- Add build script for automation"
```

---

### Task 8: Deploy to Fly.io

**Steps**:

1. **Install Fly CLI**:

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Verify installation
fly version
```

2. **Login to Fly**:

```bash
fly auth login
```

This opens browser for authentication.

3. **Create Dockerfile**:

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Build static assets
COPY scripts ./scripts
RUN chmod +x scripts/build.sh && ./scripts/build.sh

# Expose port
EXPOSE 8080

# Run migrations and start app
CMD uv run alembic upgrade head && \
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8080
```

4. **Create .dockerignore**:

```
.env
.git
.venv
__pycache__
*.pyc
*.db
test.db
.pytest_cache
.ruff_cache
```

5. **Test Docker build locally**:

```bash
# Build image
docker build -t fit-agent .

# Run container
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=test123 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  fit-agent

# Test
curl http://localhost:8080/health
```

6. **Create fly.toml**:

```toml
app = "fit-agent"
primary_region = "sea"  # Change to your nearest region

[build]

[env]
  ENVIRONMENT = "production"
  DEBUG = "false"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

7. **Launch app on Fly**:

```bash
# Initialize and create app
fly launch

# Follow prompts:
# - App name: fit-agent (or your choice)
# - Region: Select nearest (e.g., sea for Seattle)
# - PostgreSQL: Yes (select shared-cpu-1x, 256MB)
# - Redis: No (Phase 2)
# - Deploy now: No (set secrets first)
```

8. **Set secrets**:

```bash
# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Set all secrets
fly secrets set SECRET_KEY=$SECRET_KEY
fly secrets set ANTHROPIC_API_KEY=sk-ant-api03-...
fly secrets set DEBUG=false
fly secrets set ENVIRONMENT=production

# Database URL is auto-configured by Fly
```

9. **Deploy**:

```bash
fly deploy
```

Monitor deployment:
```bash
fly logs
```

10. **Verify deployment**:

```bash
# Get app URL
fly status

# Test health endpoint
curl https://fit-agent.fly.dev/health

# Expected: {"status":"healthy","environment":"production"}
```

11. **Test in browser**:

Visit: `https://fit-agent.fly.dev`

- Register new account
- Login
- Log weight/meal/workout
- Verify all features work

12. **Set up auto-deploy** (optional):

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy to Fly.io
        run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Get token:
```bash
fly tokens create deploy
```

Add to GitHub secrets as `FLY_API_TOKEN`.

13. **Document deployment**:

Update README.md:

```markdown
## Deployment

App is deployed at: https://fit-agent.fly.dev

### Deploy manually

```bash
fly deploy
```

### View logs

```bash
fly logs
```

### Database access

```bash
fly postgres connect -a <postgres-app-name>
```
```

14. **Commit deployment config**:

```bash
git add Dockerfile fly.toml .dockerignore .github/
git commit -m "Add Fly.io deployment configuration

- Dockerfile with multi-stage build
- fly.toml with auto-scaling config
- GitHub Actions for auto-deploy on push to main
- Deployed at https://fit-agent.fly.dev"
```

---

## Part 4: Verification & Next Steps

### Final Verification Checklist

Run through this checklist:

```bash
# Local testing
- [ ] Start app: uv run uvicorn src.main:app --reload
- [ ] Register new user
- [ ] Login successfully
- [ ] Log weight (no 401 error)
- [ ] Log meal (no 401 error)
- [ ] Log workout (no 401 error)
- [ ] View dashboard (shows recent data)
- [ ] View workouts page (shows history)
- [ ] View nutrition page (shows history)
- [ ] Call AI workout plan endpoint (works)
- [ ] Call AI nutrition endpoint (works)

# Database
- [ ] Run: uv run alembic upgrade head (no errors)
- [ ] Run: uv run alembic downgrade -1 (works)
- [ ] Run: uv run alembic upgrade head (works)
- [ ] Check tables exist: psql -d fitgent -c "\dt"

# Tests
- [ ] Run: uv run pytest (all pass)
- [ ] Run: uv run pytest --cov=src (>70% coverage)

# Deployment
- [ ] Build Docker: docker build -t fit-agent .
- [ ] Deploy: fly deploy (success)
- [ ] Test production: curl https://fit-agent.fly.dev/health
- [ ] Register user on production
- [ ] Test all features on production
```

### Update Documentation

After completing MVP:

1. **Update fit_agent_plan.md**:

```markdown
## **CURRENT STATUS UPDATE** (2025-11-19)

### **Phase 1 Progress: ✅ 100% Complete**

**✅ Completed:**
- All Phase 1 tasks finished
- HTMX auth bug fixed
- Alembic migrations set up
- AI endpoints tested end-to-end
- Error handling added
- Real data displayed in UI
- Test suite with 70%+ coverage
- Tailwind CSS compiled
- Deployed to Fly.io

**📊 Metrics:**
- Lines of Code: ~2,000 Python
- Test Coverage: 75%
- Database: PostgreSQL with Alembic migrations
- Deployment: https://fit-agent.fly.dev

**🎉 MVP COMPLETE**
```

2. **Update IMPLEMENTATION_STATUS.md**:

Mark all Phase 1 items as complete.

3. **Update README.md**:

Add deployment URL and update status.

### Next Phase Planning

**Phase 2 begins** with:

1. **Multi-model AI strategy**
   - Add Opus for planning
   - Add GPT-5-mini for extraction
   - Add Haiku for validation
   - Add cost tracking

2. **Redis caching**
   - Cache AI responses
   - Reduce duplicate API calls

3. **Background jobs**
   - Weekly analysis automation
   - Email notifications

See `fit_agent_plan.md` Phase 2 section for details.

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep fitgent-db

# Check connection
psql -d fitgent -U postgres -h localhost -c "SELECT 1;"

# Reset database
docker stop fitgent-db
docker rm fitgent-db
# Re-create (see Part 1: Start PostgreSQL)
```

### Alembic Migration Errors

```bash
# Check current migration version
uv run alembic current

# Force to head (if stuck)
uv run alembic stamp head

# Reset all migrations (dev only!)
uv run alembic downgrade base
uv run alembic upgrade head
```

### HTMX Auth Still Broken

Debug steps:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Submit weight form
4. Click the request
5. Check Headers tab
6. Verify `Authorization: Bearer ...` exists
7. If missing, check:
   - Login saves token: `localStorage.getItem('access_token')`
   - Script runs: Check Console for errors
   - Event listener attached: Add `console.log()` in script

### AI Endpoints Return Errors

```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# Test directly
curl https://api.anthropic.com/v1/messages \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","max_tokens":100,"messages":[{"role":"user","content":"Hi"}]}'

# Should return response, not error
```

### Fly Deployment Fails

```bash
# Check logs
fly logs

# Common issues:
# - Missing secrets: fly secrets list
# - Database not attached: fly postgres attach <db-name>
# - Build fails: Test Docker build locally first
# - Port mismatch: Check internal_port in fly.toml matches CMD

# Redeploy
fly deploy --strategy immediate
```

---

## Quick Reference

### Common Commands

```bash
# Development
uv sync                                    # Install dependencies
uv run uvicorn src.main:app --reload      # Start dev server
uv run pytest                              # Run tests
uv run alembic upgrade head                # Run migrations

# Database
docker start fitgent-db                    # Start PostgreSQL
psql -d fitgent -U postgres -h localhost   # Connect to DB

# Deployment
fly deploy                                 # Deploy to Fly.io
fly logs                                   # View logs
fly ssh console                            # SSH to production

# Git
git add .
git commit -m "message"
git push origin main
```

### Key Files

- `src/main.py` - FastAPI app
- `src/services/ai.py` - AI agents
- `src/api/` - API routes
- `src/models/` - Database models
- `src/templates/` - HTML templates
- `alembic/versions/` - Database migrations
- `tests/` - Test suite
- `.env` - Environment variables (local)
- `fly.toml` - Deployment config

---

## Support

Questions? Check:

1. `fit_agent_plan.md` - Comprehensive project plan
2. `IMPLEMENTATION_STATUS.md` - Current status
3. `CLAUDE.md` - Development guidelines
4. `docs/` - Additional guides

Issues? Review logs:

```bash
# Local
uv run uvicorn src.main:app --reload --log-level debug

# Production
fly logs --app fit-agent
```
