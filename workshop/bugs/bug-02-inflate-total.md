# Bug 02: Today's Total Includes Active Session Time

## Description

The "Today: X min focused" total inflates over time because the running session's *current*
elapsed time is counted even though it hasn't been completed yet.

## Symptom

1. Start a 25-minute session.
2. Let 10 minutes elapse.
3. Open the Today summary panel.
4. **Actual**: Total shows ~10 min (and keeps climbing while the session runs).
5. **Expected**: Total shows 0 min — active sessions should not count until they reach a
   terminal state (`completed` or `stopped_early`).

## Spec Reference

- **FR-018**: The today summary total MUST only include sessions in terminal states.
- **contracts/sessions-api.md** `GET /sessions/today`: `total_focused_minutes` is described as
  "active session excluded from total".

## Root Cause

`session_service.get_today()` includes rows with `status IN ('running', 'paused')` in the
`SUM(focused_seconds)` computation. Because `focused_seconds` is `NULL` while active, the
SQL sum is zero — **but** the service computes elapsed seconds for active rows on-the-fly
instead of reading the column, causing the total to grow.

## Affected File

`backend/src/services/session_service.py` — `get_today()` function.

## Fix Hint

Filter the `total_focused_minutes` calculation to `status IN ('completed', 'stopped_early')`
only. Active sessions must be included in the *session list* but excluded from the *total*.

---

## Workshop Exercise

Work through the steps below in order. Each step tells you **what speckit command to run**,
**what to type**, and **what to do with the output**.

---

### Step 1 — Clarify the intended behaviour (`/speckit.clarify`)

Use `/speckit.clarify` to interrogate the spec about what "today's total" should and should
not include. This surfaces the exact requirement before you touch any code.

**Run this command:**
```
/speckit.clarify
```

**When prompted, describe the ambiguity:**
> "The Today summary shows a total of focused minutes. I need to confirm: should a currently
> running or paused session count toward today's total, and if not, which session statuses
> are allowed to contribute?"

**What to look for in the output:**
- The clarifying answers should reference FR-018 and the `GET /sessions/today` contract.
- Confirm: only `completed` and `stopped_early` sessions contribute to `total_focused_minutes`.
- Active (`running`, `paused`) sessions must appear in the session list but with a zero
  or null contribution to the total.

---

### Step 2 — Write a mini-spec for the fix (`/speckit.specify`)

Use `/speckit.specify` to encode the corrected rule as a precise user story.

**Run this command:**
```
/speckit.specify
```

**Describe the behaviour you want to enforce:**
> "As a user reviewing today's summary, the total focused minutes should only count sessions
> I have fully completed or explicitly stopped — not sessions I'm currently in — so the
> number I see is a reliable reflection of work already done, not a live estimate."

**What to look for in the output:**
- An acceptance criterion along the lines of: *"Given a running session with 10 minutes
  elapsed, `GET /sessions/today` returns `total_focused_minutes: 0`."*
- Use this criterion verbatim as your test assertion in Step 4.

---

### Step 3 — Reproduce the bug

1. Make sure the backend is running: `cd backend && uvicorn src.main:app --reload`
2. Start a session via the UI (or via curl):
   ```bash
   curl -X POST http://127.0.0.1:8000/sessions/start \
        -H "Content-Type: application/json" \
        -d '{"configured_minutes": 25}'
   ```
3. Immediately call `GET /sessions/today`:
   ```bash
   curl http://127.0.0.1:8000/sessions/today
   ```
4. Wait ~60 seconds and call it again.
5. **Observe**: `total_focused_minutes` is > 0 and grows over time.

---

### Step 4 — Write a failing test

Open `backend/tests/test_sessions.py` and add:

```python
@pytest.mark.asyncio
async def test_active_session_excluded_from_today_total(client):
    """Running session must NOT contribute to today's total."""
    await client.post("/sessions/start", json={"configured_minutes": 25})
    resp = await client.get("/sessions/today")
    assert resp.json()["total_focused_minutes"] == 0
```

Run the tests to confirm it **fails**:
```bash
cd backend && pytest tests/ -v -k "excluded_from_today"
```

---

### Step 5 — Apply the fix

In `backend/src/services/session_service.py`, locate the `get_today()` function and update
the total calculation so it only sums sessions in terminal states:

```python
total_seconds = sum(
    (s.focused_seconds or 0)
    for s in sessions
    if s.status in ("completed", "stopped_early")  # ← only terminal
)
```

---

### Step 6 — Verify

```bash
# All backend tests must pass
cd backend && pytest tests/ -v

# Lint + type checks
ruff check src/ tests/ && mypy src/
```

All checks must be green before the exercise is complete.

