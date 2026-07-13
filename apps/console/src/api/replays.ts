import { request } from './client';

/* Real incident replays (spec §10) — the same fixtures the eval harness
   scores, served by /api/replays. Nothing here is fabricated: events come
   from the recorded incident stream and the Verge alert marker is computed
   by the actual engine run. */

export interface ReplaySummary {
  incidentId: string;
  title: string;
  zoneId: string;
  breachTs: string;
}

export interface ReplayEvent {
  time: number; // seconds from stream start
  type: 'reading' | 'permit' | 'shift' | 'breach' | 'verge-alert';
  title: string;
  sensor: string;
  value: string;
}

export interface ReplayTimeline {
  id: string;
  name: string;
  description: string;
  zoneId: string;
  duration: number; // seconds
  breachTs: string;
  vergeAlertTs: string | null;
  band: string | null;
  leadMin: number | null;
  events: ReplayEvent[];
}

export async function listReplays(signal?: AbortSignal): Promise<ReplaySummary[]> {
  return request<ReplaySummary[]>('/api/replays', { signal });
}

export async function getReplay(incidentId: string, signal?: AbortSignal): Promise<ReplayTimeline> {
  return request<ReplayTimeline>(`/api/replays/${encodeURIComponent(incidentId)}`, { signal });
}
