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

---

### Step 1 — Clarify the intended behaviour (`/speckit.clarify`)

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

### Step 2 — Write a mini-spec for the fix (`/speckit.specify`)

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

### Step 3 — Reproduce the bug

1. Start the backend: `cd backend && uvicorn src.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Click **Start**, then immediately **Stop** — repeat 8–10 times to generate several sessions.
4. **Observe**:
   - Sessions are listed oldest-first (earliest time at the top).
   - The page scrolls rather than the list panel.

---

### Step 4 — Write failing tests

Open `frontend/src/components/__tests__/TodaySummary.test.tsx` and add these two tests:

```tsx
it('renders most recent session first', () => {
  const older = { ...completedSession, id: 1, start_at: '2026-01-01T09:00:00' };
  const newer = { ...completedSession, id: 2, start_at: '2026-01-01T09:30:00' };
  render(<TodaySummary sessions={[older, newer]} totalFocusedMinutes={50} />);
  const rows = screen.getAllByRole('listitem');
  expect(rows[0]).toHaveTextContent('09:30');  // newer first
  expect(rows[1]).toHaveTextContent('09:00');
});

it('session list has overflow scroll styling', () => {
  render(<TodaySummary sessions={[completedSession]} totalFocusedMinutes={25} />);
  const list = screen.getByRole('list');
  expect(list).toHaveClass('session-list');
  // Snapshot or style check — the class must exist and CSS must cap the height
});
```

Run to confirm they **fail**:
```bash
cd frontend && npm test
```

---

### Step 5 — Apply the fix

**`frontend/src/components/TodaySummary.tsx`** — reverse sessions before rendering:

```tsx
<ul className="session-list" aria-label="Today's sessions">
  {[...sessions].reverse().map((s) => (   // ← spread + reverse
    <SessionRow key={s.id} session={s} />
  ))}
</ul>
```

**`frontend/src/index.css`** — cap the list height and enable internal scroll:

```css
.session-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 18rem;     /* ← add */
  overflow-y: auto;      /* ← add */
}
```

---

### Step 6 — Verify

```bash
# Frontend tests (must show your new tests passing)
cd frontend && npm test

# Type check
npm run typecheck

# Lint
npm run lint
```

All checks must be green before the exercise is complete.

