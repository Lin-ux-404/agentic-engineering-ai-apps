# Phase 0 Research: Automatic Break Countdown

## Decision: Persist breaks as first-class backend records

**Rationale**: The constitution requires deterministic timer recovery from wall-clock timestamps across reloads and tab switches. A dedicated `breaks` table with `start_at`, `expected_end_at`, and terminal status makes the break lifecycle auditable, avoids duplicating timing rules in the UI, and preserves the distinction between a completed focus session and the rest period that follows it.

**Alternatives considered**:
- Derive break state only in the frontend after session completion: rejected because it would be lost on reload and violate predictable recovery.
- Reuse the `sessions` table/status for breaks: rejected because it would blur focus-session reporting and break the “completed vs stopped early” trust boundary.

## Decision: Expose dedicated break endpoints instead of overloading session endpoints

**Rationale**: The existing API separates session and settings concerns cleanly. Adding `GET /breaks/active` and `POST /breaks/{breakId}/skip` keeps typed boundaries explicit, lets the frontend hydrate break state independently of active focus sessions, and avoids changing the meaning of `/sessions/active`.

**Alternatives considered**:
- Add break data only as an optional nested field on `/sessions/active`: rejected because `/sessions/active` currently returns `null` when no focus session is active, which would make break hydration awkward and semantically confusing.
- Trigger skip through `/sessions/{id}/complete` or `/sessions/{id}/stop`: rejected because skip-break acts on a different lifecycle object with different validation rules.

## Decision: Snapshot the configured break duration at focus completion time

**Rationale**: The feature spec explicitly states that the upcoming automatic break should use the break duration in effect when the focus session completes. Persisting `configured_minutes` (or derived seconds) onto the break record ensures later settings changes do not retroactively mutate an active break.

**Alternatives considered**:
- Always read the latest `settings.break_minutes` while a break is active: rejected because editing settings mid-break would unexpectedly change the current countdown.
- Store only `expected_end_at` without the configured duration: rejected because duration snapshots are useful for auditability, testing, and rebuilding projections.

## Decision: Allow `break_minutes = 0` and bypass break creation entirely

**Rationale**: The spec requires zero-duration breaks to return directly to a ready state without showing a meaningless countdown. Supporting `0..120` for `break_minutes` at the model/database boundary is simpler and more honest than creating an immediately-expired break that the UI must special-case away.

**Alternatives considered**:
- Continue validating break duration as `1..120`: rejected because it conflicts with FR-011 and the edge-case requirements.
- Create a zero-second break record and auto-finish it: rejected because it adds unnecessary records and complicates status handling for no user benefit.

## Decision: Keep the frontend timer service as the sole UI state owner

**Rationale**: Constitution Principle IX requires one canonical UI owner for timer state. The backend persists break facts, while `frontend/src/hooks/useTimerService.ts` remains the only place that translates active session + active break responses into display status, countdown values, and control availability.

**Alternatives considered**:
- Add local break state inside `Controls` or `TimerDisplay`: rejected because it would fragment state ownership and make transitions harder to test.
- Create a second independent frontend store for breaks: rejected because focus and break are a single timer workflow and should remain coordinated in one service.

## Decision: Validate the feature with backend integration tests and frontend component/store tests

**Rationale**: The constitution requires behavior-focused tests on state transitions and typed contracts. Backend tests will cover break creation, skip, expiry, and zero-duration bypass; frontend tests will cover break labels, skip action availability, and timer rehydration behavior.

**Alternatives considered**:
- Rely only on manual validation: rejected because this is a critical timer-state transition with persistence requirements.
- Test only UI rendering: rejected because backend timing rules and API contract changes are central to the feature.
