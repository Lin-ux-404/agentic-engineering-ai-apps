# Data Model: Automatic Break Countdown

## Entity: Focus Session

**Purpose**: Existing work interval record. This feature changes what happens immediately after a session reaches the `completed` outcome.

### Fields

| Field | Type | Source | Notes |
|---|---|---|---|
| `id` | integer | existing | Primary key |
| `start_at` | ISO-8601 UTC string | existing | Wall-clock start timestamp |
| `end_at` | ISO-8601 UTC string \| null | existing | Set when session ends |
| `status` | enum | existing | `running`, `paused`, `completed`, `stopped_early` |
| `configured_minutes` | integer | existing | Snapshot of focus duration |
| `focused_seconds` | integer \| null | existing | Derived total excluding pauses |
| `paused_seconds` | integer | existing | Accumulated paused time |
| `paused_at` | ISO-8601 UTC string \| null | existing | Open pause marker |
| `note` | string \| null | existing | Optional user note |
| `date_key` | string | existing | Local calendar day bucket |

### Validation Rules

- `configured_minutes` remains `1..480`.
- `status = completed` is only allowed when full elapsed duration is reached or the backend auto-completes an expired running session.
- `status = stopped_early` must never create a follow-on break countdown.

### Relationships

- One focus session may create **zero or one** `BreakCountdown` records.
- Relationship is zero when the session is stopped early or when `break_minutes = 0` at completion time.

### State Transitions

```text
idle -> running -> paused -> running -> completed
idle -> running -> stopped_early
completed -> (optionally spawns BreakCountdown.active)
```

## Entity: Break Duration Setting

**Purpose**: User preference that determines how long the next automatic break should last.

### Fields

| Field | Type | Source | Notes |
|---|---|---|---|
| `focus_minutes` | integer | existing settings row | Unchanged |
| `break_minutes` | integer | existing settings row | Must be expanded to allow zero |

### Validation Rules

- `focus_minutes` remains `1..480`.
- `break_minutes` becomes `0..120`.
- The value used for a break is the value currently saved when the focus session completes.

### Relationships

- One settings row influences many future focus sessions.
- The configured break duration is copied into a `BreakCountdown` snapshot so later settings edits do not mutate an active break.

## Entity: Break Countdown

**Purpose**: New persisted rest interval spawned by a completed focus session.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Primary key |
| `session_id` | integer | Foreign key to `sessions.id`, unique per source session |
| `start_at` | ISO-8601 UTC string | Timestamp when the break started |
| `expected_end_at` | ISO-8601 UTC string | `start_at + configured_minutes` |
| `configured_minutes` | integer | Snapshot of break duration used for this break |
| `status` | enum | `active`, `skipped`, `finished` |
| `skipped_at` | ISO-8601 UTC string \| null | Set only when user skips |
| `finished_at` | ISO-8601 UTC string \| null | Set when break naturally expires |
| `date_key` | string | Local calendar day bucket for future reporting |

### Validation Rules

- Created only when the parent focus session reaches `completed`.
- `configured_minutes` must be `1..120` on persisted break records because zero-duration breaks are bypassed and never inserted.
- Only one break may be `active` at a time.
- `skip` is valid only from `status = active`.
- On hydrate/read, if `now >= expected_end_at`, the backend must transition the break to `finished` and return ready state.

### Relationships

- `BreakCountdown.session_id` references exactly one completed `FocusSession`.
- The frontend timer store projects `BreakCountdown` into the current timer display and controls.

### State Transitions

```text
none -> active -> finished
none -> active -> skipped
completed focus session + break_minutes = 0 -> none (direct ready state)
stopped_early focus session -> none
```

## Derived Projection: Timer View State

**Purpose**: Frontend-only projection owned by `useTimerService.ts`.

### Derived Fields

| Field | Type | Derived From |
|---|---|---|
| `status` | `idle \| running \| paused \| break \| completed \| stopped_early` | active session + active break APIs |
| `remainingSeconds` | number \| null | wall-clock calculation from the current active object |
| `sessionId` | number \| null | active focus session |
| `breakId` | number \| null | active break |

### Rules

- The UI must never hold separate countdown math outside this store.
- When a break is active, the timer label/status reflects break state and `Skip break` is the only valid secondary action.
- When no focus session or break is active, the projection returns to `idle`/ready-to-start behavior.
