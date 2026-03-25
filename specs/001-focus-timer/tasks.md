---
description: "Task list for Personal Focus Timer (Workday Pomodoro)"
---

# Tasks: Personal Focus Timer (Workday Pomodoro)

**Input**: Design documents from `/specs/001-focus-timer/`
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/ ✅ · quickstart.md ✅

**Tests**: Tests are included — the feature specification and workshop requirements explicitly require
test coverage of all critical paths (timer lifecycle, persistence, API contract compliance).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.
Workshop bug tasks (Phase 9) are intentionally placed last as they modify working code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in every description

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/src/components/__tests__/`
- **Workshop**: `workshop/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the monorepo, scaffold both projects, configure tooling, and add CI.

- [x] T001 Initialize repository structure: create `frontend/`, `backend/`, `workshop/` folders and root `README.md`
- [x] T002 Scaffold Vite + React + TypeScript frontend app in `frontend/` with `tsconfig.json` (`strict: true`, `noUncheckedIndexedAccess: true`)
- [x] T003 Scaffold FastAPI backend in `backend/` with `backend/src/main.py` (GET `/health` → `{"status": "ok"}`) and `pyproject.toml` / `requirements.txt`
- [x] T004 [P] Configure frontend tooling in `frontend/`: ESLint (TypeScript rules), Prettier, `npm run lint`, `npm run typecheck` (`tsc --noEmit`)
- [x] T005 [P] Configure backend tooling in `backend/`: `ruff` (lint + format), `mypy` (strict), `pytest`, `pytest-asyncio`, `httpx`; add `make lint` and `make test` targets
- [x] T006 Add GitHub Actions CI workflow in `.github/workflows/ci.yml` running `npm run lint && npm run typecheck && npm test` (frontend) and `ruff check && mypy && pytest` (backend) on every push

**Checkpoint**: Both projects scaffold and toolchain pass lint + typecheck with empty test suites.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, DB access layer, Pydantic models, FastAPI app wiring, and frontend
store/client scaffolding that MUST be complete before any user story implementation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Define SQLite DDL (sessions table, settings table, partial unique index `idx_one_active_session`) in `backend/src/database.py` per data-model.md schema
- [x] T008 [P] Implement `aiosqlite` connection factory (`get_db` context manager) and `init_db()` function (creates tables + seeds default settings row) in `backend/src/database.py`
- [x] T009 [P] Define all Pydantic models (`SessionStartRequest`, `ActiveSessionResponse`, `SessionSummaryResponse`, `TodayResponse`, `SettingsRequest`, `SettingsResponse`, `ErrorResponse`) in `backend/src/models.py` per contracts/
- [x] T010 Register session and settings routers, configure CORS (`allow_origins=["http://localhost:5173"]`), and `lifespan` → `init_db()` call in `backend/src/main.py`
- [x] T011 [P] Create backend test fixture in `backend/tests/conftest.py`: in-memory SQLite DB, async test client (`httpx.AsyncClient`), `pytest-asyncio` config
- [x] T012 Scaffold Zustand store shell (`TimerState` interface, initial state, `useTimerStore`) in `frontend/src/hooks/useTimerService.ts` — state shape only, no actions yet
- [x] T013 [P] Implement typed fetch API client wrapper (`apiFetch`, `ApiError`) with offline detection (catches `TypeError: Failed to fetch`) in `frontend/src/api/client.ts`
- [x] T014 [P] Install `zustand` and `openapi-typescript`; add `"generate:types"` npm script (`openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api/schema.ts`) in `frontend/package.json`

**Checkpoint**: Backend starts, `/health` returns 200, `init_db()` creates both tables. Frontend compiles with no errors.

---

## Phase 3: User Story 1 — Start and Complete a Focus Session (Priority: P1) 🎯 MVP

**Goal**: User can start a session, see a live countdown, leave and return with correct remaining time,
and let the session auto-complete when the countdown reaches zero. Today panel shows the completed session.

**Independent Test**: Start the app, press Start, switch tabs for 60 seconds, return and verify countdown
is accurate, wait for full session to expire, verify "Completed" row appears in today panel with correct
focused_seconds.

### Implementation for User Story 1

- [x] T015 [P] [US1] Implement `session_service.start()` (enforces single-active constraint, inserts session row, returns `ActiveSessionResponse`) in `backend/src/services/session_service.py`
- [x] T016 [P] [US1] Implement `session_service.complete()` (writes `status=completed`, `end_at`, `focused_seconds=elapsed-paused_seconds`) and `get_active_with_auto_complete()` (auto-complete if `remaining_seconds <= 0 and status=running`) in `backend/src/services/session_service.py`
- [x] T017 [US1] Implement `GET /sessions/active` router (calls `get_active_with_auto_complete`, returns `ActiveSessionResponse | null`) in `backend/src/routers/sessions.py`
- [x] T018 [US1] Implement `POST /sessions/start` router (201 Created / 409 Conflict) in `backend/src/routers/sessions.py`
- [x] T019 [US1] Implement `POST /sessions/{id}/complete` router (idempotency guard: 409 if not `running`) in `backend/src/routers/sessions.py`
- [x] T020 [US1] Implement `GET /sessions/today` router (`session_service.get_today()` — `FLOOR(SUM(focused_seconds)/60)`, ordered by `start_at`, active session excluded from total) in `backend/src/routers/sessions.py`
- [x] T021 [US1] Add API tests for US1 in `backend/tests/test_sessions.py`: start → active returns session; auto-complete on GET when remaining ≤ 0; today total is correct; 409 on double-start; complete is idempotent
- [x] T022 [US1] Implement `useTimerService` state machine (`idle → running → completed`), 200 ms `setInterval` tick (remaining = `configuredSeconds - elapsed + pausedSeconds`), and `hydrate()` call on mount from `GET /sessions/active` in `frontend/src/hooks/useTimerService.ts`
- [x] T023 [US1] Implement `TimerDisplay` component (mm:ss countdown, state label "Idle" / "Running" / "Completed", `aria-live="polite"`) in `frontend/src/components/TimerDisplay.tsx`
- [x] T024 [US1] Implement `Controls` component with "Start" (idle) and "Stop" (running) as primary CTAs; each button has descriptive `aria-label`; dispatches via `useTimerService` in `frontend/src/components/Controls.tsx`
- [x] T025 [US1] Implement `TodaySummary` component: total focused minutes header and empty-state message ("No sessions yet today"); reads from `useTimerService.todaySessions` in `frontend/src/components/TodaySummary.tsx`
- [x] T026 [US1] Wire `App.tsx` root layout: offline banner (hidden initially), `TimerDisplay`, `Controls`, `TodaySummary` in `frontend/src/App.tsx`
- [x] T027 [US1] Add component tests for US1 in `frontend/src/components/__tests__/`: `TimerDisplay` renders idle/running states; `TodaySummary` renders empty state and loaded session list

**Checkpoint**: US1 fully functional — start, auto-complete, today panel updates, page refresh restores running session.

---

## Phase 4: User Story 2 — Pause and Resume a Session (Priority: P2)

**Goal**: User can pause a running session, the countdown freezes, and on resume the countdown
continues. Focused_seconds in the final record excludes all paused time.

**Independent Test**: Start session, wait 2 min, press Pause, wait 3 min, press Resume, let complete.
Verify `focused_seconds ≈ 1500` (25 min) not `1500 + 180`.

### Implementation for User Story 2

- [x] T028 [P] [US2] Implement `session_service.pause()` (validates `status=running`, sets `paused_at=now`) in `backend/src/services/session_service.py`
- [x] T029 [P] [US2] Implement `session_service.resume()` (validates `status=paused`, adds `now - paused_at` to `paused_seconds`, clears `paused_at`) in `backend/src/services/session_service.py`
- [x] T030 [US2] Implement `POST /sessions/{id}/pause` router (409 if not `running`) in `backend/src/routers/sessions.py`
- [x] T031 [US2] Implement `POST /sessions/{id}/resume` router (409 if not `paused`) in `backend/src/routers/sessions.py`
- [x] T032 [US2] Add API tests for US2 in `backend/tests/test_sessions.py`: pause freezes remaining; resume restores; focused_seconds excludes pause duration; paused state survives GET /sessions/active; resume on non-paused → 409
- [x] T033 [US2] Extend `useTimerService` with `paused` state: frozen countdown (remaining pinned at pause snapshot), optimistic pause/resume dispatch, `paused_at` tracking in `frontend/src/hooks/useTimerService.ts`
- [x] T034 [US2] Add Pause and Resume buttons to `Controls` component: Pause shown when `running`, Resume shown when `paused`; both have `aria-label` in `frontend/src/components/Controls.tsx`
- [x] T035 [US2] Add component tests for US2 in `frontend/src/components/__tests__/Controls.test.tsx`: pause button appears when running; countdown freezes on pause; resume button appears when paused; countdown resumes

**Checkpoint**: US2 fully functional — pause/resume works, focused_seconds is accurate, Paused state survives page refresh.

---

## Phase 5: User Story 3 — Stop a Session Early (Priority: P3)

**Goal**: User can stop a running or paused session at any time. Session saved as "Stopped early" with
accurate focused_seconds. App returns to idle state ready for a new session.

**Independent Test**: Start session, press Stop after 8 min. Verify `stopped_early` row in today panel
with `focused_seconds ≈ 480`, app returns to idle, new session can immediately start.

### Implementation for User Story 3

- [x] T036 [US3] Implement `session_service.stop_early()` (validates status is `running` or `paused`; finalizes any open pause interval; sets `status=stopped_early`, `end_at`, `focused_seconds`) in `backend/src/services/session_service.py`
- [x] T037 [US3] Implement `POST /sessions/{id}/stop` router (409 if session already in terminal state) in `backend/src/routers/sessions.py`
- [x] T038 [US3] Add API tests for US3 in `backend/tests/test_sessions.py`: stop from running → stopped_early; stop from paused → correct focused_seconds; stop on terminal → 409; new session can start after stop
- [x] T039 [US3] Extend `useTimerService` with `stopped_early` transition: dispatch `stop()`, reset store to idle on success in `frontend/src/hooks/useTimerService.ts`
- [x] T040 [US3] Add Stop button to `Controls` component rendered in both `running` and `paused` states; Stop is always secondary to Pause/Resume in `frontend/src/components/Controls.tsx`
- [x] T041 [US3] Add component tests for US3 in `frontend/src/components/__tests__/Controls.test.tsx`: Stop available in running/paused states; after stop, app is idle; "Stopped early" label visible in TodaySummary

**Checkpoint**: US3 fully functional — any session can be stopped early cleanly with accurate records.

---

## Phase 6: User Story 4 — Review Today's Focus Summary (Priority: P4)

**Goal**: Today panel shows the correct total focused minutes and a full list of individual sessions
(start time, focused duration, status, optional note). Resets for a new calendar day.

**Independent Test**: Record two completed sessions and one stopped-early. Verify total = sum of all
three `focused_seconds / 60` (floored). Verify each session row shows local-time start, duration,
status badge.

### Implementation for User Story 4

- [x] T042 [US4] Verify `session_service.get_today()` in `backend/src/services/session_service.py`: active sessions excluded from total; `date_key` filter correct; result ordered by `start_at` ascending
- [x] T043 [US4] Add API tests for US4 in `backend/tests/test_sessions.py`: zero state returns 0 total; multi-session total arithmetic; note field visible in session list; previous-day sessions excluded via `date_key`
- [x] T044 [US4] Extend `TodaySummary` component with individual session rows: local-time start formatted as HH:mm, focused minutes rounded down, status badge ("Completed" / "Stopped early"), note (if present) in `frontend/src/components/TodaySummary.tsx`
- [x] T045 [US4] Add component tests for US4 in `frontend/src/components/__tests__/TodaySummary.test.tsx`: multi-session list renders; status labels match constitution terminology; note displayed per session; zero-state shows placeholder

**Checkpoint**: US4 fully functional — today panel shows accurate summary, correct labels, correct arithmetic.

---

## Phase 7: User Story 5 — Configure Default Durations (Priority: P5)

**Goal**: User can open settings, change focus and break durations, save, and the next session started
uses the updated duration. Changes survive page refresh.

**Independent Test**: Change focus duration to 50 min, refresh, press Start — countdown begins at 50:00.
Enter "0" and verify validation error; setting is not saved.

### Implementation for User Story 5

- [x] T046 [P] [US5] Implement `settings_service` (GET singleton defaults; UPSERT on PUT; validate `focus_minutes` 1–480, `break_minutes` 1–120) in `backend/src/services/settings_service.py`
- [x] T047 [P] [US5] Implement `GET /settings` and `PUT /settings` routers in `backend/src/routers/settings.py`
- [x] T048 [US5] Add API tests for US5 in `backend/tests/test_settings.py`: GET returns defaults; PUT valid values → 200; PUT invalid (0, negative, >480) → 422; successive GETs return updated value
- [x] T049 [US5] Implement `SettingsModal` component (focus_minutes + break_minutes text inputs, inline validation message on submit, Save/Cancel, keyboard-operable) in `frontend/src/components/SettingsModal.tsx`
- [x] T050 [US5] Load settings on app startup in `useTimerService.ts`; use `settings.focus_minutes` as `configured_minutes` when dispatching Start in `frontend/src/hooks/useTimerService.ts`
- [x] T051 [US5] Add component tests for US5 in `frontend/src/components/__tests__/SettingsModal.test.tsx`: valid save dispatches PUT; invalid input shows validation message; modal closes on cancel; saved values persist on reopen

**Checkpoint**: US5 fully functional — durations configurable, validated, persisted, and applied to new sessions.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility pass, performance audit, Page Visibility API, degraded-mode banner,
and final security verification.

- [x] T052 [P] Accessibility pass — add `aria-label`, `aria-live="polite"` (timer), `role="status"` (state indicator), and visible focus rings to all interactive elements in `frontend/src/components/`
- [x] T053 [P] Performance pass — wrap `TodaySummary` and session list rows in `React.memo`; confirm `useTimerService` subscriptions are slice-based (components only re-render on their slice changing) in `frontend/src/`
- [x] T054 [P] Implement `visibilitychange` listener in `useTimerService.ts` that calls `GET /sessions/active` and overwrites store `remainingSeconds` when tab becomes visible in `frontend/src/hooks/useTimerService.ts`
- [x] T055 [P] Verify backend binds to `127.0.0.1` (not `0.0.0.0`) in `backend/src/main.py` uvicorn startup; verify `allow_origins` is restricted to `["http://localhost:5173"]`
- [x] T056 Implement degraded-mode offline banner in `App.tsx`: renders "Offline — data may not be saved" when `useTimerService.backendReachable === false`; hidden otherwise in `frontend/src/App.tsx`

---

## Phase 9: Workshop Bugs (Intentional, for SDD Exercises)

**Purpose**: Introduce 3 deliberate, realistic defects for workshop participants to reproduce,
spec-first diagnose, and fix. Each bug has a corresponding documentation file in `workshop/bugs/`.

⚠️ **All previous phases must be complete and passing before introducing bugs.**
⚠️ **Bug introductions must be confined to the exact files and lines documented.**

- [x] T057 [P] Introduce Bug 1 (session list order & overflow) — in `TodaySummary.tsx`, render sessions oldest-first (no reverse) and remove `max-height`/`overflow-y` from `.session-list` in `index.css` so the list grows unbounded; document in `workshop/bugs/bug-01-session-list-order-overflow.md`
- [x] T058 [P] Introduce Bug 2 (inflate focus total) — in `session_service.get_today()`, change the `total_focused_minutes` SQL to `SUM(focused_seconds)` without filtering by `status = 'completed'` so `stopped_early` sessions inflate the total; document in `workshop/bugs/bug-02-inflate-total.md`
- [ ] T059 Create Feature 1 exercise (break timer) — document in `workshop/features/feature-01-break-timer.md`; the feature uses the existing `break_minutes` setting to start a countdown after a focus session completes; the exercise guides participants through `/speckit.specify` → `/speckit.tasks` → tests → implementation
- [x] T060 Create `workshop/README.md` documenting 2 bugs and 1 feature exercise: reproduction steps, observed vs. expected behavior, spec reference (FR-number), and spec-first fix/implement guidance for each

---

## Dependencies (User Story Completion Order)

```
Phase 1 Setup
    └── Phase 2 Foundational
             ├── Phase 3 (US1 — P1) 🎯  ← MVP
             │       ├── Phase 4 (US2 — P2)   [requires active session infrastructure from US1]
             │       ├── Phase 5 (US3 — P3)   [requires active session infrastructure from US1]
             │       ├── Phase 6 (US4 — P4)   [requires session records from US1+US2+US3]
             │       └── Phase 7 (US5 — P5)   [requires Start flow from US1; independent of US2-US4]
             │
             └── Phase 8 Polish          [after US1–US5 complete]
                     └── Phase 9 Workshop  [after all phases passing]
```

**Parallel between user stories**: US2, US3, and US5 backend work (service functions) can be
implemented in parallel once Phase 2 is complete. Their frontend work can also overlap. US4 is
primarily UI and can be incrementally built alongside US1.

---

## Parallel Execution Examples Per User Story

**Within US1**:
```
│ T015 session_service.start()          │ T012 useTimerService store shell       │
│ T016 session_service.complete()       │ T013 API client wrapper                │
│ (backend service layer)               │ (frontend infrastructure)              │
```

**Within US2**:
```
│ T028 session_service.pause()          │ T033 useTimerService Paused state      │
│ T029 session_service.resume()         │ T034 Pause/Resume in Controls          │
│ (parallel: different functions)       │ (parallel: after T033)                 │
```

**Within US5**:
```
│ T046 settings_service                 │ T049 SettingsModal component           │
│ T047 settings routers                 │ T050 load settings on startup          │
│ (parallel: service + router)          │ (parallel: component + hook wiring)    │
```

**Within Phase 8**:
```
│ T052 Accessibility pass               │ T053 Performance pass                  │
│ T054 Page Visibility API              │ T055 Backend security check            │
│ (all parallel: different files)                                                 │
```

---

## Implementation Strategy

**MVP Scope** (deliver value after Phase 3 alone):
Complete Phases 1 + 2 + 3 (T001–T027). This gives a fully working start → auto-complete → today panel
flow. Users can already track focused sessions from day one.

**Incremental delivery**:
1. **Phase 1–3** (T001–T027): Working MVP — start/complete + today panel
2. **+ Phase 4** (T028–T035): Add pause/resume — robust against interruptions
3. **+ Phase 5** (T036–T041): Add stop-early — clean exit path
4. **+ Phase 6** (T042–T045): Enrich today panel with full session list
5. **+ Phase 7** (T046–T051): Add configurable durations
6. **+ Phase 8** (T052–T056): Polish — accessibility, performance, resilience
7. **+ Phase 9** (T057–T060): Introduce workshop defects and feature exercise (non-production work)

**Format validation**: All 60 tasks follow `- [ ] T### [P?] [US#?] Description with file path` format.
