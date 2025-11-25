# Multi-Model AI Testing Strategy

## Overview

Testing multi-model AI requires mocking all provider APIs to avoid burning credits in CI/CD and during development.

## Mock Strategy

### Option 1: PydanticAI TestModel (Recommended)

```python
from pydantic_ai.models.test import TestModel

# In tests, inject TestModel instead of real models
test_model = TestModel(
    custom_result_text="Mocked response"
)

# Override agent model for testing
agent = Agent('openai:gpt-5-mini')
agent._model = test_model  # Inject mock
```

### Option 2: pytest-mock with fixtures

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Mock Anthropic API client"""
    mock_response = AsyncMock()
    mock_response.data = {
        "weeks": 8,
        "phases": [{"name": "Phase 1", "weeks": 4}],
        "exercises": ["Squat", "Bench", "Deadlift"],
        "frequency": 4,
        "rationale": "Test rationale"
    }
    mock_response.usage.return_value = {
        "request_tokens": 500,
        "response_tokens": 200,
        "total_tokens": 700
    }

    monkeypatch.setattr(
        "src.services.ai.Agent.run",
        AsyncMock(return_value=mock_response)
    )
    return mock_response

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI API client"""
    # Similar pattern for OpenAI
    pass

@pytest.fixture
def mock_google_client(monkeypatch):
    """Mock Google Generative AI client"""
    # Similar pattern for Gemini
    pass
```

### Option 3: Environment-based mocking

```python
# src/services/ai.py (add at top)
import os

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "false").lower() == "true"

if USE_MOCK_AI:
    from pydantic_ai.models.test import TestModel

    def get_planning_agent() -> Agent:
        return Agent(
            TestModel(
                custom_result_text='{"weeks": 8, "phases": [], "exercises": [], "frequency": 4, "rationale": "Mock"}'
            ),
            result_type=WorkoutPlanOutput,
        )
```

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_ai_agents.py       # Agent initialization
│   ├── test_models.py          # Pydantic model validation
│   └── test_cost_tracking.py   # Logfire instrumentation
├── integration/
│   ├── test_workout_planning.py    # End-to-end planning flow
│   ├── test_extraction.py          # Data extraction with mocks
│   └── test_multi_model.py         # Model fallback logic
└── manual/
    └── test_real_apis.py       # Run manually with real API keys (not in CI)
```

## Example Test Cases

### Test 1: Model Selection is Correct

```python
# tests/unit/test_ai_agents.py
import pytest
from src.services.ai import (
    get_planning_agent,
    get_nutrition_agent,
    get_extraction_agent,
    get_validation_agent,
    get_deep_analysis_agent,
)

def test_planning_agent_uses_opus():
    """Planning agent should use Claude Opus 4.1"""
    agent = get_planning_agent()
    # PydanticAI stores model string in agent._model or similar
    # Verify it's the expected model
    assert "claude-opus-4-1" in str(agent._model).lower()

def test_extraction_agent_uses_gpt5mini():
    """Extraction agent should use GPT-5-mini"""
    agent = get_extraction_agent()
    assert "gpt-5-mini" in str(agent._model).lower()

def test_validation_agent_uses_haiku():
    """Validation agent should use Claude Haiku 4.5"""
    agent = get_validation_agent()
    assert "haiku" in str(agent._model).lower()

def test_deep_analysis_uses_gemini():
    """Deep analysis agent should use Gemini 2.5 Pro"""
    agent = get_deep_analysis_agent()
    assert "gemini-2.5-pro" in str(agent._model).lower()
```

### Test 2: Mocked Workout Plan Generation

```python
# tests/integration/test_workout_planning.py
import pytest
from src.services.ai import generate_workout_plan

@pytest.mark.asyncio
async def test_generate_workout_plan_structure(mock_anthropic_client):
    """Test workout plan generation with mocked API"""
    result = await generate_workout_plan(
        user_goals="Build muscle",
        experience_level="intermediate",
        equipment_access=["barbell", "dumbbells", "rack"],
        time_availability=240,
        age=30,
    )

    assert result.weeks > 0
    assert result.frequency > 0
    assert len(result.exercises) > 0
    assert len(result.rationale) > 0
```

### Test 3: Cost Tracking

```python
# tests/unit/test_cost_tracking.py
import pytest
from unittest.mock import MagicMock
from src.services.ai import generate_workout_plan

@pytest.mark.asyncio
async def test_logfire_cost_tracking(mock_anthropic_client, monkeypatch):
    """Verify Logfire logs cost metrics"""
    logfire_calls = []

    def capture_logfire(event_name, **kwargs):
        logfire_calls.append((event_name, kwargs))

    monkeypatch.setattr("logfire.info", capture_logfire)

    await generate_workout_plan(
        user_goals="Test",
        experience_level="beginner",
        equipment_access=["bodyweight"],
        time_availability=120,
    )

    # Verify Logfire was called with cost data
    assert any("workout_plan_generated" in call[0] for call in logfire_calls)
    cost_log = next(c for c in logfire_calls if "workout_plan_generated" in c[0])
    assert "total_tokens" in cost_log[1]
    assert "model" in cost_log[1]
```

### Test 4: Model Fallback (Future Enhancement)

```python
# tests/integration/test_multi_model.py
import pytest
from src.services.ai import generate_workout_plan

@pytest.mark.asyncio
async def test_model_fallback_on_failure(monkeypatch):
    """If Opus fails, should fall back to Sonnet"""
    # Simulate API failure
    def mock_opus_fail(*args, **kwargs):
        raise Exception("API rate limit exceeded")

    monkeypatch.setattr("anthropic.AsyncAnthropic.messages.create", mock_opus_fail)

    # Should fall back to Sonnet (requires implementing fallback logic)
    # For now, this test demonstrates what we want
    with pytest.raises(Exception):
        await generate_workout_plan(
            user_goals="Test",
            experience_level="beginner",
            equipment_access=["bodyweight"],
            time_availability=120,
        )

    # TODO: Implement fallback and assert it used Sonnet instead
```

## Running Tests

```bash
# Run all tests with mocks (no API calls)
uv run pytest

# Run with coverage
uv run pytest --cov=src/services/ai

# Run manual tests with real APIs (requires API keys)
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...
uv run pytest tests/manual/ --real-apis

# Run only fast unit tests
uv run pytest tests/unit/
```

## CI/CD Configuration

```yaml
# .github/workflows/test.yml
name: Test AI Services

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run tests (mocked)
        env:
          USE_MOCK_AI: "true"
        run: uv run pytest --cov=src

      # DO NOT run tests/manual/ in CI - requires real API keys
```

## Manual Testing Checklist

Before deploying multi-model changes:

1. **Test each model individually** (requires API keys):
   ```bash
   uv run python -c "
   import asyncio
   from src.services.ai import generate_workout_plan
   asyncio.run(generate_workout_plan(
       user_goals='Build muscle',
       experience_level='intermediate',
       equipment_access=['barbell', 'rack'],
       time_availability=240,
       age=30
   ))
   "
   ```

2. **Verify cost tracking in Logfire** (if configured):
   - Check that `workout_plan_generated` events appear
   - Verify token counts are reasonable
   - Check estimated costs match expectations

3. **Test extraction with GPT-5-mini**:
   ```bash
   uv run python -c "
   import asyncio
   from src.services.ai import extract_workout_log
   asyncio.run(extract_workout_log('Bench 225x5x3 @RPE 8'))
   "
   ```

4. **Test validation with Haiku**:
   ```bash
   uv run python -c "
   import asyncio
   from src.services.ai import validate_exercise_name
   asyncio.run(validate_exercise_name('bench'))
   "
   ```

5. **Test Gemini deep analysis** (expensive, run sparingly):
   - Generate sample data (2+ months of logs)
   - Run `analyze_complete_history()`
   - Verify it handles large context without errors

## Cost Monitoring

Expected costs during testing (with real APIs):

- **Unit tests** (mocked): $0
- **Integration tests** (mocked): $0
- **Manual testing** (real APIs, ~20 calls): $0.50-1.00
- **Full manual validation** (all models, ~50 calls): $2-5

**Budget**: Set $10/month testing budget. If exceeded, review test strategy.

## Future Enhancements

1. **Snapshot testing** for prompt consistency
2. **Model fallback logic** (Opus → Sonnet → Haiku)
3. **Response caching** during development (avoid repeat calls)
4. **A/B testing framework** for prompt optimization
5. **Mock response generator** based on real API response formats
