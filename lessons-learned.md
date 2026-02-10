# Lessons Learned

Project-specific discoveries and insights for fit-AI.

---

## AI Agents

### YYYY-MM-DD: Model selection matters
**Context**: [Describe situation]
**Learning**: Using Opus for everything was expensive. Most tasks work fine with Sonnet or even Haiku.
**Impact**: Implemented tiered model strategy, reduced costs 70%.

### YYYY-MM-DD: Structured outputs prevent hallucination
**Context**: [Describe situation]
**Learning**: PydanticAI's structured outputs catch when models don't follow instructions. Retry with better prompt.
**Impact**: Added validation + retry logic to all agents.

### YYYY-MM-DD: Caching is essential
**Context**: [Describe situation]
**Learning**: Regenerating workout plans on every view was burning API credits. 7-day cache is fine for this use case.
**Impact**: Added Redis caching, cut API calls 90%.

---

## Frontend

### YYYY-MM-DD: HTMX simplicity wins
**Context**: [Describe situation]
**Learning**: Considered React but HTMX + Alpine covers all use cases with 10x less code.
**Impact**: Kept stack simple, faster development.

### YYYY-MM-DD: Mobile-first responsive
**Context**: [Describe situation]
**Learning**: Users log workouts at the gym on phones. Desktop was afterthought.
**Impact**: Redesigned all views mobile-first.

---

## Database

### YYYY-MM-DD: SQLModel gotchas
**Context**: [Describe situation]
**Learning**: SQLModel relationship definitions differ from pure SQLAlchemy. Check docs carefully.
**Impact**: [How it changed the project]

### YYYY-MM-DD: JSONB for flexible schemas
**Context**: [Describe situation]
**Learning**: Workout plans have variable structure. JSONB column better than normalized tables.
**Impact**: Simplified schema, easier AI integration.

---

## Cost Management

### YYYY-MM-DD: Logfire for visibility
**Context**: [Describe situation]
**Learning**: Without cost tracking, had no idea which features were expensive. Logfire made it visible.
**Impact**: Added per-endpoint cost tracking.

### YYYY-MM-DD: Token counting
**Context**: [Describe situation]
**Learning**: Long user histories were inflating costs. Needed to summarize or truncate.
**Impact**: Implemented context window management.

---

## Deployment

### YYYY-MM-DD: Fly.io secrets management
**Context**: [Describe situation]
**Learning**: Environment variables in fly.toml are visible. Use `fly secrets` for sensitive data.
**Impact**: Moved all API keys to secrets.

### YYYY-MM-DD: [Title]
**Context**: [Describe situation]
**Learning**: [What you learned]
**Impact**: [How it changed the project]

---

## User Experience

### YYYY-MM-DD: [Title]
**Context**: [Describe situation]
**Learning**: [What you learned]
**Impact**: [How it changed the project]

---

## Template

<!--
### YYYY-MM-DD: Brief title
**Context**: What were you trying to do?
**Learning**: What did you discover?
**Impact**: How did this change the project?
-->
