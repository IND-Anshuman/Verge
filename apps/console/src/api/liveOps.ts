/** Live Ops feeds — voice, vision (with frameUri), lessons. Honest empties. */

export interface VoiceEventRow {
  eventId: string;
  ts: string;
  transcript: string;
  zoneId?: string | null;
  hazards?: string[];
  source?: string;
}

export interface VisionDetectionRow {
  detectionId: string;
  ts: string;
  cameraId: string;
  zoneId: string;
  label: string;
  confidence: number;
  /** Browser path `/api/vision/frames/…` or s3:// when only storage exists. */
  frameUri?: string | null;
}

export interface LessonCardRow {
  lessonId: string;
  title: string;
  summary?: string;
  sourceRefs?: string[];
  findingId?: string | null;
}

function isHttpFrame(uri: string | null | undefined): boolean {
  if (!uri) return false;
  return uri.startsWith('/api/') || uri.startsWith('http://') || uri.startsWith('https://');
}

export function displayableFrameSrc(uri: string | null | undefined): string | null {
  return isHttpFrame(uri) ? uri! : null;
}

export async function fetchVoiceEvents(limit = 12): Promise<VoiceEventRow[]> {
  const res = await fetch(`/api/voice/events?limit=${limit}`);
  if (!res.ok) throw new Error(`voice ${res.status}`);
  const body = (await res.json()) as { events?: VoiceEventRow[] };
  return body.events ?? [];
}

export async function fetchVisionEvents(limit = 12): Promise<VisionDetectionRow[]> {
  const res = await fetch(`/api/vision/events?limit=${limit}`);
  if (!res.ok) throw new Error(`vision ${res.status}`);
  const body = (await res.json()) as { detections?: VisionDetectionRow[] };
  return body.detections ?? [];
}

export async function fetchProactiveLessons(zoneId: string): Promise<LessonCardRow[]> {
  const res = await fetch(`/api/lessons/proactive?zoneId=${encodeURIComponent(zoneId)}`);
  if (!res.ok) throw new Error(`lessons ${res.status}`);
  const body = (await res.json()) as { proactiveCards?: LessonCardRow[] };
  return body.proactiveCards ?? [];
}
