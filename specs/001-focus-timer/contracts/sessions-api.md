# API Contract: Focus Sessions

**Version**: 1.0  
**Base URL**: `http://127.0.0.1:8000`  
**Format**: JSON  
**Auth**: None (localhost-only)

---

## Common Types

```yaml
SessionStatus:
  type: string
  enum: [running, paused, completed, stopped_early]

ActiveSessionResponse:
  type: object
  required: [id, start_at, status, configured_minutes, paused_seconds, remaining_seconds]
  properties:
    id:
      type: integer
    start_at:
      type: string
      format: date-time
    end_at:
      type: string
      format: date-time
      nullable: true
    status:
      $ref: '#/SessionStatus'
    configured_minutes:
      type: integer
    paused_seconds:
      type: integer
    paused_at:
      type: string
      format: date-time
      nullable: true
    remaining_seconds:
      type: number
      description: Computed server-side from timestamps; authoritative for client restoration
    note:
      type: string
      nullable: true

SessionSummaryResponse:
  type: object
  required: [id, start_at, status, focused_seconds]
  properties:
    id:
      type: integer
    start_at:
      type: string
      format: date-time
    end_at:
      type: string
      format: date-time
    status:
      $ref: '#/SessionStatus'
    focused_seconds:
      type: integer
    note:
      type: string
      nullable: true

ErrorResponse:
  type: object
  required: [detail]
  properties:
    detail:
      type: string
```

---

## Endpoints

### GET /sessions/active

Returns the currently active (running or paused) session with server-computed remaining time.
Used on page load and on tab visibility restore to re-synchronize frontend state.

**Response 200** — active session exists:
```json
{
  "id": 42,
  "start_at": "2026-03-24T09:00:00Z",
  "end_at": null,
  "status": "running",
  "configured_minutes": 25,
  "paused_seconds": 0,
  "paused_at": null,
  "remaining_seconds": 1342.7,
  "note": null
}
```

**Response 200** — no active session:
```json
null
```

**Side effect**: If an active session is found with `remaining_seconds <= 0` and `status = 'running'`,
the backend auto-completes it (sets `status = 'completed'`, writes `end_at` and `focused_seconds`)
and returns the completed session.

---

### POST /sessions/start

Starts a new focus session. Rejects with 409 if any session is already running or paused.

**Request body**:
```json
{
  "configured_minutes": 25,
  "note": "Deep work: spec review"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `configured_minutes` | integer | Yes | 1–480 |
| `note` | string | No | Max 500 chars; empty string stored as null |

**Response 201**:
```json
{
  "id": 43,
  "start_at": "2026-03-24T10:00:00Z",
  "end_at": null,
  "status": "running",
  "configured_minutes": 25,
  "paused_seconds": 0,
  "paused_at": null,
  "remaining_seconds": 1500.0,
  "note": "Deep work: spec review"
}
```

**Response 409** — session already active:
```json
{ "detail": "A focus session is already active. Stop or complete it before starting a new one." }
```

**Response 422** — validation error (FastAPI default):
```json
{ "detail": [{ "loc": ["body", "configured_minutes"], "msg": "ensure this value is greater than 0", "type": "value_error.number.not_gt" }] }
```

---

### POST /sessions/{id}/pause

Pauses the specified running session. Records `paused_at = now`.

**Path parameter**: `id` — session ID (integer)

**Request body**: empty

**Response 200**:
```json
{
  "id": 43,
  "start_at": "2026-03-24T10:00:00Z",
  "end_at": null,
  "status": "paused",
  "configured_minutes": 25,
  "paused_seconds": 0,
  "paused_at": "2026-03-24T10:05:30Z",
  "remaining_seconds": 1170.0,
  "note": null
}
```

**Response 404** — session not found:
```json
{ "detail": "Session not found." }
```

**Response 409** — session not in `running` state:
```json
{ "detail": "Session is not running; cannot pause." }
```

---

### POST /sessions/{id}/resume

Resumes a paused session. Adds `(now - paused_at)` seconds to `paused_seconds`, clears `paused_at`.

**Path parameter**: `id` — session ID (integer)

**Request body**: empty

**Response 200**:
```json
{
  "id": 43,
  "start_at": "2026-03-24T10:00:00Z",
  "end_at": null,
  "status": "running",
  "configured_minutes": 25,
  "paused_seconds": 90,
  "paused_at": null,
  "remaining_seconds": 1080.0,
  "note": null
}
```

**Response 404** — session not found.  
**Response 409** — session not in `paused` state:
```json
{ "detail": "Session is not paused; cannot resume." }
```

---

### POST /sessions/{id}/stop

Stops a running or paused session early. Computes `focused_seconds`, writes `end_at`, sets
`status = 'stopped_early'`.

**Path parameter**: `id` — session ID (integer)

**Request body**: empty

**Response 200**:
```json
{
  "id": 43,
  "start_at": "2026-03-24T10:00:00Z",
  "end_at": "2026-03-24T10:08:12Z",
  "status": "stopped_early",
  "configured_minutes": 25,
  "focused_seconds": 402,
  "paused_seconds": 90,
  "paused_at": null,
  "remaining_seconds": 0,
  "note": null
}
```

**Response 404** — session not found.  
**Response 409** — session already in a terminal state:
```json
{ "detail": "Session has already ended." }
```

---

### POST /sessions/{id}/complete

Marks a session as completed (full duration elapsed). Normally called by the client when client-side
remaining time hits zero; backend will also auto-complete on the next `GET /sessions/active` call.

**Path parameter**: `id` — session ID (integer)

**Request body**: empty

**Response 200**:
```json
{
  "id": 43,
  "start_at": "2026-03-24T10:00:00Z",
  "end_at": "2026-03-24T10:25:00Z",
  "status": "completed",
  "configured_minutes": 25,
  "focused_seconds": 1500,
  "paused_seconds": 0,
  "note": null
}
```

**Response 404** — session not found.  
**Response 409** — session not in `running` state (idempotency guard):
```json
{ "detail": "Session is not running; cannot complete." }
```

---

### GET /sessions/today

Returns all sessions started today (local calendar date), ordered by `start_at` ascending, plus the
total focused minutes for today.

**Response 200**:
```json
{
  "date": "2026-03-24",
  "total_focused_minutes": 42,
  "sessions": [
    {
      "id": 41,
      "start_at": "2026-03-24T08:00:00Z",
      "end_at": "2026-03-24T08:25:00Z",
      "status": "completed",
      "focused_seconds": 1500,
      "note": null
    },
    {
      "id": 42,
      "start_at": "2026-03-24T09:00:00Z",
      "end_at": "2026-03-24T09:08:12Z",
      "status": "stopped_early",
      "focused_seconds": 402,
      "note": "interrupted by standup"
    }
  ]
}
```

**Notes**:
- Active (running/paused) session is included in the list with `end_at = null` and `focused_seconds = null`.
- `total_focused_minutes` is `FLOOR(SUM(focused_seconds) / 60)` — only counts sessions with a non-null
  `focused_seconds` (completed or stopped_early). Active session does not inflate the total.
