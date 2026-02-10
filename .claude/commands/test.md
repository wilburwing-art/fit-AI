# Run test suite

Run the test suite and report results.

## Steps

1. Run tests with coverage:
```bash
uv run pytest --cov=src
```

2. Report summary:
   - Total tests run
   - Passed/failed counts
   - Coverage percentage
   - Any failures with brief explanation

3. If failures, suggest fixes based on error messages.
