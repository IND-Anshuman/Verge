import { request } from './client';

export interface FleetPlant {
  plantId: string;
  name: string;
  location: string;
  activeRisks: number;
  sensorHealth: number | null;
  alertFatigueRate: number | null;
  trir: number | null;
  status: 'imminent' | 'near' | 'ok';
  connected?: boolean;
  measured: {
    activeRisks: boolean;
    sensorHealth: boolean;
    alertFatigueRate: boolean;
    trir: boolean;
  };
}

export interface FleetSummary {
  plants: FleetPlant[];
  connectedSite: string;
}

export async function getFleetSummary(signal?: AbortSignal): Promise<FleetSummary> {
  return request<FleetSummary>('/api/fleet/summary', { signal });
}
