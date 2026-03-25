# Implementation Plan: Personal Focus Timer (Workday Pomodoro)

**Branch**: `001-focus-timer` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-focus-timer/spec.md`

## Summary

A single-user, local-first focus timer for knowledge workers. The user starts a 25-minute (configurable)
focus session, can pause/resume it, and stops it early or lets it auto-complete. Every state transition
is persisted immediately to a local SQLite database through a FastAPI backend running on localhost. A
React + TypeScript (Vite) frontend renders all state from a single timer-service hook and calls the
backend API for every mutation. Today's session history and total focused minutes are displayed
alongside the live countdown.

## Technical Context

**Language/Version**: Python 3.11 (backend) · TypeScript 5.x / Node 20+ (frontend)  
**Primary Dependencies**: FastAPI 0.110+, SQLite via `aiosqlite` + raw SQL (backend) · React 18, Vite 5, React Testing Library (frontend)  
**Storage**: SQLite — single file in `~/.focus-timer/focus.db` (or OS-appropriate app-data dir)  
**Testing**: pytest + httpx (backend API tests) · Vitest + React Testing Library (frontend unit + component tests)  
**Target Platform**: Desktop browser (Chrome/Firefox/Edge on macOS/Linux/Windows); backend binds to `127.0.0.1`  
**Project Type**: Web application — React SPA frontend + local FastAPI backend  
**Performance Goals**: App interactive within 2 s of page load; timer drift < 1 s over 25-minute session  
**Constraints**: Localhost-only binding; no cloud calls; single active session at a time; offline-tolerant UI (degraded-mode banner when backend unreachable)  
**Scale/Scope**: Single user per installation; ~5 screens of UI; ~10 API endpoints; no auth

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|---|---|---|
| I | Focus-First Design | ✅ PASS | Single-page layout; minimal UI surface; one primary CTA enforced by design |
| II | Predictable & Deterministic Behavior | ✅ PASS | Timer uses wall-clock timestamps; state restored on reload from DB snapshot |
| III | User Trust Through Honest Reporting | ✅ PASS | Status labels (Completed / Stopped early) set server-side; paused seconds stored separately |
| IV | Privacy by Default | ✅ PASS | Backend binds to `127.0.0.1`; SQLite in local app-data dir; no external calls |
| V | Accessibility First | ✅ PASS | ARIA labels required on all controls; keyboard navigation enforced in component design |
| VI | Readable Over Clever | ✅ PASS | Plain SQL over ORM; explicit state‑machine transitions; no magic |
| VII | Small, Composable Components | ✅ PASS | 4 focused components (TimerDisplay, Controls, TodaySummary, SettingsModal); hook owns all business logic |
| VIII | Typed Boundaries | ✅ PASS | `strict` TypeScript; Pydantic request/response models; OpenAPI schema shared |
| IX | Single Source of Truth for Timer State | ✅ PASS | `useTimerService` hook is sole owner of timer state; backend is authoritative for persistence |

**Gate result: ALL PASS — proceed to Phase 0.**

**Post-design re-check** (after Phase 1 artifacts):

| # | Principle | Post-Design Status | Verification |
|---|---|---|---|
| I | Focus-First Design | ✅ PASS | 4 focused components; single primary CTA per state enforced in Controls component contract |
| II | Predictable & Deterministic Behavior | ✅ PASS | `remaining_seconds` computed from DB timestamps on every `GET /sessions/active`; Page Visibility API re-syncs |
| III | User Trust Through Honest Reporting | ✅ PASS | `focused_seconds = elapsed − paused_seconds` computed server-side at session close; no inflation in `total_focused_minutes` |
| IV | Privacy by Default | ✅ PASS | Backend CORS restricted to `localhost:5173`; DB path in OS app-data dir; no external URLs in codebase |
| V | Accessibility First | ✅ PASS | All buttons carry ARIA labels per component contract; keyboard operability enforced in Controls design |
| VI | Readable Over Clever | ✅ PASS | DDL in plain SQL; service layer has one function per transition; no clever query tricks |
| VII | Small, Composable Components | ✅ PASS | Each component has a single concern; `useTimerService` holds all business logic; ~100 lines per component |
| VIII | Typed Boundaries | ✅ PASS | `openapi-typescript` generates `schema.ts` from FastAPI OpenAPI; Pydantic models on all request/response paths |
| IX | Single Source of Truth | ✅ PASS | Zustand store is sole owner; components never compute or store remaining time locally |

**Post-design gate: ALL PASS.**

## Project Structure

### Documentation (this feature)

```text
specs/001-focus-timer/
├── plan.md              # This file
├── research.md          # Phase 0 output (10 research decisions)
├── data-model.md        # Phase 1 output (entities, DDL, frontend state model)
├── quickstart.md        # Phase 1 output (setup + dev workflow)
├── contracts/
│   ├── sessions-api.md  # Phase 1 output (session lifecycle endpoints)
│   └── settings-api.md  # Phase 1 output (settings GET/PUT)
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                  # FastAPI app: CORS, lifespan, router registration
│   ├── database.py              # aiosqlite factory + DDL init on startup
│   ├── models.py                # Pydantic request/response models
│   ├── routers/
│   │   ├── sessions.py          # GET /sessions/active, POST /sessions/*, GET /sessions/today
│   │   └── settings.py          # GET /settings, PUT /settings
│   └── services/
│       └── session_service.py   # start / pause / resume / stop / complete / get_today
└── tests/
    ├── conftest.py              # In-memory SQLite test fixture + test app
    ├── test_sessions.py         # State-machine + API integration tests
    └── test_settings.py         # Settings CRUD tests

frontend/
├── src/
│   ├── main.tsx                 # React entry point
│   ├── App.tsx                  # Root layout + offline banner
│   ├── api/
│   │   ├── client.ts            # fetch wrapper (error handling, offline detection)
│   │   └── schema.ts            # Auto-generated from /openapi.json (do not edit)
│   ├── hooks/
│   │   └── useTimerService.ts   # Zustand store, 200 ms tick, Page Visibility sync
│   └── components/
│       ├── TimerDisplay.tsx     # mm:ss + state label; reads from useTimerService
│       ├── Controls.tsx         # Start / Stop / Pause / Resume; dispatches via useTimerService
│       ├── TodaySummary.tsx     # Total focused minutes + session list
│       ├── SettingsModal.tsx    # focus_minutes / break_minutes form
│       └── __tests__/          # Vitest + React Testing Library component tests
├── vite.config.ts
└── tsconfig.json                # strict: true
```

**Structure Decision**: Web application layout (`backend/` + `frontend/`) is used. The project has
a clear frontend/backend separation with independent dependency management and test suites.
No shared code package is needed at MVP scope — the only cross-boundary contract is the OpenAPI
schema, consumed via `openapi-typescript` code generation into `frontend/src/api/schema.ts`.
