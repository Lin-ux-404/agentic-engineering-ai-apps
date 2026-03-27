import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { useTimerService, useTimerStore } from '../useTimerService';

describe('TimerService — US2', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        (globalThis as Record<string, unknown>).fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ break_minutes: 5 }),
        });
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it('transitions to break state after session completes', async () => {
        const { result } = renderHook(() => useTimerService());

        // Start a session
        await act(async () => {
            await result.current.startSession();
        });

        // Advance timer until remaining_seconds hits 0
        act(() => {
            while ((result.current.remainingSeconds ?? 0) > 0) {
                vi.advanceTimersByTime(1000);
            }
        });

        // Assert store status === 'break' and remaining break seconds === 300
        expect(result.current.status).toBe('break');
        expect(result.current.remainingSeconds).toBe(300);
    });

    it('skip break returns to idle', async () => {
        const { result } = renderHook(() => useTimerService());

        // Start a session
        await act(async () => {
            await result.current.startSession();
        });

        // Advance timer until remaining_seconds hits 0 to enter break state
        act(() => {
            while ((result.current.remainingSeconds ?? 0) > 0) {
                vi.advanceTimersByTime(1000);
            }
        });

        expect(result.current.status).toBe('break');

        // Call skipBreak to return to idle
        await act(async () => {
            await result.current.skipBreak();
        });

        // Assert store status === 'idle'
        expect(result.current.status).toBe('idle');
    });

    it('useTimerStore is exported for direct access', () => {
        expect(useTimerStore).toBeDefined();
    });
});