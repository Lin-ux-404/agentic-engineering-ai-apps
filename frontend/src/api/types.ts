export interface ActiveSessionResponse {
  id: number;
  start_at: string;
  end_at: string | null;
  status: 'running' | 'paused' | 'completed' | 'stopped_early';
  configured_minutes: number;
  paused_seconds: number;
  paused_at: string | null;
  remaining_seconds: number;
  note: string | null;
}

export interface SessionSummaryResponse {
  id: number;
  start_at: string;
  end_at: string | null;
  status: 'running' | 'paused' | 'completed' | 'stopped_early';
  focused_seconds: number | null;
  note: string | null;
}

export interface TodayResponse {
  date: string;
  total_focused_minutes: number;
  sessions: SessionSummaryResponse[];
}

export interface SettingsResponse {
  focus_minutes: number;
  break_minutes: number;
}

export interface BreakCountdownResponse {
  id: number;
  session_id: number;
  start_at: string;
  expected_end_at: string;
  configured_minutes: number;
  remaining_seconds: number;
  status: 'active' | 'skipped' | 'finished';
  skipped_at: string | null;
  finished_at: string | null;
}
