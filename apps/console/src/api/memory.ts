import { request } from './client';

export interface SimilarIncident {
  title: string;
  year: number | null;
  excerpt: string;
  source: string;
}

export interface RegulatoryClause {
  id: string;
  title: string;
  excerpt: string;
}

export interface PlantHistoryEntry {
  findingId: string;
  summary: string;
  closedAt: string | null;
}

export interface FindingContext {
  findingId: string;
  similarIncidents: SimilarIncident[];
  regulatoryClauses: RegulatoryClause[];
  plantHistory: PlantHistoryEntry[];
  degraded: boolean;
  reason?: string;
}

export async function getFindingContext(
  findingId: string,
  signal?: AbortSignal,
): Promise<FindingContext> {
  return request<FindingContext>(`/api/findings/${findingId}/context`, { signal });
}

export interface MemoryCitation {
  id: string;
  title: string;
  excerpt: string;
}

export interface MemoryQueryResult {
  answer: string;
  citations: MemoryCitation[];
  degraded: boolean;
  reason?: string;
}

export async function queryMemory(
  query: string,
  findingId?: string,
  signal?: AbortSignal,
): Promise<MemoryQueryResult> {
  return request<MemoryQueryResult>('/api/memory/query', {
    method: 'POST',
    body: { query, findingId },
    signal,
  });
}
