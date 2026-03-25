# Quickstart: Personal Focus Timer (Workday Pomodoro)

**Branch**: `001-focus-timer` | **Date**: 2026-03-24

This guide covers getting the app running locally in development mode.

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 20 LTS | `node --version` |
| npm | 10+ | Bundled with Node 20 |

---

## Repository Layout

```text
├── backend/
│   ├── src/
│   │   ├── main.py             # FastAPI app + CORS + startup
│   │   ├── database.py         # aiosqlite connection factory + schema init
│   │   ├── models.py           # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── sessions.py     # /sessions/* endpoints
│   │   │   └── settings.py     # /settings endpoints
│   │   └── services/
│   │       └── session_service.py  # Business logic: start/pause/resume/stop/complete
│   └── tests/
│       ├── conftest.py         # In-memory aiosqlite fixture
│       ├── test_sessions.py    # API + state-machine integration tests
│       └── test_settings.py    # Settings CRUD tests
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── App.tsx             # Root component: layout + context wiring
│   │   ├── api/
│   │   │   ├── client.ts       # fetch wrapper + error handling
│   │   │   └── schema.ts       # Auto-generated from backend OpenAPI (do not edit)
│   │   ├── hooks/
│   │   │   └── useTimerService.ts  # Zustand store + 200 ms tick + Page Visibility sync
│   │   ├── components/
│   │   │   ├── TimerDisplay.tsx    # mm:ss countdown + state label
│   │   │   ├── Controls.tsx        # Start / Stop / Pause / Resume buttons
│   │   │   ├── TodaySummary.tsx    # Total focused minutes + session list
│   │   │   └── SettingsModal.tsx   # focus_minutes / break_minutes form
│   │   └── components/__tests__/  # Vitest + React Testing Library tests
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── specs/001-focus-timer/      # This directory
```

---

## 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn[standard] aiosqlite pydantic

# Run the API server (binds to 127.0.0.1:8000)
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

**SQLite database location** (created automatically on first run):

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/focus-timer/focus.db` |
| Linux | `~/.local/share/focus-timer/focus.db` |
| Windows | `%APPDATA%\focus-timer\focus.db` |

---

## 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Generate TypeScript types from backend OpenAPI schema
# (backend must be running on port 8000)
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api/schema.ts

# Start the dev server (proxies /api/* to the backend automatically)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 3. Running Tests

**Backend**:

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

**Frontend**:

```bash
cd frontend
npm test
# or: npm run test:ui  (Vitest UI)
```

**Run all (CI equivalent)**:

```bash
# From repo root:
cd backend && pytest tests/ && cd ..
cd frontend && npm run typecheck && npm run lint && npm test && cd ..
```

---

## 4. Key npm / pip scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build to `frontend/dist/` |
| `npm run typecheck` | `tsc --noEmit` (no emit, type errors only) |
| `npm run lint` | ESLint on `src/**/*.{ts,tsx}` |
| `npm test` | Vitest unit + component tests |
| `uvicorn src.main:app --reload` | Backend dev server |
| `pytest tests/ -v` | Backend tests with verbose output |

---

## 5. Architecture Notes

- **Backend owns persistence and state truth.** All timer mutations call the backend first.
- **Frontend uses optimistic UI updates** — it transitions its local Zustand state immediately on
  button press, but re-syncs from the backend response. If the backend call fails, the optimistic
  state is rolled back and the error banner is shown.
- **Page Visibility API** — when the browser tab regains focus after being hidden, `useTimerService`
  calls `GET /sessions/active` to re-seed `remainingSeconds` from server timestamps. This prevents
  display drift after background throttling.
- **OpenAPI types** — `src/api/schema.ts` is machine-generated. Re-run the `openapi-typescript`
  command whenever backend models change. Never edit `schema.ts` by hand.
- **Backend CORS** — the FastAPI app configures `allow_origins=["http://localhost:5173"]` for dev.
  Production (same-host serving) does not require CORS headers.
