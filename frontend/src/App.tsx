import { useState } from 'react';
import { Controls } from './components/Controls';
import { SettingsModal } from './components/SettingsModal';
import { TimerDisplay } from './components/TimerDisplay';
import { TodaySummary } from './components/TodaySummary';
import { useTimerService } from './hooks/useTimerService';

export function App() {
  const {
    status,
    remainingSeconds,
    todaySessions,
    totalFocusedMinutes,
    settings,
    backendReachable,
    startSession,
    pauseSession,
    resumeSession,
    stopSession,
    skipBreak,
    saveSettings,
  } = useTimerService();

  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="app">
      {!backendReachable && (
        <div className="offline-banner" role="alert" aria-live="assertive">
          Offline — data may not be saved
        </div>
      )}

      <header className="app-header">
        <h1>🍅 Focus Timer</h1>
        <button
          className="btn btn-ghost"
          onClick={() => setShowSettings(true)}
          aria-label="Open settings"
        >
          ⚙ Settings
        </button>
      </header>

      <main className="app-main">
        <TimerDisplay status={status} remainingSeconds={remainingSeconds} />
        <Controls
          status={status}
          onStart={() => { void startSession(); }}
          onPause={() => { void pauseSession(); }}
          onResume={() => { void resumeSession(); }}
          onStop={() => { void stopSession(); }}
          onSkipBreak={() => { void skipBreak(); }}
        />
        <TodaySummary
          sessions={todaySessions}
          totalFocusedMinutes={totalFocusedMinutes}
        />
      </main>

      {showSettings && (
        <SettingsModal
          settings={settings}
          onSave={saveSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
