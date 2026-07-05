import type {
  FindingState,
  LeadTimeBand,
  DataQuality,
  EstimateQuality,
  FeedbackVerdict,
  SuppressionStatus,
  RiskFinding,
  ContributingSignal,
  Sensor,
  Reading,
  FindingEvent,
  FindingFeedback,
} from '@verge/schema';

// Re-export all schema types
export type {
  FindingState,
  LeadTimeBand,
  DataQuality,
  EstimateQuality,
  FeedbackVerdict,
  SuppressionStatus,
  RiskFinding,
  ContributingSignal,
  Sensor,
  Reading,
  FindingEvent,
  FindingFeedback,
};

// ── Frontend-only types ──────────────────────────────────

export interface FindingFilters {
  states?: FindingState[];
  zones?: string[];
  leadTimeBands?: LeadTimeBand[];
  assignedTo?: string[];
  confidenceDegraded?: boolean;
  dateRange?: { start: string; end: string };
  minConfidence?: number;
  search?: string;
}

export type SortField = 'leadTimeBand' | 'confidence' | 'createdAt' | 'zone' | 'state';
export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

export interface ColumnConfig {
  state: FindingState;
  label: string;
  visible: boolean;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

export interface SensorHealthSummary {
  live: number;
  stale: number;
  stuckAtValue: number;
  outOfRange: number;
  clockSkewed: number;
  missing: number;
  total: number;
  lastUpdated: string;
}

export interface Health {
  status: string;
  llm: { provider: string; degraded: boolean };
  audit: { entries: number; head: string; verified: boolean };
  findings: number;
}

export interface Ribbon {
  text: string;
  counts: Record<string, number>;
}

export interface UserInfo {
  id: string;
  name: string;
  email: string;
  roles: string[];
}

// Band ordering for sorting
export const BAND_SEVERITY: Record<LeadTimeBand, number> = {
  IMMINENT: 0,
  NEAR: 1,
  WATCH: 2,
  UNKNOWN: 3,
};

// Band display colors
export const BAND_COLORS: Record<LeadTimeBand, string> = {
  IMMINENT: 'imminent',
  NEAR: 'near',
  WATCH: 'watch',
  UNKNOWN: 'unknown',
};

// State display labels
export const STATE_LABELS: Record<FindingState, string> = {
  'new': 'New',
  'acknowledged': 'Acknowledged',
  'assigned': 'Assigned',
  'in-progress': 'In Progress',
  'snoozed': 'Snoozed',
  'escalated': 'Escalated',
  'suppressed-as-duplicate': 'Suppressed',
  'resolved': 'Resolved',
  'closed': 'Closed',
  'reopened': 'Reopened',
};

// Default kanban columns
export const DEFAULT_COLUMNS: ColumnConfig[] = [
  { state: 'new', label: 'New', visible: true },
  { state: 'acknowledged', label: 'Acknowledged', visible: true },
  { state: 'assigned', label: 'Assigned', visible: true },
  { state: 'in-progress', label: 'In Progress', visible: true },
  { state: 'escalated', label: 'Escalated', visible: true },
  { state: 'snoozed', label: 'Snoozed', visible: true },
  { state: 'resolved', label: 'Resolved', visible: true },
  { state: 'closed', label: 'Closed', visible: false },
  { state: 'suppressed-as-duplicate', label: 'Suppressed', visible: false },
  { state: 'reopened', label: 'Reopened', visible: true },
];
