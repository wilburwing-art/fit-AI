# Error Documentation

Known issues and fixes for fit-AI.

---

## Database

### "Connection refused"
**Symptoms**: App can't connect to PostgreSQL
**Cause**: Database not running
**Fix**:
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16
```

### Alembic migration conflicts
**Symptoms**: Multiple heads, can't upgrade
**Cause**: Branched migration history
**Fix**:
```bash
# See heads
uv run alembic heads

# Merge if needed
uv run alembic merge -m "merge heads" head1 head2
uv run alembic upgrade head
```

---

## AI Agents

### "API key invalid"
**Symptoms**: PydanticAI agent fails on first call
**Cause**: Missing or expired API key
**Fix**: Check `.env` for correct keys:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

### Rate limit / quota exceeded
**Symptoms**: 429 error from AI provider
**Cause**: Hit API rate limits
**Fix**:
- Check dashboard for quota
- Implement exponential backoff
- Use cheaper model for high-volume tasks

### Unexpected output format
**Symptoms**: Pydantic validation error on AI response
**Cause**: Model didn't follow schema
**Fix**:
```python
# Add retry with better prompt
result = await agent.run(
    prompt,
    retries=3,  # Retry on validation failure
)
```

### High costs
**Symptoms**: Bill higher than expected
**Cause**: Using expensive model for simple tasks
**Fix**:
- Use GPT-5-mini for extraction
- Use Haiku for validation
- Cache responses (7-day TTL)

---

## Frontend (HTMX)

### Partial not rendering
**Symptoms**: HTMX request succeeds but nothing updates
**Cause**: Wrong hx-target or hx-swap
**Fix**:
```html
<!-- Ensure target exists -->
<div id="target"></div>

<!-- Correct targeting -->
<button hx-post="/action" hx-target="#target" hx-swap="innerHTML">
```

### Form not submitting
**Symptoms**: Button click does nothing
**Cause**: Missing hx-post/hx-get
**Fix**: Add HTMX attributes to form or button

### Alpine.js state not updating
**Symptoms**: UI doesn't reflect data changes
**Cause**: Reactivity issue
**Fix**:
```html
<!-- Use x-effect for side effects -->
<div x-data="{ count: 0 }" x-effect="console.log(count)">
```

---

## Caching (Redis)

### Cache miss when expecting hit
**Symptoms**: AI called when cached response exists
**Cause**: Cache key mismatch or expired TTL
**Fix**:
```bash
# Check what's in cache
redis-cli KEYS "*"
redis-cli GET "cache:workout_plan:user_123"
```

### Redis connection refused
**Symptoms**: Cache operations fail
**Cause**: Redis not running
**Fix**:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Deployment (Fly.io)

### Deploy fails
**Symptoms**: `fly deploy` errors out
**Cause**: Various (check logs)
**Fix**:
```bash
fly logs
# Common: missing secrets
fly secrets set ANTHROPIC_API_KEY=...
```

### App not starting
**Symptoms**: Health check fails
**Cause**: Port mismatch or startup error
**Fix**: Ensure app listens on `0.0.0.0:8080`

---

## Linting

### Ruff errors on save
**Symptoms**: VSCode shows lint errors
**Cause**: Code doesn't match Ruff rules
**Fix**:
```bash
uvx ruff check --fix .
uvx ruff format .
```

---

## Add your own errors below

<!-- Template:
### Error title
**Symptoms**: What you see
**Cause**: Why it happens
**Fix**:
```bash
commands to fix
```
-->
