# Implementation Plan: Automatic Break Countdown

**Branch**: `[002-auto-break-timer]` | **Date**: 2026-03-27 | **Spec**: [/home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/specs/002-auto-break-timer/spec.md]  
**Input**: Feature specification from `/home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/specs/002-auto-break-timer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Automatically transition a completed focus session into a persisted break countdown that uses the break duration configured at completion time, then let the user skip that break early from the existing timer UI. The design extends the FastAPI/SQLite backend with explicit break lifecycle records and typed break endpoints, while keeping the React/Zustand timer service as the single UI state owner that hydrates from persisted wall-clock timestamps.

## Technical Context

**Language/Version**: Python 3.11 backend; TypeScript 5.5 / React 18 frontend  
**Primary Dependencies**: FastAPI 0.110, Pydantic 2.6, aiosqlite 0.20, React 18, Zustand 4.5, Vite 5  
**Storage**: Local SQLite database (`focus_timer.db`) for sessions, settings, and new break records  
**Testing**: pytest + httpx + pytest-asyncio; Vitest + React Testing Library; ruff, mypy, ESLint, `tsc --noEmit`  
**Target Platform**: Local-first localhost web app (`127.0.0.1:8000` API + Vite frontend on `localhost:5173`)  
**Project Type**: Web application with React frontend and FastAPI backend  
**Performance Goals**: Auto-start visible break countdown within 1 second of focus completion; skip-break returns ready state within 1 second; break timing drift stays within 1 second across visibility changes/reload  
**Constraints**: Persist and derive timer state from wall-clock timestamps; keep backend localhost-only; preserve single-source timer state in `useTimerService`; allow zero-minute breaks to bypass countdown entirely; expose keyboard-accessible skip control only while break is active  
**Scale/Scope**: Single-user local timer workflow with at most one active focus session and one active break countdown at a time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Focus-First Design — PASS**: Break UI keeps the countdown/status as the primary visual element and exposes only the relevant action for the current state; `Skip break` remains secondary to the primary `Start` action that reappears only after break completion/skip.
- **II. Predictable & Deterministic Behavior — PASS**: Break state will be persisted with timestamps and rehydrated on visibility change/reload, avoiding tick-count drift and preserving actual remaining time.
- **III. User Trust Through Honest Reporting — PASS**: Only sessions that truly reach `completed` create a break; stopped-early sessions never trigger a break countdown.
- **IV. Privacy by Default — PASS**: The feature stays fully local in SQLite and localhost APIs with no new network destinations or telemetry.
- **V. Accessibility First — PASS**: Break status and remaining time remain screen-reader visible, and the skip action is keyboard operable and only present when valid.
- **VI. Readable Over Clever — PASS**: The plan adds a dedicated backend break service/router and small frontend state extensions instead of burying break logic in UI components.
- **VII. Small, Composable Components — PASS**: Break presentation stays in existing display/control components while business rules live in service/hook layers.
- **VIII. Typed Boundaries — PASS**: New/changed REST surfaces will use Pydantic models plus matching TypeScript/OpenAPI-generated client types.
- **IX. Single Source of Truth for Timer State — PASS**: The persisted backend break record is the canonical source across reloads, and the frontend continues to project all timer UI from `useTimerService`.

**Gate Result (pre-research)**: PASS. No constitution violations require exemption.

**Gate Result (post-design re-check)**: PASS. `research.md`, `data-model.md`, `quickstart.md`, and `contracts/breaks.openapi.yaml` keep timer state timestamp-based, typed, local-first, and centered on the existing single timer service.

## Project Structure

### Documentation (this feature)

```text
specs/002-auto-break-timer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── breaks.openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)
```text
backend/
├── src/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   ├── sessions.py
│   │   ├── settings.py
│   │   └── breaks.py          # planned
│   └── services/
│       ├── session_service.py
│       ├── settings_service.py
│       └── breaks_service.py  # planned
└── tests/
    ├── conftest.py
    ├── test_sessions.py
    ├── test_settings.py
    └── test_breaks.py         # planned

frontend/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── schema.ts
│   │   └── types.ts
│   ├── components/
│   │   ├── Controls.tsx
│   │   ├── TimerDisplay.tsx
│   │   └── __tests__/
│   ├── hooks/
│   │   └── useTimerService.ts
│   └── App.tsx
└── tests/
```

**Structure Decision**: Use the existing web-application split. Backend changes stay in `backend/src/{models.py,database.py,services/,routers/}` and backend tests; frontend changes stay in `frontend/src/{hooks,components,api}` and existing component tests. Feature planning artifacts live under `/home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/specs/002-auto-break-timer/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
