import { request } from './client';

export interface TelemetryPoint {
  ts: string;
  value: number;
  zoneId?: string;
  kind?: string;
  unit?: string;
}

export interface TelemetrySeries {
  sensorId: string;
  kind: string;
  unit: string;
  threshold: number | null;
  points: TelemetryPoint[];
}

export interface FindingTelemetry {
  findingId: string;
  zoneId: string;
  series: TelemetrySeries[];
  degraded: boolean;
  reason?: string;
}

export async function getFindingTelemetry(
  findingId: string,
  signal?: AbortSignal,
): Promise<FindingTelemetry> {
  return request<FindingTelemetry>(`/api/findings/${findingId}/telemetry`, { signal });
}
