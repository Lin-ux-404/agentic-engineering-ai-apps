import React from 'react';
import type { TimerStatus } from '../hooks/useTimerService';

interface Props {
  status: TimerStatus;
  remainingSeconds: number | null;
}

function formatTime(seconds: number): string {
  const s = Math.max(0, Math.ceil(seconds));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

const STATUS_LABELS: Record<TimerStatus, string> = {
  idle: 'Idle',
  running: 'Running',
  paused: 'Paused',
  break: 'Break',
  completed: 'Completed',
  stopped_early: 'Stopped early',
};

export const TimerDisplay = React.memo(function TimerDisplay({ status, remainingSeconds }: Props) {
  const timeLabel =
    remainingSeconds !== null ? formatTime(remainingSeconds) : '--:--';

  return (
    <div className="timer-display" data-status={status}>
      <div
        className="timer-countdown"
        aria-live="polite"
        aria-label={`Timer: ${timeLabel}`}
        role="timer"
      >
        {timeLabel}
      </div>
      <div
        className="timer-status"
        role="status"
        aria-label={`Status: ${STATUS_LABELS[status]}`}
      >
        {STATUS_LABELS[status]}
      </div>
    </div>
  );
});
