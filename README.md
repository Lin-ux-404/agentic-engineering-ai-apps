# Personal Focus Timer (Workday Pomodoro)

A local-first focus timer for knowledge workers. Start a 25-minute focus session, pause/resume when interrupted, stop early if needed, and review today's focused time — all persisted locally on your machine.

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

Run the following command to start the backend:

```
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Project Structure

```
backend/         FastAPI backend (Python 3.11, aiosqlite, SQLite)
frontend/        React + TypeScript frontend (Vite 5)
workshop/        Intentional workshop bugs + exercise guide
specs/           Design artifacts (spec, plan, data-model, contracts, tasks)
```

## Development

See [specs/001-focus-timer/quickstart.md](specs/001-focus-timer/quickstart.md) for full development setup.

### Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm test
```

### Linting & Type-checks

```bash
# Backend
cd backend && ruff check src/ tests/ && mypy src/

# Frontend
cd frontend && npm run lint && npm run typecheck
```
