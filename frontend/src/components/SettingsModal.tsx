import React, { useEffect, useRef, useState } from 'react';
import type { SettingsResponse } from '../api/types';
import { ApiError } from '../api/client';

interface Props {
  settings: SettingsResponse;
  onSave: (settings: SettingsResponse) => Promise<void>;
  onClose: () => void;
}

export function SettingsModal({ settings, onSave, onClose }: Props) {
  const [focusMinutes, setFocusMinutes] = useState(String(settings.focus_minutes));
  const [breakMinutes, setBreakMinutes] = useState(String(settings.break_minutes));
  const [error, setError] = useState<string | null>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstInputRef.current?.focus();
  }, []);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  const validate = (): string | null => {
    const fm = Number(focusMinutes);
    const bm = Number(breakMinutes);
    if (!Number.isInteger(fm) || fm < 1 || fm > 480) {
      return 'Focus duration must be a whole number between 1 and 480.';
    }
    if (!Number.isInteger(bm) || bm < 0 || bm > 120) {
      return 'Break duration must be a whole number between 0 and 120.';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await onSave({ focus_minutes: Number(focusMinutes), break_minutes: Number(breakMinutes) });
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Save failed: ${err.detail}`);
      } else {
        setError('Save failed. Please try again.');
      }
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Settings"
    >
      <div className="modal-content">
        <h2>Settings</h2>
          <form onSubmit={(e) => { void handleSubmit(e); }} noValidate>
          <label htmlFor="focus-minutes">Focus duration (minutes)</label>
          <input
            id="focus-minutes"
            ref={firstInputRef}
            type="number"
            value={focusMinutes}
            onChange={(e) => { setFocusMinutes(e.target.value); setError(null); }}
            min={1}
            max={480}
            aria-label="Focus duration in minutes"
          />

          <label htmlFor="break-minutes">Break duration (minutes)</label>
          <input
            id="break-minutes"
            type="number"
            value={breakMinutes}
            onChange={(e) => { setBreakMinutes(e.target.value); setError(null); }}
            min={0}
            max={120}
            aria-label="Break duration in minutes"
          />

          {error ? (
            <p className="settings-error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="modal-actions">
            <button type="submit" className="btn btn-primary" aria-label="Save settings">
              Save
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              aria-label="Cancel and close settings"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
