# Quickstart: Validate Automatic Break Countdown Design

## Prerequisites

- Backend dependencies installed for `/home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/backend`
- Frontend dependencies installed for `/home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/frontend`
- Terminal access with `pwsh`, `python`, and `npm`

## 1. Start the application locally

### Backend

```bash
cd /home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/backend
make run
```

### Frontend

```bash
cd /home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/frontend
npm run dev
```

## 2. Exercise the core user stories

### Scenario A: Auto-start a break after a completed focus session

1. Open the app with default settings or set `break_minutes` to a non-zero value.
2. Start a short focus session (or use API-assisted fixtures in test/dev).
3. Let the session complete naturally.
4. Confirm:
   - the app transitions into a visible break state without another click,
   - the remaining break time is shown,
   - the status label clearly indicates that a break is active.

### Scenario B: Skip the active break

1. While the break countdown is active, activate `Skip break` using mouse and keyboard.
2. Confirm:
   - the break ends immediately,
   - the countdown is no longer shown as active,
   - the app returns to the ready state where `Start` is available again.

### Scenario C: Let the break finish naturally

1. Start another focus session and let it complete.
2. Allow the break countdown to reach zero.
3. Confirm:
   - the app does not continue showing an expired countdown,
   - the UI returns to a ready-to-start state.

### Scenario D: Zero-duration break bypass

1. Set `break_minutes` to `0`.
2. Complete a focus session.
3. Confirm no active break is shown and the app returns directly to the ready state.

### Scenario E: Visibility/reload resilience

1. Start a break and note the expected end time.
2. Switch tabs or reload the page midway through the break.
3. Confirm the remaining time reflects actual wall-clock time left rather than restarting from the full duration.

## 3. Validate automated checks

### Backend

```bash
cd /home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/backend
make lint
make typecheck
make test
```

### Frontend

```bash
cd /home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/frontend
npm run lint
npm run typecheck
npm test
```

## 4. Validate API contract alignment

1. Start the backend.
2. Refresh generated frontend types if the OpenAPI contract changes:

```bash
cd /home/reeissin/code/microsoft/forks/agentic-engineering-ai-apps/frontend
npm run generate:types
```

3. Verify the generated schema includes:
   - `GET /breaks/active`
   - `POST /breaks/{breakId}/skip`
   - `break_minutes` accepting `0`

## Expected readiness signal

The design is ready for task generation when the manual scenarios above are clear, the contract shapes are settled, and the backend/frontend test additions can be mapped directly to implementation work.
