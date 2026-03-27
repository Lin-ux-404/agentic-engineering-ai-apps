# Tasks: Automatic Break Countdown

**Input**: Design documents from `/specs/002-auto-break-timer/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/breaks.openapi.yaml ✅, quickstart.md ✅

**Tests**: Not included — tests were not explicitly requested for this task generation run.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend: Python 3.11 / FastAPI 0.110 / Pydantic 2.6 / aiosqlite 0.20
- Frontend: TypeScript 5.5 / React 18 / Zustand 4.5 / Vite 5

---

## Phase 1: Setup (Schema & Models)

**Purpose**: Extend the database schema and typed models to support break countdown records before any feature logic is added.

- [x] T001 Add `breaks` table to `backend/src/database.py` — add a `CREATE TABLE IF NOT EXISTS breaks` statement inside the existing `init_db()` function with columns: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `session_id INTEGER NOT NULL UNIQUE REFERENCES sessions(id)`, `start_at TEXT NOT NULL`, `expected_end_at TEXT NOT NULL`, `configured_minutes INTEGER NOT NULL CHECK(configured_minutes BETWEEN 1 AND 120)`, `status TEXT NOT NULL CHECK(status IN ('active','skipped','finished')) DEFAULT 'active'`, `skipped_at TEXT`, `finished_at TEXT`, `date_key TEXT NOT NULL`; also create a partial unique index `CREATE UNIQUE INDEX IF NOT EXISTS uix_breaks_single_active ON breaks(status) WHERE status = 'active'` to enforce at most one active break at a time
- [x] T002 [P] Add `BreakCountdownResponse` Pydantic model and update settings validation range in `backend/src/models.py` — add a new `BreakCountdownResponse(BaseModel)` class with fields: `id: int`, `session_id: int`, `start_at: str`, `expected_end_at: str`, `configured_minutes: int = Field(ge=1, le=120)`, `remaining_seconds: float`, `status: Literal['active', 'skipped', 'finished']`, `skipped_at: str | None = None`, `finished_at: str | None = None`; also change the existing `SettingsRequest.break_minutes` field constraint from `ge=1` to `ge=0` so zero-duration breaks are accepted per FR-011 and the contract `SettingsRequest` schema
- [x] T003 [P] Add `BreakCountdownResponse` TypeScript interface to `frontend/src/api/types.ts` — add `export interface BreakCountdownResponse { id: number; session_id: number; start_at: string; expected_end_at: string; configured_minutes: number; remaining_seconds: number; status: 'active' | 'skipped' | 'finished'; skipped_at: string | null; finished_at: string | null; }` matching the OpenAPI `BreakCountdownResponse` schema in `contracts/breaks.openapi.yaml`

---

## Phase 2: Foundational (Service & Router Infrastructure)

**Purpose**: Create the breaks service and router skeleton that all user stories will extend. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Create `backend/src/services/breaks_service.py` with `get_active_break()` — create the new module importing `aiosqlite`, `datetime`, and the `BreakCountdownResponse` model; implement `async def get_active_break(db: aiosqlite.Connection) -> BreakCountdownResponse | None` that executes `SELECT * FROM breaks WHERE status = 'active' LIMIT 1`; if a row is found and `datetime.utcnow() >= expected_end_at`, update the row to `status='finished', finished_at=utcnow()` and return the response with `remaining_seconds=0.0`; otherwise compute `remaining_seconds = max(0, (expected_end_at - utcnow).total_seconds())` and return the hydrated `BreakCountdownResponse`; return `None` if no active break exists; parse all timestamps as ISO-8601 UTC strings consistent with the existing `session_service.py` patterns
- [x] T005 Create `backend/src/routers/breaks.py` with `GET /breaks/active` endpoint — create a new FastAPI `APIRouter(tags=["breaks"])`; implement `@router.get("/active")` that obtains the database connection from the existing `get_db` dependency (same pattern as `routers/sessions.py`), calls `breaks_service.get_active_break(db)`, and returns the `BreakCountdownResponse | None` result directly (FastAPI serializes `None` as JSON `null`)
- [x] T006 Register breaks router in `backend/src/main.py` — add `from .routers import breaks` alongside the existing session/settings imports; add `app.include_router(breaks.router, prefix="/api/breaks")` following the existing `include_router` pattern for sessions and settings

**Checkpoint**: Foundation ready — breaks table exists, active-break endpoint responds, user story implementation can now begin

---

## Phase 3: User Story 1 — Start Break Automatically (Priority: P1) 🎯 MVP

**Goal**: When a focus session completes, automatically create and display a break countdown using the configured break duration, with no additional user action required.

**Independent Test**: Complete a focus session with `break_minutes > 0` configured and confirm the app automatically transitions to a visible break countdown showing the correct remaining time without any extra clicks.

### Implementation for User Story 1

- [x] T007 [US1] Implement `create_break()` in `backend/src/services/breaks_service.py` — add `async def create_break(db: aiosqlite.Connection, session_id: int, break_minutes: int) -> BreakCountdownResponse` that computes `start_at = datetime.utcnow().isoformat() + 'Z'`, `expected_end_at = (utcnow + timedelta(minutes=break_minutes)).isoformat() + 'Z'`, `date_key = date.today().isoformat()`; inserts into the `breaks` table with `status='active'`; retrieves the new row's `id` via `cursor.lastrowid`; returns a hydrated `BreakCountdownResponse` with `remaining_seconds = break_minutes * 60`; use the same ISO-8601 UTC format and `db.execute` + `db.commit` pattern used in `session_service.py`
- [x] T008 [US1] Trigger break creation on session completion in `backend/src/services/session_service.py` — in the `complete()` function (and in the auto-complete branch of `get_active_with_auto_complete()` where `status` is set to `'completed'`), after the session row is updated to `completed`: query `SELECT break_minutes FROM settings WHERE id = 1` to read the current break duration; if `break_minutes > 0`, call `await breaks_service.create_break(db, session_id, break_minutes)`; import `breaks_service` from `..services`; this implements FR-001 (auto-transition) and FR-002 (use configured duration at completion time); the `break_minutes = 0` case is handled by simply not creating a break, satisfying FR-011
- [x] T009 [US1] Add break state fields and break hydration to `frontend/src/hooks/useTimerService.ts` — extend the Zustand store state type to add: `breakId: number | null` (init `null`), `breakStartAt: number | null` (Unix ms, init `null`), `breakExpectedEndAt: number | null` (Unix ms, init `null`), `breakConfiguredSeconds: number | null` (init `null`); expand the `status` type union to include `'break'`; in `hydrate()`, after the existing active-session fetch, call `apiFetch<BreakCountdownResponse | null>('/breaks/active')`; if the response is non-null and `status === 'active'`, set the break fields from the response (parse ISO strings to Unix ms), set `remainingSeconds` to `response.remaining_seconds`, and set `status` to `'break'`; also add a `clearBreak()` internal helper that resets all four break fields to `null`; import `BreakCountdownResponse` from `../api/types`
- [x] T010 [US1] Extend `tick()` in `frontend/src/hooks/useTimerService.ts` to handle break countdown — inside `tick()`, add a branch: if `status === 'break'` and `breakExpectedEndAt !== null`, compute `remainingSeconds = Math.max(0, Math.round((breakExpectedEndAt - Date.now()) / 1000))`; update `remainingSeconds` in the store; this uses wall-clock timestamps (not tick counting) to satisfy FR-009 and the constitution's predictable-recovery requirement; the existing 200ms tick interval provides smooth UI updates
- [x] T011 [P] [US1] Update `frontend/src/components/TimerDisplay.tsx` to display break countdown — add a case for `status === 'break'` that renders the `remainingSeconds` value in the existing `MM:SS` format; change the status label to `'Break'`; keep the existing `aria-live="polite"` region so screen readers announce the break state per the accessibility constitution check; the component reads from the same `useTimerService` store — no new data source needed
- [x] T012 [P] [US1] Update `frontend/src/components/Controls.tsx` to suppress focus-session controls during break — add `status === 'break'` to the conditional rendering logic so that when a break is active, the Start, Pause, Resume, and Stop buttons are not displayed; this prevents focus-session actions during the break period per FR-003; in this phase the break status shows no action buttons — the Skip button is added in US2

**Checkpoint**: User Story 1 is complete — a completed focus session automatically starts a visible break countdown with correct remaining time. The app clearly shows break state and suppresses focus controls.

---

## Phase 4: User Story 2 — Skip Break Early (Priority: P2)

**Goal**: Allow the user to end an active break before the countdown finishes and immediately return to a ready-to-start state.

**Independent Test**: Start an automatic break after a completed focus session, click/press "Skip break" before the countdown ends, and confirm the app immediately ends the break and shows the Start button for the next focus session.

### Implementation for User Story 2

- [x] T013 [US2] Implement `skip_break()` in `backend/src/services/breaks_service.py` — add `async def skip_break(db: aiosqlite.Connection, break_id: int) -> BreakCountdownResponse` that executes `SELECT * FROM breaks WHERE id = ?`; if no row found, raise `HTTPException(404)`; if `row['status'] != 'active'`, raise `HTTPException(409, detail='Break is not active')`; execute `UPDATE breaks SET status = 'skipped', skipped_at = ? WHERE id = ?` with `utcnow()` ISO string; compute `remaining_seconds = 0.0`; return the updated `BreakCountdownResponse`; import `HTTPException` from `fastapi`
- [x] T014 [US2] Add `POST /breaks/{break_id}/skip` endpoint to `backend/src/routers/breaks.py` — add `@router.post("/{break_id}/skip")` that accepts `break_id: int` as a path parameter, obtains the DB connection, calls `await breaks_service.skip_break(db, break_id)`, and returns the `BreakCountdownResponse`; FastAPI will propagate the 404/409 `HTTPException` raised by the service
- [x] T015 [US2] Add `skipBreak()` action to `frontend/src/hooks/useTimerService.ts` — add `skipBreak: async () => void` to the store actions; implementation: if `breakId` is null, return early; call `await apiFetch<BreakCountdownResponse>(\`/breaks/${breakId}/skip\`, { method: 'POST' })`; on success, call `clearBreak()`, set `status` to `'idle'`, set `remainingSeconds` to `null`; call `loadToday()` to refresh session summary; wrap in try/catch for network errors consistent with existing action patterns
- [x] T016 [US2] Add keyboard-accessible "Skip break" button to `frontend/src/components/Controls.tsx` — when `status === 'break'`, render a `<button>` element with text `Skip break` that calls `skipBreak()` from the store; use a native `<button>` element (not a div/span) for keyboard accessibility; the button should only be present/visible when break is active, satisfying FR-005, FR-010, and the accessibility constitution check; style consistently with existing control buttons

**Checkpoint**: User Story 2 is complete — the user can skip an active break via a keyboard-accessible button, and the app immediately returns to idle/ready state.

---

## Phase 5: User Story 3 — Finish Break and Resume Readiness (Priority: P3)

**Goal**: When the break countdown reaches zero (either in real-time or discovered on return), the app marks the break as finished and clearly returns to a ready-to-start state.

**Independent Test**: Let an automatic break countdown reach zero and confirm the app stops showing the break, does not display negative or stale time, and the Start button reappears for the next focus session.

### Implementation for User Story 3

- [x] T017 [US3] Handle break natural expiry in `frontend/src/hooks/useTimerService.ts` `tick()` — in the `status === 'break'` branch of `tick()` (added in T010), add: when computed `remainingSeconds <= 0`, call `clearBreak()`, set `status` to `'idle'`, set `remainingSeconds` to `null`; also fire a background `apiFetch<BreakCountdownResponse | null>('/breaks/active')` to trigger the backend's auto-finish logic in `get_active_break()` (which transitions expired breaks to `finished` on read); this ensures FR-007 is satisfied — the break ends at zero and the app returns to ready state
- [x] T018 [US3] Handle already-expired break during hydration in `frontend/src/hooks/useTimerService.ts` — in `hydrate()`, after calling `GET /api/breaks/active`: if the response is `null` (backend returned no active break because it auto-finished an expired one), ensure the store is in `idle` status with break fields cleared; if the response has `status === 'finished'`, also clear break state and set `idle`; this covers the case where the user returns to the app after the break has already expired (tab switch, page reload) and satisfies FR-009's accuracy requirement
- [x] T019 [P] [US3] Update `frontend/src/components/TimerDisplay.tsx` to prevent stale break display — ensure that when `status` transitions away from `'break'` (to `'idle'`), the component does not flash negative remaining time or a stale "Break" label; if `remainingSeconds` is `null` or `0` and `status !== 'break'`, render the idle display (e.g., configured focus time or `00:00`); this satisfies acceptance scenario US3-2: "the app does not continue showing an expired countdown"

**Checkpoint**: All three user stories are independently functional — breaks auto-start (US1), can be skipped (US2), and complete naturally (US3) with clean transitions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge-case hardening, accessibility verification, and end-to-end validation across all stories.

- [x] T020 Verify zero-duration break bypass end-to-end in `backend/src/services/session_service.py` — confirm that the `break_minutes > 0` guard added in T008 correctly prevents break record creation when `break_minutes = 0`; trace the code path: `complete()` → read settings → `break_minutes == 0` → no `create_break()` call → frontend `hydrate()` sees no active break → stays idle; add an inline comment in `session_service.py` documenting this FR-011 bypass path for future maintainers
- [x] T021 [P] Update `frontend/src/components/SettingsModal.tsx` to allow `break_minutes = 0` — change the break-minutes input's `min` attribute from `1` to `0` so the user can configure a zero-duration break that triggers the FR-011 bypass; update any client-side validation that rejects zero; keep the `max` at `120` consistent with the updated `SettingsRequest` schema
- [x] T022 [P] Ensure visibility-change re-sync covers break state in `frontend/src/hooks/useTimerService.ts` — verify that the existing `visibilitychange` event listener (or equivalent re-sync mechanism) calls `hydrate()` which now includes break-state fetching from T009; if the existing listener only re-syncs session state, extend it to also trigger break hydration so that remaining break time is accurate after a tab switch per FR-009
- [x] T023 [P] Guard skip-break action availability in `frontend/src/components/Controls.tsx` — verify that the "Skip break" button from T016 is not rendered and not keyboard-reachable when `status !== 'break'`; ensure no other status (idle, running, paused, completed, stopped_early) accidentally shows the skip action; this is a defensive check for FR-010
- [x] T024 Run `specs/002-auto-break-timer/quickstart.md` validation scenarios end-to-end — execute Scenario A (auto-start break), Scenario B (skip break), Scenario C (natural finish), Scenario D (zero-duration bypass), and Scenario E (visibility/reload resilience) as described in quickstart.md; verify backend lint (`make lint`), typecheck (`make typecheck`), and frontend lint (`npm run lint`), typecheck (`npm run typecheck`) all pass with the new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (T001 for table, T002 for models) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion (service skeleton, router, registration)
- **US2 (Phase 4)**: Depends on Phase 2 completion; independent of US1 at the code level (extends same service/router files, but adds new functions/endpoints); however, testing US2 requires a running break which is created by US1 logic
- **US3 (Phase 5)**: Depends on Phase 2 completion; independent of US2; testing requires an active break (US1 logic must work)
- **Polish (Phase 6)**: Depends on US1, US2, and US3 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependencies on other stories. **Recommended first.**
- **User Story 2 (P2)**: Can start after Foundational — extends the same files as US1 but adds distinct functions/endpoints. Sequencing after US1 avoids merge conflicts and allows testing the skip flow on real breaks.
- **User Story 3 (P3)**: Can start after Foundational — extends tick() and hydrate() from US1. Sequencing after US1 ensures the break expiry path has a working break to expire.

### Recommended Sequential Order

```text
Phase 1 (T001 → T002 ∥ T003)
  ↓
Phase 2 (T004 → T005 → T006)
  ↓
Phase 3 / US1 (T007 → T008 → T009 → T010 → T011 ∥ T012)
  ↓
Phase 4 / US2 (T013 → T014 → T015 → T016)
  ↓
Phase 5 / US3 (T017 → T018, T019 ∥)
  ↓
Phase 6 / Polish (T020, T021 ∥ T022 ∥ T023, → T024)
```

### Within Each User Story

- Backend service logic before router endpoints
- Frontend store/hook changes before component UI changes
- Core implementation before integration/edge cases

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (Python models vs TypeScript types — different languages and files)
- **Phase 3 (US1)**: T011 and T012 can run in parallel (TimerDisplay.tsx vs Controls.tsx — different component files, both read from store)
- **Phase 5 (US3)**: T019 can run in parallel with T017/T018 (TimerDisplay.tsx is a different file from useTimerService.ts)
- **Phase 6**: T021, T022, and T023 can all run in parallel (SettingsModal.tsx, useTimerService.ts, Controls.tsx — different files, independent concerns)

---

## Parallel Example: User Story 1

```text
# After T010 completes (break state + tick in useTimerService.ts):

# Launch both component updates in parallel:
Task T011: "Update TimerDisplay.tsx for break countdown display"
Task T012: "Update Controls.tsx to suppress focus controls during break"

# These are safe to parallelize because:
# - Different files (TimerDisplay.tsx vs Controls.tsx)
# - Both read from useTimerService store (no writes to each other)
# - No import dependencies between them
```

## Parallel Example: Phase 1 Setup

```text
# After T001 completes (breaks table DDL):

# Launch model tasks in parallel:
Task T002: "Add BreakCountdownResponse Pydantic model in backend/src/models.py"
Task T003: "Add BreakCountdownResponse TypeScript type in frontend/src/api/types.ts"

# These are safe to parallelize because:
# - Different languages (Python vs TypeScript)
# - Different project directories (backend/ vs frontend/)
# - Both define the same contract shape independently
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (3 tasks)
3. Complete Phase 3: User Story 1 (6 tasks)
4. **STOP and VALIDATE**: A completed focus session should automatically start a visible break countdown
5. The break ticks down but cannot yet be skipped (US2) or cleanly finish (US3 transition) — partial but demonstrable

### Incremental Delivery

1. Setup + Foundational (6 tasks) → Schema and infrastructure ready
2. Add User Story 1 (6 tasks) → Breaks auto-start after focus completion → **MVP!**
3. Add User Story 2 (4 tasks) → Users can skip breaks → Fully interactive
4. Add User Story 3 (3 tasks) → Breaks finish naturally with clean transitions → Feature complete
5. Polish (5 tasks) → Edge cases, zero-duration bypass, validation → Production ready
6. Each story adds value without breaking previous stories

### File Change Summary

| File | Tasks | Changes |
|------|-------|---------|
| `backend/src/database.py` | T001 | Add breaks table DDL |
| `backend/src/models.py` | T002 | Add BreakCountdownResponse, update SettingsRequest |
| `backend/src/services/breaks_service.py` | T004, T007, T013 | New file: get_active, create, skip |
| `backend/src/routers/breaks.py` | T005, T014 | New file: GET active, POST skip |
| `backend/src/main.py` | T006 | Register breaks router |
| `backend/src/services/session_service.py` | T008, T020 | Trigger break on complete |
| `frontend/src/api/types.ts` | T003 | Add BreakCountdownResponse type |
| `frontend/src/hooks/useTimerService.ts` | T009, T010, T015, T017, T018, T022 | Break state, tick, skip, expiry, hydrate |
| `frontend/src/components/TimerDisplay.tsx` | T011, T019 | Break display, expiry transition |
| `frontend/src/components/Controls.tsx` | T012, T016, T023 | Suppress focus controls, skip button |
| `frontend/src/components/SettingsModal.tsx` | T021 | Allow break_minutes=0 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete sibling tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after Foundational phase
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- All timer state is derived from wall-clock timestamps (constitution Principle II)
- The frontend `useTimerService.ts` remains the single source of truth for UI timer state (constitution Principle IX)
- Backend `breaks_service.get_active_break()` auto-finishes expired breaks on read — no separate cron or background job needed
