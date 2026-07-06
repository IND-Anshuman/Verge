import { request } from './client';

export interface MemoryStatus {
  dataset: string;
  configured: boolean;
  degraded: boolean;
  reason?: string;
}

export interface AlertPreview {
  languages: Record<string, string>;
  degraded: boolean;
  reason?: string;
}

export interface EvidenceManifest {
  packId?: string;
  findingId?: string;
  items?: unknown[];
  manifestHash?: string;
  degraded?: boolean;
  reason?: string;
  objectStore?: { bucket: string; key: string };
}

export async function getMemoryStatus(signal?: AbortSignal): Promise<MemoryStatus> {
  return request<MemoryStatus>('/api/memory/status', { signal });
}

export async function getAlertPreview(
  findingId: string,
  signal?: AbortSignal,
): Promise<AlertPreview> {
  return request<AlertPreview>(`/api/findings/${findingId}/alert/preview`, {
    method: 'POST',
    signal,
  });
}

export async function getEvidenceManifest(
  packId: string,
  findingId?: string,
  signal?: AbortSignal,
): Promise<EvidenceManifest> {
  const qs = findingId ? `?findingId=${encodeURIComponent(findingId)}` : '';
  return request<EvidenceManifest>(`/api/evidence/${packId}${qs}`, { signal });
}
