# Data Model: Personal Focus Timer (Workday Pomodoro)

**Phase 1 output** | Branch: `001-focus-timer` | Date: 2026-03-24

---

## Entities

### 1. FocusSession

Represents a single timed work interval from the moment the user presses "Start" until the session
ends (either by auto-completion when the countdown reaches zero, or by the user pressing "Stop").

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER (PK) | No | Auto-increment primary key |
| `start_at` | TEXT (ISO 8601 UTC) | No | Wall-clock time at which the session was started |
| `end_at` | TEXT (ISO 8601 UTC) | Yes | Wall-clock time at which the session ended; NULL while active |
| `status` | TEXT | No | `running` · `paused` · `completed` · `stopped_early` |
| `configured_minutes` | INTEGER | No | Focus duration configured at session start (minutes) |
| `focused_seconds` | INTEGER | Yes | Actual focused (non-paused) duration; NULL until session ends |
| `paused_seconds` | INTEGER | No | Accumulated pause time in seconds; 0 initially |
| `paused_at` | TEXT (ISO 8601 UTC) | Yes | Timestamp of the most recent pause; NULL when not paused |
| `note` | TEXT | Yes | Optional user-provided text note; NULL if not entered |
| `date_key` | TEXT (YYYY-MM-DD) | No | Calendar date of `start_at` in local time; used for "today" filtering |

**State machine**:

```
idle (no row)
    │ POST /sessions/start
    ▼
running ──── POST /sessions/pause ──▶ paused
    │                                    │
    │         POST /sessions/resume ◀────┘
    │
    ├── POST /sessions/stop ──▶ stopped_early (terminal)
    └── auto (remaining ≤ 0)  ──▶ completed (terminal)
```

**Constraints**:
- At most one row in `(running, paused)` status at any time (enforced by partial unique index).
- `end_at` and `focused_seconds` MUST be set atomically when transitioning to a terminal state.
- `focused_seconds = (end_at - start_at) total seconds − paused_seconds`.
- `date_key` is computed from `start_at` converted to local time at insert time.
- A session in a terminal state (`completed`, `stopped_early`) MUST NOT be mutated.

**Validation rules**:
- `configured_minutes`: positive integer, 1–480 (maximum 8-hour session as sanity cap).
- `note`: maximum 500 characters; empty string normalized to NULL.
- `status`: only the four values listed above; rejected otherwise.

---

### 2. Settings

A singleton configuration record. There is always exactly one row (row `id = 1`), created on first
run with default values. UPSERT on PUT.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER (PK) | No | Always 1 |
| `focus_minutes` | INTEGER | No | Default focus session duration in minutes; default 25 |
| `break_minutes` | INTEGER | No | Default break duration in minutes; default 5 |

**Validation rules**:
- `focus_minutes`: positive integer, 1–480.
- `break_minutes`: positive integer, 1–120.

---

## Database Schema (SQLite DDL)

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at          TEXT    NOT NULL,
    end_at            TEXT,
    status            TEXT    NOT NULL CHECK(status IN ('running','paused','completed','stopped_early')),
    configured_minutes INTEGER NOT NULL CHECK(configured_minutes BETWEEN 1 AND 480),
    focused_seconds   INTEGER,
    paused_seconds    INTEGER NOT NULL DEFAULT 0,
    paused_at         TEXT,
    note              TEXT    CHECK(LENGTH(note) <= 500),
    date_key          TEXT    NOT NULL
);

-- Partial unique index: only one row may be in an active state at any time.
-- SQLite unique indexes ignore NULL values, so completed/stopped rows are exempt.
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_session
    ON sessions (CASE WHEN status IN ('running', 'paused') THEN 1 END);

CREATE TABLE IF NOT EXISTS settings (
    id            INTEGER PRIMARY KEY CHECK(id = 1),
    focus_minutes INTEGER NOT NULL DEFAULT 25 CHECK(focus_minutes BETWEEN 1 AND 480),
    break_minutes INTEGER NOT NULL DEFAULT 5  CHECK(break_minutes BETWEEN 1 AND 120)
);

-- Ensure the singleton row always exists.
INSERT OR IGNORE INTO settings (id, focus_minutes, break_minutes) VALUES (1, 25, 5);
```

---

## Frontend State Model

The `useTimerService` hook exposes the following state shape (TypeScript):

```ts
type TimerStatus = 'idle' | 'running' | 'paused' | 'completed' | 'stopped_early';

interface TimerState {
  status: TimerStatus;

  // Present when status is 'running' or 'paused'; null when 'idle'
  sessionId: number | null;
  startAt: number | null;           // Unix ms (from backend ISO timestamp)
  configuredSeconds: number | null;
  pausedSeconds: number | null;     // Accumulated paused seconds (from backend)
  pausedAt: number | null;          // Unix ms when current pause started; null if not paused
  note: string;

  // Derived, computed on every tick
  remainingSeconds: number;         // max(0, configuredSeconds - elapsed + pausedSeconds)

  // Today summary (refreshed after each state transition)
  todaySessions: SessionSummary[];
  todayFocusedMinutes: number;

  // Error/offline state
  backendReachable: boolean;
  lastError: string | null;
}

interface SessionSummary {
  id: number;
  startAt: string;           // Displayed as local time HH:mm
  focusedSeconds: number;
  status: 'completed' | 'stopped_early';
  note: string | null;
}
```

**Derived computation** (performed in `useTimerService` on every tick, not stored):

```
if status === 'running':
  elapsed = (Date.now() - startAt) / 1000
  remaining = max(0, configuredSeconds - elapsed + pausedSeconds)

if status === 'paused':
  elapsedBeforePause = (pausedAt - startAt) / 1000
  remaining = max(0, configuredSeconds - elapsedBeforePause + pausedSeconds)
```

---

## State Transitions (Frontend ↔ Backend)

| User Action | Frontend dispatches | Backend endpoint | Backend response used to update store |
|---|---|---|---|
| App load | hydrate from API | `GET /sessions/active` | Full session state or `null` |
| Press Start | optimistic → `running` | `POST /sessions/start` | Confirmed session with `id`, `start_at` |
| Press Pause | optimistic → `paused` | `POST /sessions/{id}/pause` | Confirmed `paused_at` |
| Press Resume | optimistic → `running` | `POST /sessions/{id}/resume` | Confirmed `paused_seconds` |
| Press Stop | optimistic → `stopped_early` | `POST /sessions/{id}/stop` | Final session record |
| Timer reaches 0 | display `completed` | `POST /sessions/{id}/complete` (or next GET auto-completes) | Final session record |
| Tab becomes visible | re-sync | `GET /sessions/active` | Fresh `remaining_seconds` overwrites local calculation |
