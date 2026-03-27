# test Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-27

## Active Technologies
- TypeScript 5.5 / React 18.3 + React 18.3, Zustand 4.5, Vite 5.4, Vitest 2.0, @testing-library/react 16 (003-session-list-display)
- N/A — display-only change; sessions are read from props passed by the parent component (003-session-list-display)
- Python 3.12 (backend), TypeScript / React 18 (frontend) + FastAPI, aiosqlite, Pydantic (backend); Vite, React (frontend) (004-fix-total-rounding)
- SQLite via aiosqlite (004-fix-total-rounding)
- TypeScript 5 (strict mode enabled) + React 18, Zustand (state store), Vite (dev/build) (006-break-timer)
- N/A — break state is display-only; not persisted to backend (006-break-timer)
- Python 3.11 backend; TypeScript 5.5 / React 18 frontend + FastAPI 0.110, Pydantic 2.6, aiosqlite 0.20, React 18, Zustand 4.5, Vite 5 (002-auto-break-timer)
- Local SQLite database (`focus_timer.db`) for sessions, settings, and new break records (002-auto-break-timer)

- Python 3.11 (backend) · TypeScript 5.x / Node 20+ (frontend) + FastAPI 0.110+, SQLite via `aiosqlite` + raw SQL (backend) · React 18, Vite 5, React Testing Library (frontend) (001-focus-timer)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11 (backend) · TypeScript 5.x / Node 20+ (frontend): Follow standard conventions

## Recent Changes
- 002-auto-break-timer: Added Python 3.11 backend; TypeScript 5.5 / React 18 frontend + FastAPI 0.110, Pydantic 2.6, aiosqlite 0.20, React 18, Zustand 4.5, Vite 5
- 006-break-timer: Added TypeScript 5 (strict mode enabled) + React 18, Zustand (state store), Vite (dev/build)
- 004-fix-total-rounding: Added Python 3.12 (backend), TypeScript / React 18 (frontend) + FastAPI, aiosqlite, Pydantic (backend); Vite, React (frontend)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
