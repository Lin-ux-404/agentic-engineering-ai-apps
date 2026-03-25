# Workshop: Personal Focus Timer

Welcome to the Spec-Driven Development (SDD) workshop. This directory contains **two realistic
bugs** and **one new feature** to implement in the Personal Focus Timer application.

The goal is not just to fix bugs or add features — it's to practise the **speckit workflow**:
using spec artifacts and AI-assisted commands to diagnose, document, and verify changes before
writing a single line of code.

---

## The SDD Bug-Fix & Feature Workflow

For every bug, follow this 5-step loop:

```
1. CLARIFY   → understand the intended behaviour from the spec
2. REPRODUCE → confirm the bug exists and is observable
3. SPECIFY   → write a one-sentence user story for the fix (/speckit.specify)
4. TEST      → write a failing test that encodes the expected behaviour
5. FIX       → change the minimum amount of code to make the test green
```

For the feature exercise, replace steps 1–2 with:

```
1. SPECIFY   → write the user story and acceptance criteria (/speckit.specify)
2. TASKS     → break it into ordered implementation steps (/speckit.tasks)
3. TEST      → write failing tests for each acceptance criterion
4. IMPLEMENT → work through the task list
5. VERIFY    → run all tests, lint, and typecheck
```

The speckit commands below map directly to these loops. Each exercise file shows exactly which
command to run and what to type at each stage.

---

## Branching Strategy

Each exercise runs on its own isolated branch. Speckit creates the branch and saves spec
artifacts automatically when you run the first speckit command for that exercise — you don't
need to do anything manually.

| Exercise | Branch (created by speckit) | Spec folder (populated by speckit) |
|----------|-----------------------------|-------------------------------------|
| Bug 01   | `workshop/bug-01-session-list-order-overflow` | `specs/bug-01-session-list-order-overflow/` |
| Bug 02   | `workshop/bug-02-inflate-total`               | `specs/bug-02-inflate-total/` |
| Feature 01 | `workshop/feature-01-break-timer`           | `specs/feature-01-break-timer/` |

---

## Bugs

| # | File | Title | Component | Branch | Speckit Focus |
|---|------|-------|-----------|--------|---------------|
| 1 | [bug-01-session-list-order-overflow.md](bugs/bug-01-session-list-order-overflow.md) | Session List Order & Overflow | Frontend | `workshop/bug-01-session-list-order-overflow` | `/speckit.clarify` → `/speckit.specify` |
| 2 | [bug-02-inflate-total.md](bugs/bug-02-inflate-total.md) | Today's Total Includes Active Session Time | Backend | `workshop/bug-02-inflate-total` | `/speckit.clarify` → `/speckit.specify` |

---

## Features

| # | File | Title | Component | Branch | Speckit Focus |
|---|------|-------|-----------|--------|---------------|
| 1 | [feature-01-break-timer.md](features/feature-01-break-timer.md) | Break Timer | Frontend | `workshop/feature-01-break-timer` | `/speckit.specify` → `/speckit.tasks` |

---

## Speckit Commands Quick Reference

| Command | When to use it |
|---------|----------------|
| `/speckit.clarify` | Ask targeted questions about an underspecified behaviour before writing code |
| `/speckit.specify` | Encode a new or corrected behaviour as a user story with acceptance criteria |
| `/speckit.tasks` | Break a spec change into concrete, ordered implementation tasks |
| `/speckit.checklist` | Generate a verification checklist for a specific change |
| `/speckit.analyze` | Audit consistency between spec, plan, and tasks after making changes |

---

## Running Tests

**Backend**:
```bash
cd backend
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux
pytest tests/ -v
```

**Frontend**:
```bash
cd frontend
npm test
```

**Linting & type checks** (run these before opening a PR):
```bash
# Backend
ruff check src/ tests/ && mypy src/

# Frontend
npm run lint && npm run typecheck
```
