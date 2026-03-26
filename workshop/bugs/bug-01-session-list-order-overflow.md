# Bug 01: Session List Grows Without Bound and Shows Oldest First

## Description

The Today summary panel renders sessions in the order they were created (oldest at top) and has
no maximum height or scroll. After several sessions the list pushes all content below it off
screen with no way to scroll within the panel.

## Symptom

1. Complete or stop several sessions in quick succession.
2. **Actual**: The session list expands indefinitely downward; the oldest session is at the top;
   no scroll bar appears inside the panel.
3. **Expected**: The list is capped at a fixed height with an internal scroll bar, and the
   most recent session appears at the top.

## Spec Reference

- **US4 Acceptance**: "Today panel shows a scrollable list of all sessions, most recent first."
- **contracts/sessions-api.md** `GET /sessions/today`: sessions are returned oldest-first from
  the API — the frontend is responsible for reversing the display order.

## Root Cause

Two separate issues:

1. **Order**: `TodaySummary.tsx` renders `sessions.map(...)` as-is; the API returns sessions in
   ascending `start_at` order, so the oldest appears first.
2. **Overflow**: `.session-list` in `index.css` has no `max-height` or `overflow-y` rule, so
   the list grows the page rather than scrolling internally.

## Affected Files

- `frontend/src/components/TodaySummary.tsx` — reverse the sessions array before rendering.
- `frontend/src/index.css` — add `max-height` and `overflow-y: auto` to `.session-list`.

## Fix Hint

In `TodaySummary.tsx`, spread and reverse: `[...sessions].reverse().map(...)`.  
In `index.css`, add `max-height: 18rem; overflow-y: auto;` to `.session-list`.

---

## Workshop Exercise

Work through the steps below in order. Each step tells you **what speckit command to run**,
**what to type**, and **what to do with the output**.

This bug fix uses the same full specification pipeline as a new feature:
`/speckit.clarify` → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
— speckit handles everything including writing tests, applying the fix, and running verification.

Speckit will automatically create the branch `workshop/bug-01-session-list-order-overflow` and
save spec artifacts to `specs/bug-01-session-list-order-overflow/` when you run the first command below.

---

### Step 1 — Reproduce the bug
Understand what is currently going on first by reproducing the bug.

1. Start the backend: `cd backend && uvicorn src.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Click **Start**, then immediately **Stop** — repeat 8–10 times to generate several sessions.
4. **Observe**:
   - Sessions are listed oldest-first (earliest time at the top).
   - The page scrolls rather than the list panel.

---

### Step 2 — Clarify the intended behaviour (`/speckit.clarify`)

Before touching any code, use `/speckit.clarify` to ask the spec targeted questions about
how the session list should look and behave.

**Run this command:**
```
/speckit.clarify
```

**When prompted, describe the gap you found:**
> "The Today summary lists sessions with the oldest at the top and no scroll. I need to
> confirm: what sort order should the session list use in the UI, and should the list have
> a maximum visible height so it doesn't push content off the page?"

**What to look for in the output:**
- Confirmation that the UI must display sessions **most recent first** (descending), even
  though the API returns them ascending.
- Confirmation that the panel must be scrollable when there are many sessions — the page
  layout must not be disturbed by a long list.

---

### Step 3 — Write a mini-spec for the fix (`/speckit.specify`)

Use `/speckit.specify` to express the corrected behaviour as a user story with testable
acceptance criteria.

**Run this command:**
```
/speckit.specify
```

**Describe the behaviour you want to enforce:**
> "As a user reviewing today's sessions, the most recent session should appear at the top of
> the list so I can see what I just finished without scrolling. If I have many sessions, the
> list must stay within the panel with an internal scroll bar rather than growing the page."

**What to look for in the output:**
- An acceptance criterion such as: *"Given sessions A (09:00) and B (09:30), B is rendered
  before A in the list."*
- A second criterion: *"Given more sessions than fit in the panel, a scroll bar appears within
  the list container, not on the page."*
- Use these as your test assertions in Step 4.

---

### Step 4 — Create the implementation plan (`/speckit.plan`)

Use `/speckit.plan` to translate the spec into a technical design before breaking it into tasks.

**Run this command:**
```
/speckit.plan
```

**What to look for in the output:**
- A `plan.md` written to your spec directory.
- Identification of the two affected files: `TodaySummary.tsx` (display order) and `index.css`
  (height constraint and overflow scroll).
- Confirmation that no backend changes are required — sessions are already persisted and
  returned correctly by `GET /sessions/today`; this is a pure display-layer fix.

---

### Step 5 — Generate implementation tasks (`/speckit.tasks`)

Use `/speckit.tasks` to break the plan into ordered, concrete implementation steps.

**Run this command:**
```
/speckit.tasks
```

**What to look for in the output:**
- A numbered `tasks.md` covering at minimum: reversing the sessions array in `TodaySummary.tsx`,
  adding the `max-height` and `overflow-y` rules to `.session-list` in `index.css`, and writing
  the two tests that verify ordering and scroll containment.
- Tasks ordered so tests are written before implementation changes.

---

### Step 6 — Implement the fix (`/speckit.implement`)

Use `/speckit.implement` to execute every task in `tasks.md` automatically — writing the
failing tests, applying the code changes, and running all verification checks.

**Run this command:**
```
/speckit.implement
```

**What to look for in the output:**
- Tests written first and confirmed failing, then the fix applied.
- `TodaySummary.tsx` updated to reverse the sessions array.
- `.session-list` in `index.css` updated with `max-height` and `overflow-y: auto`.
- All checks green at the end: `npm test`, `npm run typecheck`, `npm run lint`.


### Step 7 - Verify the results
**Verify manually:**
1. Reload the app in the browser.
2. Create 8–10 sessions by clicking **Start** then **Stop** in quick succession.
3. Confirm the most recent session appears **at the top** of the list.
4. Confirm a scroll bar appears **inside the panel** — not on the page — once the list overflows.

All checks must be green before the exercise is complete.

