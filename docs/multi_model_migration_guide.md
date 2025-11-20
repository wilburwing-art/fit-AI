# Multi-Model Migration Guide

## Migration from Single-Model to Multi-Model Strategy

This guide walks through migrating from the current single-model (Claude Sonnet 4.5 for everything) to the optimized multi-model approach.

## Pre-Migration Checklist

- [ ] All API keys configured in `.env`:
  - `ANTHROPIC_API_KEY` (for Opus, Sonnet, Haiku)
  - `OPENAI_API_KEY` (for GPT-5-mini)
  - `GOOGLE_API_KEY` (for Gemini 2.5 Pro)
- [ ] Logfire token configured: `LOGFIRE_TOKEN`
- [ ] Dependencies installed: `uv sync`
- [ ] Tests passing: `uv run pytest`
- [ ] Backup current `src/services/ai.py` (git should have this)

## Migration Steps

### Step 1: Environment Configuration

Update `.env` with all required API keys:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...  # Required: Used for Opus, Sonnet, Haiku
OPENAI_API_KEY=sk-...                # Required: Used for GPT-5-mini extraction
GOOGLE_API_KEY=...                   # Optional: Used for Gemini deep analysis

LOGFIRE_TOKEN=...                    # Optional but recommended: Cost tracking
```

### Step 2: Verify Dependencies

Ensure `pyproject.toml` includes all required packages:

```toml
dependencies = [
    "pydantic-ai-slim[anthropic,logfire,openai]>=1.15.0",  # Core AI
    # ... other deps
]
```

If Google support needed, add:
```toml
dependencies = [
    "pydantic-ai-slim[anthropic,logfire,openai,google]>=1.15.0",
    # OR install google-generativeai separately:
    "google-generativeai>=0.8.0",
]
```

Run: `uv sync`

### Step 3: Replace ai.py

The new `src/services/ai.py` has been written. Verify changes:

```bash
# Compare old vs new
git diff src/services/ai.py

# Key changes:
# - 7 agent types instead of 2
# - Model-specific selection per agent
# - New functions: extract_workout_log, extract_meal_log, validate_exercise_name, etc.
# - Logfire instrumentation on all functions
```

### Step 4: Update API Endpoints (if needed)

Check if any routes in `src/api/` call AI functions directly. Update calls:

**Before:**
```python
# Old approach - no extraction agent
meal_data = {
    "protein_g": form.protein,
    "carbs_g": form.carbs,
    # ...
}
```

**After (Phase 2 - Natural Language Logging):**
```python
from src.services.ai import extract_meal_log

# User inputs: "Chicken breast, rice, broccoli - ~40p/50c/10f"
meal_data = await extract_meal_log(user_input)
# Returns: MealLogExtraction with parsed macros
```

### Step 5: Test Each Model Individually

Run manual tests to verify each model works:

```bash
# Test 1: Opus (Planning)
uv run python -c "
import asyncio
from src.services.ai import generate_workout_plan

async def test():
    result = await generate_workout_plan(
        user_goals='Build muscle',
        experience_level='intermediate',
        equipment_access=['barbell', 'rack', 'dumbbells'],
        time_availability=240,
        age=30
    )
    print(f'Plan: {result.weeks} weeks, {result.frequency}x/week')
    print(f'Exercises: {result.exercises[:3]}')

asyncio.run(test())
"

# Test 2: GPT-5-mini (Extraction)
uv run python -c "
import asyncio
from src.services.ai import extract_workout_log

async def test():
    result = await extract_workout_log('Bench 225x5x3 @RPE 8, felt strong')
    print(f'Exercise: {result.exercise_name}')
    print(f'Sets: {result.sets}')

asyncio.run(test())
"

# Test 3: Haiku (Validation)
uv run python -c "
import asyncio
from src.services.ai import validate_exercise_name

async def test():
    result = await validate_exercise_name('bench')
    print(f'Valid: {result.is_valid}')
    print(f'Normalized: {result.normalized_value}')

asyncio.run(test())
"

# Test 4: Sonnet (Analysis)
uv run python -c "
import asyncio
from src.services.ai import analyze_progress

async def test():
    result = await analyze_progress(
        workout_history=[{'date': '2025-11-01', 'exercise': 'Squat', 'weight': 315}],
        weight_history=[{'date': '2025-11-01', 'weight': 180}],
        meal_history=[{'date': '2025-11-01', 'protein': 150, 'calories': 2500}]
    )
    print(result)

asyncio.run(test())
"

# Test 5: Gemini (Deep Analysis) - EXPENSIVE, run sparingly
# Only run this if you have GOOGLE_API_KEY configured
uv run python -c "
import asyncio
from src.services.ai import analyze_complete_history

async def test():
    # Use small test data to minimize cost
    result = await analyze_complete_history(
        complete_workout_history=[{'date': '2025-10-01', 'exercise': 'Squat', 'weight': 300}],
        complete_nutrition_history=[{'date': '2025-10-01', 'protein': 150}],
        complete_weight_history=[{'date': '2025-10-01', 'weight': 180}],
        user_profile={'goals': 'Build strength', 'age': 30}
    )
    print(result[:500])  # Print first 500 chars

asyncio.run(test())
"
```

### Step 6: Monitor Costs in Logfire

If Logfire configured:

1. Visit https://logfire.pydantic.dev
2. Check spans for `ai_workout_plan_generation`, `ai_extract_workout_log`, etc.
3. Verify token counts and cost estimates appear
4. Set up alerts for daily cost > $5 (during testing)

### Step 7: Gradual Rollout

**Week 1: Deploy multi-model, monitor costs**
- Deploy updated `src/services/ai.py`
- Keep existing UI (manual logging)
- Monitor costs daily
- Expected: $1-3/week for 2-3 users

**Week 2: Add natural language logging (optional Phase 2)**
- Update workout/meal logging forms to accept NL input
- Call `extract_workout_log()` and `extract_meal_log()`
- Expected: Additional $0.50-1.00/week

**Week 3: Add conversational coaching (optional Phase 2)**
- Add chat UI
- Call `answer_coaching_question()`
- Expected: Additional $1-2/week

**Week 4: Add deep analysis (optional Phase 3)**
- Monthly deep dive with Gemini
- Call `analyze_complete_history()`
- Expected: Additional $1-2/month

## Rollback Plan

If costs exceed budget or models fail:

### Option 1: Revert to Sonnet-only

```python
# Quick fix: override all agents to use Sonnet
# Add to src/services/ai.py top

FORCE_SONNET_ONLY = True  # Emergency override

if FORCE_SONNET_ONLY:
    def get_planning_agent():
        return Agent("anthropic:claude-sonnet-4-5-20250929", result_type=WorkoutPlanOutput, ...)
    # Override all other agents similarly
```

### Option 2: Git Revert

```bash
git log --oneline  # Find commit before multi-model
git revert <commit-hash>
git push
```

### Option 3: Disable Expensive Models

```python
# Disable Opus, use Sonnet for planning
def get_planning_agent():
    return Agent(
        "anthropic:claude-sonnet-4-5-20250929",  # Instead of Opus
        result_type=WorkoutPlanOutput,
        ...
    )

# Disable Gemini, use Sonnet for deep analysis
def get_deep_analysis_agent():
    return Agent("anthropic:claude-sonnet-4-5-20250929", ...)
```

## Cost Monitoring

Track these metrics weekly:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Total AI cost (weekly) | $3-5 | > $10 |
| Opus calls (weekly) | 8-12 | > 20 |
| GPT-5-mini calls (weekly) | 50-100 | > 300 |
| Haiku calls (weekly) | 20-50 | > 150 |
| Gemini calls (monthly) | 4-8 | > 15 |
| Cost per user (monthly) | $5-10 | > $20 |

### Logfire Query Examples

```python
# In Logfire dashboard, filter spans:

# Total cost this week
sum(estimated_cost_usd) where timestamp > now() - 7d

# Most expensive model this month
group_by(model).sum(estimated_cost_usd) where timestamp > now() - 30d

# Opus usage frequency
count(*) where model = 'claude-opus-4-1-20250805' and timestamp > now() - 7d
```

## Troubleshooting

### Issue: API Key Not Found

**Symptom:** `AuthenticationError: Invalid API key`

**Fix:**
1. Check `.env` has correct key format
2. Restart app to reload environment
3. Verify key not expired (check provider dashboard)

### Issue: Model Not Found

**Symptom:** `ModelNotFoundError: claude-opus-4-1-20250805 not found`

**Fix:**
1. Check model name matches current API (models change over time)
2. Try dated endpoint: `claude-opus-4-1-20250805` vs `claude-opus-4`
3. Fall back to Sonnet if Opus unavailable

### Issue: Costs Too High

**Symptom:** Logfire shows $20/day AI costs

**Fix:**
1. Check for infinite loops (agent calling itself)
2. Verify caching works (duplicate calls for same input)
3. Reduce context size (trim history to recent 30 days)
4. Switch expensive models to cheaper alternatives

### Issue: Structured Output Fails

**Symptom:** `ValidationError: Invalid response format`

**Fix:**
1. Check Pydantic model matches expected output
2. Add retry logic with backoff
3. Log raw response to debug
4. Simplify system prompt

## Success Criteria

Migration is successful when:

- [ ] All 5+ models tested and working
- [ ] Logfire shows cost metrics for each model
- [ ] Weekly cost < $5 for 2-3 users
- [ ] No API authentication errors for 7 days
- [ ] Opus used for planning (8-12 calls/week)
- [ ] GPT-5-mini used for extraction (50+ calls/week)
- [ ] Haiku used for validation (20+ calls/week)
- [ ] Response times < 3s for 95th percentile
- [ ] Zero data loss from parsing errors

## Next Steps After Migration

1. **Phase 2: Implement Redis caching**
   - Cache AI responses (TTL: 7 days)
   - Reduce duplicate API calls
   - Expected savings: 20-30% of costs

2. **Phase 2: Add background jobs**
   - Weekly analysis runs automatically
   - Batch calls instead of on-demand
   - Expected savings: 10-15% of costs

3. **Phase 3: Optimize prompts**
   - A/B test shorter prompts
   - Reduce token usage 20-30%
   - Expected savings: 15-20% of costs

4. **Phase 3: Implement fallback logic**
   - Opus fails → fall back to Sonnet
   - Gemini fails → fall back to Sonnet with chunking
   - Improve reliability without increasing costs

## Reference

- PydanticAI Docs: https://ai.pydantic.dev/
- Anthropic API: https://docs.anthropic.com/
- OpenAI API: https://platform.openai.com/docs/
- Google Generative AI: https://ai.google.dev/docs
- Logfire: https://logfire.pydantic.dev/
