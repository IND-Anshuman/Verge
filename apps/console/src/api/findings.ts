import type { RiskFinding, FindingState, FindingEvent, FindingFeedback, FeedbackVerdict } from '@/types';
import { request } from './client';

export async function getFindings(shadow = false, signal?: AbortSignal): Promise<RiskFinding[]> {
  return request<RiskFinding[]>(`/api/findings?shadow=${shadow}`, { signal });
}

export async function getFinding(id: string, signal?: AbortSignal): Promise<RiskFinding> {
  return request<RiskFinding>(`/api/findings/${id}`, { signal });
}

export async function transitionFinding(
  id: string,
  toState: FindingState,
  reason?: string,
  reasonCode?: string
): Promise<FindingEvent> {
  return request<FindingEvent>(`/api/findings/${id}/transition`, {
    method: 'POST',
    body: { toState, actor: 'operator', reasonText: reason, reasonCode },
  });
}

export async function submitFeedback(
  id: string,
  verdict: FeedbackVerdict,
  reasonCode?: string,
  reasonText?: string
): Promise<FindingFeedback> {
  return request<FindingFeedback>(`/api/findings/${id}/feedback`, {
    method: 'POST',
    body: { verdict, actor: 'operator', reasonCode, reasonText },
  });
}
