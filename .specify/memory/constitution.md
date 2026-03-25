<!--
SYNC IMPACT REPORT
==================
Version change  : [CONSTITUTION_VERSION] → 1.0.0
Bump rationale  : Initial ratification — all template placeholders replaced for the first time.
Modified principles: N/A (initial fill)
Added sections  :
  - Core Principles I–IX (user-centered product principles + code quality principles)
  - Testing Standards
  - UX Consistency Standards
  - Performance & Reliability Requirements
  - Security Requirements
  - Governance
Removed sections: N/A
Templates reviewed:
  - .specify/templates/plan-template.md  ✅ "Constitution Check" gate is per-feature; no structural change needed
  - .specify/templates/spec-template.md  ✅ No structural changes required
  - .specify/templates/tasks-template.md ✅ Task phase structure compatible; no structural change needed
  - .specify/templates/checklist-template.md ✅ No structural changes required
  - .specify/templates/commands/         ✅ No command files present; nothing to update
Deferred TODOs  : none
-->

# Personal Focus Timer Constitution

## Core Principles

### I. Focus-First Design

The UI MUST minimize distraction at every decision point:

- No noisy animations; transitions are only permitted when they serve orientation or state feedback.
- Minimal UI surface: only controls relevant to the current timer state are prominently displayed.
- One primary call-to-action per screen ("Start" when idle, "Stop" when active); secondary actions MUST
  be visually subordinate and never compete with the primary action.

**Rationale**: The product's singular value proposition is helping users focus. Any UI element that
competes with that goal directly undermines the product.

### II. Predictable & Deterministic Behavior

Timer behavior MUST be consistent and reproducible regardless of tab switching, browser refresh, or short
connectivity loss:

- Timer state MUST be derived from persisted wall-clock timestamps, not accumulated tick counts.
- On reload, the app MUST restore state from the last persisted snapshot without requiring user action.
- Short connectivity loss (< 30 s) MUST NOT cause data loss or state corruption.

**Rationale**: Users build trust through consistency. An unpredictable timer is worse than no timer.

### III. User Trust Through Honest Reporting

Session records MUST reflect actual user behavior with no inflation of focus time:

- "Completed" MUST only be assigned when a full session duration elapsed without being stopped.
- "Stopped early" MUST be recorded when a session ends before its target duration.
- "Paused" MUST be tracked separately; paused time MUST NOT count toward focused time.
- Summary calculations (daily focus totals, session history) MUST be derived from raw records and
  MUST NOT be rounded up.

**Rationale**: Inflated session data erodes the user's ability to accurately assess their own
productivity. Honest recording is a non-negotiable contract with the user.

### IV. Privacy by Default

All user data MUST remain local on the user's machine unless the user explicitly opts in to cloud sync:

- The backend MUST bind to `127.0.0.1` (localhost) only; external-facing endpoints are prohibited.
- No telemetry, analytics, or error reporting MUST be transmitted to external services without explicit
  user consent.
- Storage is SQLite in the application's designated data directory; no third-party cloud storage by default.

**Rationale**: A focus timer tracks behavioral patterns. Trust requires local-only defaults from day one.

### V. Accessibility First

The application MUST meet WCAG 2.1 AA accessibility requirements from the initial release:

- All interactive controls MUST be keyboard-operable (Tab / Enter / Space).
- All timer state indicators and controls MUST carry meaningful ARIA labels for screen readers.
- Color contrast MUST meet a minimum 4.5:1 ratio for normal text and 3:1 for large text / icons.
- Focus states MUST be clearly visible and MUST NOT be suppressed.

**Rationale**: Accessibility is not optional polish — it is a baseline quality requirement that is
far cheaper to implement from the start than to retrofit later.

### VI. Readable Over Clever

Code MUST optimize for long-term maintainability over short-term cleverness:

- Prefer explicit, straightforward implementations over terse or "magic" alternatives.
- Avoid premature abstractions; introduce shared utilities only when a pattern recurs three or more times.
- Variable and function names MUST express intent without requiring inline comments to decode them.

**Rationale**: Features are built once but maintained many times. Readable code reduces the cost of
every future change.

### VII. Small, Composable Components

React components MUST be small and single-purpose:

- A component MUST NOT own more than one major concern (e.g., data fetching AND display AND business
  logic combined in one component).
- Components exceeding ~150 lines or holding multiple unrelated responsibilities are prohibited.
- Business logic MUST live in hooks or service modules, not in JSX render functions.

**Rationale**: Small components are independently testable, reusable, and easier to reason about under
change. God components are a maintenance liability.

### VIII. Typed Boundaries

All public interfaces MUST use strict types:

- TypeScript `strict` mode MUST be enabled; `any` type assertions require an inline comment justifying
  the escape hatch.
- Backend request and response models MUST be defined as Pydantic models; untyped dicts MUST NOT appear
  at API boundaries.
- Data transfer objects (DTOs) exchanged between frontend and backend MUST be sourced from a shared
  schema definition (OpenAPI or equivalent) to prevent drift.

**Rationale**: Type-checked boundaries catch entire classes of bugs before runtime and serve as
living documentation of the interface contract.

### IX. Single Source of Truth for Timer State

Timer state MUST be owned in exactly one place:

- A dedicated state machine or timer service hook is the canonical owner of all timer state.
- UI components MUST read from that single source and MUST NOT maintain local copies of timer values.
- All mutations of timer state MUST go through the canonical service; direct state patches from
  rendering code are prohibited.

**Rationale**: Duplicate state leads to divergence bugs. Centralizing state makes every transition
auditable and testable.

## Testing Standards

All tests MUST validate behavior and outcomes, not implementation details:

- Tests MUST assert on state transitions, persisted session records, and API contract compliance —
  not on private methods or internal variables.
- Tests MUST NOT be deleted or skipped to make a PR pass; a failing test is a signal, not an obstacle.

**Critical paths — full branch coverage REQUIRED**:

- Timer lifecycle: `start` → `pause` → `resume` → `stop` → `complete` (each transition tested in
  isolation and in sequence)
- Persistence across refresh: in-progress state survives a page reload
- Session summary calculations: completed time, paused time, and status label accuracy
- Concurrency guard: starting a second session while one is already active MUST be rejected

**Frontend testing**:

- Pure logic (state machine transitions, time calculations): unit tests.
- Key user interactions (start/stop/pause flows, degraded-mode banner visibility): component tests
  using React Testing Library or equivalent.

**Backend testing**:

- Timer and session business rules: unit tests.
- Endpoint contract compliance, including error cases: API integration tests against a real test database.

**CI gate — PRs MUST pass all of the following before merge**:

- All tests (unit + integration + component)
- Lint (`eslint` / `ruff` or project equivalent)
- Type-check (`tsc --noEmit` / `mypy` or project equivalent)

## UX Consistency Standards

The following terminology MUST be used consistently across all UI surfaces, API responses, help text,
error messages, and logs:

| Term | Meaning |
|---|---|
| Focus session | A timed work interval initiated by the user |
| Break | A rest interval between focus sessions |
| Paused | Session temporarily suspended; timer not running |
| Completed | Full session duration elapsed without being stopped |
| Stopped early | User ended the session before its target duration elapsed |

Rules:

- One primary CTA per screen: "Start" when idle / "Stop" when active. Dual-purpose or ambiguous buttons
  are prohibited.
- The user MUST always be able to see: current timer state, remaining time, and what action comes next.
  These three elements MUST be present and legible at all times during an active session.
- State label and remaining time MUST be the most visually prominent elements on screen during an active
  session (largest text, highest contrast).
- UI copy MUST use the terms above exactly; synonyms ("Cancel", "End", "Finish", "Abort") MUST NOT
  replace the defined terms.

## Performance & Reliability Requirements

**Startup**: The app MUST become interactive (timer state loaded and rendered) within 2 seconds on a
local machine. No blocking network calls are permitted on the initial load path.

**Timer accuracy**: All duration calculations MUST use wall-clock timestamps (`Date.now()` on the
frontend, `datetime.utcnow()` or equivalent on the backend). Tick-count accumulation MUST NOT be
used as the source of truth for elapsed time. Acceptable drift: < 1 second over a 25-minute session.

**Resilience — degraded mode**:

- If the backend is unreachable, the UI MUST display a clearly visible "Offline — data may not be
  saved" banner.
- The frontend MUST NOT silently discard user actions when the backend is unavailable.
- The app MUST NOT crash or enter an unrecoverable state due to a backend timeout or error.

**No data loss**:

- Session state MUST be persisted to SQLite at every state transition (start, pause, resume, stop,
  complete).
- An in-progress session MUST be recoverable after an unexpected application restart.

## Security Requirements

**Network exposure**: The backend MUST bind exclusively to `127.0.0.1`. Binding to `0.0.0.0` or any
external-facing interface is prohibited without an explicit, reviewed security exception.

**Input validation**: All API inputs MUST be validated server-side (via Pydantic or equivalent) before
processing. Client-supplied values MUST NOT be passed to the data layer without validation.

**Safe defaults**:

- The application MUST only read from and write to its designated data directory.
- Arbitrary file system access, path traversal, and dynamic code execution from user-supplied input
  are prohibited.
- Dependencies MUST be pinned to specific versions in lock files (`package-lock.json`, `poetry.lock`,
  or equivalent) to ensure reproducible and auditable builds.

**No sensitive data in logs**: Session records (IDs, timestamps, durations, status) may be logged
locally for debugging purposes. No personally identifiable information beyond what the user explicitly
records MUST be written to logs or error reports.

## Governance

- This constitution supersedes all other project practices. Where a conflict exists between this document
  and any other guideline, this document takes precedence.
- **Amendment procedure**: Amendments MUST be submitted as a PR that updates this file, increments the
  version following semantic versioning rules below, and includes an updated Sync Impact Report comment.
- **Versioning policy**:
  - **MAJOR**: A principle is removed, fundamentally redefined, or rendered backward-incompatible.
  - **MINOR**: A new principle or major section is added or materially expanded.
  - **PATCH**: Clarifications, wording improvements, or non-semantic refinements.
- **Compliance review**: Every implementation plan (`plan.md`) MUST include a "Constitution Check"
  section verifying that the planned work complies with each applicable principle before work begins.
- **Enforcement**: Reviewers are empowered — and expected — to block a PR that violates a principle,
  citing the specific principle by Roman numeral.

**Version**: 1.0.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
