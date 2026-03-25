# API Contract: Settings

**Version**: 1.0  
**Base URL**: `http://127.0.0.1:8000`  
**Format**: JSON  
**Auth**: None (localhost-only)

---

## Endpoints

### GET /settings

Returns the current user settings. If no settings row exists yet, returns the system defaults.

**Response 200**:
```json
{
  "focus_minutes": 25,
  "break_minutes": 5
}
```

---

### PUT /settings

Updates user settings. Full replacement (both fields required). Validated server-side.

**Request body**:
```json
{
  "focus_minutes": 50,
  "break_minutes": 10
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `focus_minutes` | integer | Yes | 1–480 |
| `break_minutes` | integer | Yes | 1–120 |

**Response 200**:
```json
{
  "focus_minutes": 50,
  "break_minutes": 10
}
```

**Response 422** — validation error:
```json
{
  "detail": [
    {
      "loc": ["body", "focus_minutes"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Notes**:
- Settings changes do NOT affect in-progress sessions. `configured_minutes` is captured at session start.
- Settings are stored in the `settings` table (singleton row `id = 1`, UPSERT semantics).
