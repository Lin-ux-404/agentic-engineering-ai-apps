import { useEffect, useRef } from 'react';
import { create } from 'zustand';
import { OfflineError, apiFetch } from '../api/client';
import type {
  ActiveSessionResponse,
  BreakCountdownResponse,
  SessionSummaryResponse,
  SettingsResponse,
  TodayResponse,
} from '../api/types';

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export type TimerStatus = 'idle' | 'running' | 'paused' | 'break' | 'completed' | 'stopped_early';

interface TimerState {
  status: TimerStatus;

  sessionId: number | null;
  startAt: number | null;       // Unix ms
  configuredSeconds: number | null;
  pausedSeconds: number | null; // Accumulated paused seconds from backend
  pausedAt: number | null;      // Unix ms when current pause started; null if not paused

  remainingSeconds: number | null; // Computed each tick

  breakId: number | null;
  breakStartAt: number | null;       // Unix ms
  breakExpectedEndAt: number | null;  // Unix ms
  breakConfiguredSeconds: number | null;

  todaySessions: SessionSummaryResponse[];
  totalFocusedMinutes: number;

  settings: SettingsResponse;
  backendReachable: boolean;
}

interface TimerActions {
  hydrate: () => Promise<void>;
  startSession: () => Promise<void>;
  pauseSession: () => Promise<void>;
  resumeSession: () => Promise<void>;
  stopSession: () => Promise<void>;
  skipBreak: () => Promise<void>;
  tick: () => void;
  loadToday: () => Promise<void>;
  loadSettings: () => Promise<void>;
  saveSettings: (s: SettingsResponse) => Promise<void>;
}

const DEFAULT_SETTINGS: SettingsResponse = { focus_minutes: 25, break_minutes: 5 };

// ---------------------------------------------------------------------------
// Computed helpers
// ---------------------------------------------------------------------------

function computeRemaining(
  startAt: number,
  configuredSeconds: number,
  pausedSeconds: number,
  pausedAt: number | null,
): number {
  const now = Date.now();
  const elapsed = (now - startAt) / 1000;
  const currentPause = pausedAt !== null ? (now - pausedAt) / 1000 : 0;
  return configuredSeconds - elapsed + pausedSeconds + currentPause;
}

function applyActiveSession(
  session: ActiveSessionResponse,
): Partial<TimerState> {
  const startAt = new Date(session.start_at).getTime();
  const configuredSeconds = session.configured_minutes * 60;
  const pausedAt = session.paused_at ? new Date(session.paused_at).getTime() : null;

  const remaining =
    session.status === 'running' || session.status === 'paused'
      ? computeRemaining(startAt, configuredSeconds, session.paused_seconds, pausedAt)
      : 0;

  return {
    status: session.status as TimerStatus,
    sessionId: session.id,
    startAt,
    configuredSeconds,
    pausedSeconds: session.paused_seconds,
    pausedAt,
    remainingSeconds: remaining,
  };
}

function clearBreak(): Partial<TimerState> {
  return {
    breakId: null,
    breakStartAt: null,
    breakExpectedEndAt: null,
    breakConfiguredSeconds: null,
  };
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useTimerStore = create<TimerState & TimerActions>((set, get) => ({
  // Initial state
  status: 'idle',
  sessionId: null,
  startAt: null,
  configuredSeconds: null,
  pausedSeconds: null,
  pausedAt: null,
  remainingSeconds: null,
  breakId: null,
  breakStartAt: null,
  breakExpectedEndAt: null,
  breakConfiguredSeconds: null,
  todaySessions: [],
  totalFocusedMinutes: 0,
  settings: DEFAULT_SETTINGS,
  backendReachable: true,

  // Actions
  hydrate: async () => {
    try {
      const session = await apiFetch<ActiveSessionResponse | null>('/sessions/active');
      if (session && (session.status === 'running' || session.status === 'paused')) {
        set({ ...applyActiveSession(session), ...clearBreak(), backendReachable: true });
      } else {
        // No active session — check for active break
        const brk = await apiFetch<BreakCountdownResponse | null>('/breaks/active');
        if (brk && brk.status === 'active') {
          const breakStartAt = new Date(brk.start_at).getTime();
          const breakExpectedEndAt = new Date(brk.expected_end_at).getTime();
          set({
            status: 'break',
            sessionId: null,
            startAt: null,
            configuredSeconds: null,
            pausedSeconds: null,
            pausedAt: null,
            breakId: brk.id,
            breakStartAt,
            breakExpectedEndAt,
            breakConfiguredSeconds: brk.configured_minutes * 60,
            remainingSeconds: brk.remaining_seconds,
            backendReachable: true,
          });
        } else {
          set({
            status: 'idle', sessionId: null, startAt: null, configuredSeconds: null,
            pausedSeconds: null, pausedAt: null, remainingSeconds: null,
            ...clearBreak(), backendReachable: true,
          });
        }
      }
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
    }
    await get().loadToday();
    await get().loadSettings();
  },

  startSession: async () => {
    const { settings } = get();
    try {
      const session = await apiFetch<ActiveSessionResponse>('/sessions/start', {
        method: 'POST',
        body: JSON.stringify({ configured_minutes: settings.focus_minutes }),
      });
      set({ ...applyActiveSession(session), backendReachable: true });
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },

  pauseSession: async () => {
    const { sessionId } = get();
    if (sessionId === null) return;
    // Optimistic: freeze remaining before network round-trip
    const snapshot = get().remainingSeconds;
    set({ status: 'paused', pausedAt: Date.now() });
    try {
      const session = await apiFetch<ActiveSessionResponse>(
        `/sessions/${sessionId}/pause`,
        { method: 'POST' },
      );
      set({ ...applyActiveSession(session), backendReachable: true });
    } catch (err) {
      // Rollback optimistic update
      set({ status: 'running', pausedAt: null, remainingSeconds: snapshot });
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },

  resumeSession: async () => {
    const { sessionId } = get();
    if (sessionId === null) return;
    set({ status: 'running', pausedAt: null });
    try {
      const session = await apiFetch<ActiveSessionResponse>(
        `/sessions/${sessionId}/resume`,
        { method: 'POST' },
      );
      set({ ...applyActiveSession(session), backendReachable: true });
    } catch (err) {
      set({ status: 'paused' });
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },

  stopSession: async () => {
    const { sessionId } = get();
    if (sessionId === null) return;
    try {
      await apiFetch<ActiveSessionResponse>(`/sessions/${sessionId}/stop`, {
        method: 'POST',
      });
      set({
        status: 'idle', sessionId: null, startAt: null, configuredSeconds: null,
        pausedSeconds: null, pausedAt: null, remainingSeconds: null,
        ...clearBreak(), backendReachable: true,
      });
      await get().loadToday();
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },

  skipBreak: async () => {
    const { breakId } = get();
    if (breakId === null) return;
    try {
      await apiFetch<BreakCountdownResponse>(`/breaks/${breakId}/skip`, {
        method: 'POST',
      });
      set({
        status: 'idle',
        remainingSeconds: null,
        ...clearBreak(),
        backendReachable: true,
      });
      await get().loadToday();
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },

  tick: () => {
    const { status, startAt, configuredSeconds, pausedSeconds, pausedAt, sessionId, breakExpectedEndAt } = get();

    // Handle break countdown
    if (status === 'break' && breakExpectedEndAt !== null) {
      const remaining = Math.max(0, Math.round((breakExpectedEndAt - Date.now()) / 1000));
      if (remaining <= 0) {
        set({
          status: 'idle',
          remainingSeconds: null,
          ...clearBreak(),
        });
        // Trigger backend auto-finish on next read
        apiFetch<BreakCountdownResponse | null>('/breaks/active').catch(() => {});
      } else {
        set({ remainingSeconds: remaining });
      }
      return;
    }

    // Handle focus session countdown
    if (status !== 'running' || startAt === null || configuredSeconds === null || pausedSeconds === null) return;

    const remaining = computeRemaining(startAt, configuredSeconds, pausedSeconds, pausedAt);
    if (remaining <= 0) {
      set({ remainingSeconds: 0 });
      if (sessionId !== null) {
        apiFetch<ActiveSessionResponse>(`/sessions/${sessionId}/complete`, { method: 'POST' })
          .then(() => {
            // After completing, hydrate to pick up any auto-created break
            return get().hydrate();
          })
          .catch(() => {/* ignore — backend will auto-complete on next GET active */});
      }
    } else {
      set({ remainingSeconds: remaining });
    }
  },

  loadToday: async () => {
    try {
      const data = await apiFetch<TodayResponse>('/sessions/today');
      set({
        todaySessions: data.sessions,
        totalFocusedMinutes: data.total_focused_minutes,
        backendReachable: true,
      });
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
    }
  },

  loadSettings: async () => {
    try {
      const settings = await apiFetch<SettingsResponse>('/settings');
      set({ settings, backendReachable: true });
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
    }
  },

  saveSettings: async (newSettings: SettingsResponse) => {
    try {
      const saved = await apiFetch<SettingsResponse>('/settings', {
        method: 'PUT',
        body: JSON.stringify(newSettings),
      });
      set({ settings: saved, backendReachable: true });
    } catch (err) {
      if (err instanceof OfflineError) set({ backendReachable: false });
      else throw err;
    }
  },
}));

// ---------------------------------------------------------------------------
// Hook: timer tick + hydrate + visibility re-sync
// ---------------------------------------------------------------------------

export function useTimerService(): TimerState & TimerActions {
  const store = useTimerStore();
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    void store.hydrate();

    tickRef.current = setInterval(() => {
      useTimerStore.getState().tick();
    }, 200);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void useTimerStore.getState().hydrate();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (tickRef.current !== null) clearInterval(tickRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return store;
}
