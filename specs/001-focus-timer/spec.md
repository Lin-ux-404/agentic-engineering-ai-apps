# Feature Specification: Personal Focus Timer (Workday Pomodoro)

**Feature Branch**: `001-focus-timer`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Build a Personal Focus Timer (Workday Pomodoro) application that helps knowledge workers protect and track focused work time throughout the workday."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start and Complete a Focus Session (Priority: P1)

A knowledge worker opens the application, presses a single "Start" button, and sees a visible countdown
timer running from 25 minutes to zero. When the countdown reaches zero, the session is automatically
marked "Completed" and the today summary is updated. The worker can close or minimize the app at any
point and return to find the timer still running correctly.

**Why this priority**: This is the core value proposition. Without a reliable start-to-complete cycle,
the application has no value. Every other story depends on this foundation.

**Independent Test**: Open the app in idle state, press Start, observe the countdown reduce each second,
leave the tab for 60 seconds, return and confirm elapsed time is correct, let the full 25-minute duration
elapse (or use a configured shorter test duration), and confirm a "Completed" session appears in the
today panel with the correct focused minutes and an accurate start and end timestamp.

**Acceptance Scenarios**:

1. **Given** the app is in Idle state, **When** the user presses "Start", **Then** the timer begins
   counting down from the configured focus duration, the state label changes to "Running", and the
   "Stop" button becomes the primary control.
2. **Given** a session is Running, **When** the user switches to another browser tab for any amount
   of time, **Then** on returning the timer shows the correct remaining time based on elapsed wall-clock
   time, not a paused or reset value.
3. **Given** a session is Running and the countdown reaches zero, **Then** the session is automatically
   marked "Completed", the timer resets to Idle, and the today panel shows an updated total focused
   minutes and a new session row with status "Completed".
4. **Given** a Completed session exists in today's list, **When** the user refreshes the page, **Then**
   the session remains in the today panel.

---

### User Story 2 - Pause and Resume a Session (Priority: P2)

A knowledge worker is mid-session and is interrupted. They press "Pause" to suspend the timer. The
countdown freezes. When the interruption ends, they press "Resume" and the countdown continues from
where it paused. The final session record reflects only the time spent actively focusing, not the time
spent paused.

**Why this priority**: Real interruptions happen. Without pause/resume, users would stop sessions
prematurely, inflating "Stopped early" counts and undermining trust in session records.

**Independent Test**: Start a session, press Pause after 2 minutes, wait 3 minutes, press Resume,
let the session complete, and verify the recorded focused time equals the active (non-paused) duration
and the session is still marked "Completed".

**Acceptance Scenarios**:

1. **Given** a session is Running, **When** the user presses "Pause", **Then** the countdown freezes,
   the state label changes to "Paused", and a "Resume" button becomes the primary control.
2. **Given** a session is Paused, **When** the user presses "Resume", **Then** the countdown continues
   from the remaining time, the state label changes back to "Running", and paused time is not added to
   focused duration.
3. **Given** a session was paused for 5 minutes and then resumed and completed, **When** the session
   record is inspected, **Then** the recorded focused time excludes the 5 paused minutes.
4. **Given** a session is Paused and the user refreshes the page, **Then** the session remains in
   Paused state at the same remaining time.

---

### User Story 3 - Stop a Session Early (Priority: P3)

A knowledge worker needs to end a session before the timer reaches zero — for example, a meeting was
called. They press "Stop". The session is saved immediately with the actual focused duration up to
that point and marked "Stopped early". The app returns to Idle state.

**Why this priority**: Users must be able to exit cleanly without losing the record of partial work
done. This also prevents the system from ever being "stuck" in a running state.

**Independent Test**: Start a session, press Stop after 8 minutes, verify a "Stopped early" session
row appears in the today panel showing approximately 8 minutes, and verify the app is in Idle state
ready for a new session.

**Acceptance Scenarios**:

1. **Given** a session is Running or Paused, **When** the user presses "Stop", **Then** the session
   is saved with status "Stopped early", the focused duration reflects only the active (non-paused)
   elapsed time, and the app returns to Idle state.
2. **Given** the user presses Stop and the session is saved, **When** the user immediately starts a
   new session, **Then** the new session starts cleanly with no carry-over data from the stopped session.
3. **Given** a "Stopped early" session exists, **When** the user refreshes the page, **Then** the
   session remains in the today panel with correct status and duration.

---

### User Story 4 - Review Today's Focus Summary (Priority: P4)

A knowledge worker wants to see how much focused time they have accumulated today. The today panel
shows a total of focused minutes, and a list of individual sessions with start time, duration, and
status.

**Why this priority**: Visibility into daily progress is the motivational payoff. It is valuable but
depends on sessions being recorded (Stories 1–3) and is not strictly required for a session to start.

**Independent Test**: Complete two sessions and stop one early in the same calendar day. Verify the
today panel shows: total focused minutes equal to the sum of the two completed/partial session
durations, and three session rows with correct individual start times, durations, and status labels.

**Acceptance Scenarios**:

1. **Given** no sessions have been recorded today, **When** the user opens the app, **Then** the today
   panel shows "0 min" total with an empty session list.
2. **Given** multiple sessions exist for today, **When** the user views the today panel, **Then**
   total focused minutes equals the sum of active (non-paused) durations across all sessions regardless
   of status.
3. **Given** a session includes an optional note, **When** the user views the today panel, **Then**
   the session row displays the note alongside start time, duration, and status.
4. **Given** sessions were recorded on a previous calendar day, **When** the user opens the app the
   next day, **Then** total focused minutes resets to zero and the session list shows no previous-day
   sessions.

---

### User Story 5 - Configure Default Durations (Priority: P5)

A knowledge worker wants to customize their default focus duration (e.g., 50 minutes instead of 25)
and break duration (e.g., 10 minutes instead of 5). The setting persists across page refreshes and
applies to all subsequently started sessions.

**Why this priority**: The default 25/5 split does not fit all workers. This is a quality-of-life
feature — the app functions correctly at defaults, so this is the lowest-priority story.

**Independent Test**: Open settings, change focus duration to 50 minutes, save, refresh the page,
start a session, and verify the countdown begins at 50:00.

**Acceptance Scenarios**:

1. **Given** the user opens settings, **When** they change focus duration to a positive integer number
   of minutes and save, **Then** the next session started uses that duration.
2. **Given** the user has saved custom durations, **When** they refresh the page, **Then** the custom
   durations are still in effect.
3. **Given** the user enters an invalid value (zero, negative, or non-numeric) for a duration, **Then**
   the system does not accept the value and displays a clear validation message.

---

### Edge Cases

- **Simultaneous session attempt**: If the user somehow triggers "Start" while a session is already
  Running or Paused (e.g., via a rapid double-click), the second start request MUST be rejected and
  the active session MUST continue undisturbed.
- **App open in multiple tabs**: If the same app is open in two browser tabs and a session is already
  running in one, the second tab MUST show the current running state and remaining time, and MUST NOT
  allow a second session to start.
- **Session at midnight boundary**: If a session starts on one calendar day and ends on the next,
  the session MUST be attributed to the day on which it started.
- **Backend unavailable on load**: If the backend cannot be reached when the app loads, the UI MUST
  display a degraded-mode banner and MUST NOT render stale or incorrect time data.
- **Zero remaining time while paused**: If a session's configured duration elapses while the timer is
  in Paused state, the session MUST NOT auto-complete; it MUST remain Paused until the user resumes
  or stops it, at which point it transitions appropriately.
- **Note field**: An empty note MUST be treated identically to a session with no note; no validation
  error should appear.

## Requirements *(mandatory)*

### Functional Requirements

**Timer lifecycle**

- **FR-001**: Users MUST be able to start a new focus session from Idle state with a single action.
- **FR-002**: Users MUST be able to pause a Running session, causing the countdown to freeze.
- **FR-003**: Users MUST be able to resume a Paused session, causing the countdown to continue from
  the frozen value.
- **FR-004**: Users MUST be able to stop a Running or Paused session at any time; the session MUST
  be saved as "Stopped early" with the accumulated focused duration.
- **FR-005**: When the countdown reaches zero, the system MUST automatically end the session and
  record it as "Completed" without requiring user action.
- **FR-006**: The system MUST prevent more than one active session (Running or Paused) from existing
  at a time; a new start request MUST be rejected if an active session exists.

**Timer accuracy and persistence**

- **FR-007**: The countdown MUST be computed from persisted wall-clock start and pause timestamps,
  not from accumulated tick counts.
- **FR-008**: Session state (Running, Paused, remaining time) MUST survive a page refresh; the user
  MUST NOT need to take any action to restore the session.
- **FR-009**: The system MUST persist session state at every state transition (start, pause, resume,
  stop, complete).

**Session records**

- **FR-010**: Each session record MUST store: start timestamp, end timestamp, total focused duration
  (excluding paused time), status (Completed or Stopped early), and an optional user-provided note.
- **FR-011**: Session records MUST be retained durably on the user's local machine and MUST NOT
  be lost due to a page refresh or normal application restart.
- **FR-012**: Session records MUST never be modified after the session ends; the record reflects what
  actually happened.

**Today panel**

- **FR-013**: The today panel MUST display the total focused minutes for the current calendar day,
  computed as the sum of focused durations across all sessions started today.
- **FR-014**: The today panel MUST list each session started today with: start time, focused duration,
  and status label ("Completed" or "Stopped early").
- **FR-015**: The today panel MUST support displaying an optional note per session if one was entered.

**Configuration**

- **FR-016**: The system MUST provide a default focus duration of 25 minutes and a default break
  duration of 5 minutes; these MUST be configurable by the user.
- **FR-017**: Configured durations MUST persist across page refreshes.
- **FR-018**: The system MUST reject duration values that are not positive integers.

**State visibility**

- **FR-019**: The current timer state (Idle, Running, Paused, Break) MUST be visible at all times.
- **FR-020**: The remaining focus time MUST be displayed in mm:ss format and MUST update at least
  once per second while Running.
- **FR-021**: If the backend is unavailable, the UI MUST display a clear degraded-mode message and
  MUST NOT display potentially stale timer data as if it were live.

### Key Entities

- **Focus Session**: A single timed work interval. Attributes: unique ID, start timestamp, end
  timestamp, configured duration, total focused duration (wall-clock active time excluding pauses),
  status (Completed | Stopped early), optional note, date key (YYYY-MM-DD of start time).
- **Pause Record**: A sub-record attached to a session representing one pause interval. Attributes:
  session ID, pause start timestamp, pause end timestamp (null while paused). Multiple pause records
  may exist per session.
- **Settings**: User-level configuration record. Attributes: focus duration (minutes), break duration
  (minutes). Singleton per installation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can start a focus session in 2 seconds or fewer from the moment the app is
  interactive, using only a keyboard.
- **SC-002**: Timer drift is under 1 second over the full default 25-minute session duration.
- **SC-003**: Session records are accurate: focused duration matches the actual active (non-paused)
  time within a 1-second margin.
- **SC-004**: The app becomes interactive (today panel loaded, timer state restored) within 2 seconds
  of page load under normal operating conditions.
- **SC-005**: 100% of state transitions (start, pause, resume, stop, complete) result in a persisted
  record; no transition is ever silently lost.
- **SC-006**: All interactive controls are operable via keyboard alone with no mouse required.
- **SC-007**: The today panel total is always consistent with the sum of individual session focused
  durations — no rounding or inflation.

## Assumptions

- The application is a locally-run web app (browser-based frontend + local backend service); no
  cloud infrastructure is required for v1.
- There is only one user per installation; no multi-user or profile-switching is needed.
- The app runs on a desktop or laptop browser; mobile browser support is out of scope for v1.
- A "day" boundary is midnight local time; sessions are attributed to the day on which they start.
- Optional break tracking (an explicit break timer) is noted in the feature description but is
  considered a post-MVP enhancement; only the break duration configuration setting is stored.
- Sound/vibration completion cue is noted as optional and is out of scope for v1 unless trivially
  implementable; it is not a success criterion.
- Data retention policy defaults to indefinite (all sessions kept until the user deletes them);
  no automatic pruning is applied for v1.
