# Research: Personal Focus Timer (Workday Pomodoro)

**Phase 0 output** | Branch: `001-focus-timer` | Date: 2026-03-24

---

## R-01: Timer display tick vs. timestamp truth (frontend)

**Decision**: `setInterval` fires every 200 ms purely to trigger a UI re-render. The displayed remaining
time is **always calculated** from `startAt + configuredDuration - Date.now() - totalPausedMs`.
The tick count itself is never accumulated.

**Rationale**: `setInterval` is throttled by browsers (background tabs, 4 ms minimum floor, task-queue
jitter). Wall-clock timestamps (`Date.now()`) are unaffected by throttling and survive tab switches and
page refreshes without any re-calibration. Using 200 ms refresh cadence makes display feel responsive
(<1 display frame delay) while the tick contributes nothing to the timer's authoritative value.

**Alternatives Considered**:
- Accumulating tick deltas — invisible drift compounds; fails on background tabs.
- `requestAnimationFrame` — paused in background, which breaks the round-trip restore requirement.
- 1000 ms interval — simpler but display will visibly stutter if a tick fires late.

---

## R-02: Frontend state ownership (Zustand vs. Context vs. useReducer)

**Decision**: A single **`useTimerService` hook** backed by a **Zustand store** is the canonical owner
of all timer state. Components subscribe only to the slices they need.

**Rationale**: React Context re-renders every subscriber on every state change; with a 200 ms tick rate
that means constant full-tree re-renders. Zustand provides fine-grained subscription and breaks the
render cycle. The hook wraps the store so callers have a clean interface and do not depend on Zustand
directly.

**Alternatives Considered**:
- React Context — unacceptable perf: entire component tree re-renders each tick.
- `useReducer` in the root component — works well for isolated apps, but cross-component access via
  prop drilling becomes unwieldy for 4+ components. Zustand is a minimal step up with no boilerplate.
- Redux Toolkit — overkill; more code than the feature itself.

---

## R-03: Auto-completion guard (preventing double-complete)

**Decision**: State transitions are guarded at the **store reducer level**: `COMPLETE` is a no-op if
`status !== 'running'`. The same guard exists on the backend endpoint (`POST /sessions/complete`
returns 409 if session is not in `running` state).

**Rationale**: React may re-render for unrelated state changes. If completion detection lives inside a
render function or component effect, it can fire multiple times. Idempotency at the state-transition
layer — not at the call site — is the safe pattern.

**Alternatives Considered**:
- `useRef` completion flag — works but leaks lifecycle state outside the store.
- Debounce of complete action — hides the bug rather than fixing it.

---

## R-04: Page Visibility API + tab restore

**Decision**: Register a `visibilitychange` listener on app mount. When the page becomes visible, call
`GET /sessions/active` to fetch fresh remaining time from the backend and overwrite the Zustand store.
Do not rely on the `setInterval` to self-correct after a long background period.

**Rationale**: Browsers starve background timers (Chrome: ≥10 s, Firefox: ≥30 s intervals in
background). After a 10-minute background period, the `setInterval` may have missed hundreds of ticks.
The frontend cannot reliably self-correct; re-fetching from the backend is the only safe recovery.

**Alternatives Considered**:
- Self-correcting interval — requires storing `expectedNextTick` and computing drift; fragile and
  complex; still fails if tab is backgrounded for an hour.
- WebSocket push from backend — overkill for a local single-user app; introduces socket lifecycle
  to manage.

---

## R-05: Backend persistence library (aiosqlite vs. ORM)

**Decision**: **aiosqlite with hand-written SQL**. Database file at
`{platform_app_data}/focus-timer/focus.db`.

**Rationale**: Five simple queries across two tables do not justify ORM overhead, migration tooling, or
additional dependencies. `aiosqlite` is async-native (no `run_in_executor` for every db call),
platform-portable, and keeps startup time low. Plain SQL makes every query explicit and testable
without mock abstractions.

**Alternatives Considered**:
- SQLAlchemy Core — adds `Column` mapping and session management for no benefit at this scale.
- SQLAlchemy ORM — adds relationship mapping and lazy-loading complexity; contraindicated by the
  Readable Over Clever principle.
- Raw `sqlite3` module — synchronous; requires `loop.run_in_executor` wrappers in every FastAPI async
  handler; avoidable.

---

## R-06: Single active session enforcement

**Decision**: **Two layers** — application-level check (409 Conflict with clear error message) as the
primary guard, backed by a SQLite partial unique index as a DB integrity net.

```sql
CREATE UNIQUE INDEX idx_one_active_session
  ON sessions(CASE WHEN status IN ('running', 'paused') THEN 1 END);
```

SQLite ignores NULL in unique indexes, so the index only constrains the one active row.

**Rationale**: Application-level check gives us control of error response shape (human-readable
`detail` field in the API response). The DB constraint is a last-line defense against any race
condition or direct DB manipulation that bypasses the application layer.

**Alternatives Considered**:
- DB constraint only — poor UX; clients receive opaque `UNIQUE constraint failed` errors.
- Application check only — susceptible to concurrent requests in a future multi-request scenario;
  no defense against direct DB writes.

---

## R-07: Remaining time computation on `GET /sessions/active`

**Decision**: Backend computes `remaining_seconds` fresh from stored timestamps on every request:
```
remaining_seconds = configured_seconds - (now - start_at).total_seconds() + paused_seconds
```
The response includes `remaining_seconds`, `status`, `start_at`, `paused_at`, and `configured_minutes`.

**Rationale**: Backend timestamps are the authoritative source. Frontend uses `remaining_seconds` for
immediate display on load and as a seed for the Zustand store. This makes page-refresh restoration
deterministic: no client-side replay of history needed.

**Alternatives Considered**:
- Frontend computes remaining from returned timestamps — client clock skew can produce wrong display;
  logic duplication; harder to test.
- Pre-computed `remaining_seconds` stored in DB — stale immediately; requires constant update writes.

---

## R-08: Pause duration tracking (embedded vs. separate table)

**Decision**: **Embedded in `sessions` table** — columns `paused_seconds INTEGER DEFAULT 0` and
`paused_at TEXT` (ISO timestamp, NULL when not paused).

On `pause`: set `paused_at = now`.  
On `resume`: add `(now - paused_at)` seconds to `paused_seconds`, clear `paused_at`.  
On `stop`/`complete`: if `paused_at IS NOT NULL`, finalize the running pause interval before closing.

**Rationale**: The spec only needs total focused duration, not the audit trail of individual pause
intervals. Embedded columns keep the schema to two tables, eliminate JOINs, and make every query a
single-table read or write.

**Alternatives Considered**:
- Separate `pause_intervals` table — justified if the spec required per-pause visualization or
  statistics; not needed for MVP.
- Client-side pause accumulation — loses state on page refresh; wrong for server-authoritative design.

---

## R-09: Session auto-completion detection

**Decision**: **Backend auto-completes on `GET /sessions/active`** — if `remaining_seconds <= 0` and
`status = 'running'`, the backend writes `status = 'completed'`, `end_at = now`, and computes
`focused_seconds` before returning the updated response.

Frontend also performs a client-side transition when its local `remaining` hits zero (for immediate
feedback). The backend is the authoritative record; frontend's transition is cosmetic only.

**Rationale**: No background scheduler or daemon needed. The frontend polls every ~1 second anyway
for display refresh. Auto-completion on the GET request is stateless, simple, and guaranteed to fire
as long as the user has the app open. For sessions where the user closes the app before the timer
expires, the completion is recorded on the next app open.

**Alternatives Considered**:
- FastAPI background task (`BackgroundTasks`) — runs after response; fragile if the process exits
  before the task runs.
- APScheduler / asyncio background loop — adds a daemon process, increases complexity, adds a
  failure mode (scheduler crash) for negligible benefit.
- WebSocket push — appropriate if the app grows to multi-tab awareness; deferred to post-MVP.

---

## R-10: OpenAPI client type generation

**Decision**: Generate TypeScript types from the FastAPI OpenAPI schema (`/openapi.json`) using
**`openapi-typescript`** (build-time CLI), output to `frontend/src/api/schema.ts`. Frontend uses
these types for all request/response shapes. No manual DTOs.

**Rationale**: Principle VIII requires a shared schema definition to prevent frontend/backend type
drift. FastAPI generates OpenAPI 3.1 automatically; `openapi-typescript` is a zero-runtime, single
devDependency that runs as a Vite build step or standalone script.

**Alternatives Considered**:
- Manual TypeScript types — duplicates backend Pydantic models; drift-prone.
- tRPC — requires Python adapter; adds complexity; not idiomatic for FastAPI.
- zod-openapi — runtime validation overhead; unnecessary for a local app.
