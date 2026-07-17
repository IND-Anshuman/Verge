import { request } from './client';

/* Advisory orchestrator — specialists → merge → twin validator.
   Response carries digests, evidence trail, and validation report (P4/P8). */

export interface InvestigationHypothesis {
  cause: string;
  likelihood: 'high' | 'medium' | 'low' | string;
  supportedBy: string;
}

export interface InvestigationBarrier {
  action: string;
  urgency: 'immediate' | 'this-shift' | 'planned' | string;
  rationale: string;
  supportedBy?: string;
}

export interface InvestigationBrief {
  summary: string;
  hypotheses: InvestigationHypothesis[];
  recommendedBarriers: InvestigationBarrier[];
  regulatoryRefs: { clauseId: string; relevance: string }[];
  openQuestions: string[];
}

export interface InvestigationEvidence {
  tool: string;
  arguments: Record<string, unknown>;
  result: string;
  specialist?: boolean;
}

export interface SpecialistDigest {
  name: string;
  digest: Record<string, unknown>;
  evidence: InvestigationEvidence[];
  refs: string[];
}

export interface InvestigationValidation {
  ok: boolean;
  inventedTags: string[];
  demotedBarriers: Record<string, unknown>[];
  notes: string[];
}

export interface InvestigationResult {
  findingId: string;
  brief: InvestigationBrief;
  evidence: InvestigationEvidence[];
  specialists?: SpecialistDigest[];
  validation?: InvestigationValidation;
  degraded: boolean;
  reason: string | null;
  model: string;
  orchestrator?: string;
}

export async function investigateFinding(findingId: string): Promise<InvestigationResult> {
  return request<InvestigationResult>(
    `/api/findings/${encodeURIComponent(findingId)}/investigate`,
    { method: 'POST' },
  );
}
