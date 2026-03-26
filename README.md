# Personal Focus Timer (Workday Pomodoro)

> **Workshop Project** — This codebase is intentionally designed for workshop and learning purposes. It is **not** production-ready and should not be deployed or used as-is in a production environment.

A local-first focus timer for knowledge workers. Start a 25-minute focus session, pause/resume when interrupted, stop early if needed, and review today's focused time — all persisted locally on your machine.

## Prerequisites

You'll need the following installed before getting started:

- **Python 3.11+** — [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Node.js 18+ (includes npm)** — [https://nodejs.org/en/download](https://nodejs.org/en/download)

To verify your installations:

```bash
python --version
node --version
npm --version
```

## Getting Started

### 1. Fork & Clone the Repository

1. Click **Fork** at the top-right of this repository on GitHub to create your own copy.
2. Clone your fork to your local machine:

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Open in Your Editor

Open the project folder in your preferred editor:

- **VS Code** — `code .` from the terminal, or use **File → Open Folder**
- **Cursor** — `cursor .` from the terminal, or use **File → Open Folder**
- **Any other editor** — open the root project folder directly

> **VS Code users:** Install the recommended extensions when prompted for the best experience (Python, ESLint, Prettier).

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
