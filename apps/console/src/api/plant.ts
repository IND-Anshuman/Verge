import { request } from './client';

export interface PlantSensor {
  sensorId: string;
  kind: string;
  zoneId: string;
  threshold?: number | null;
}

export interface PlantGeoJson {
  type: 'FeatureCollection';
  properties: { plant: string };
  features: Array<{
    type: 'Feature';
    properties: { zoneId: string; name: string; adjacent?: string[] };
    geometry: { type: 'Polygon'; coordinates: number[][][] };
  }>;
  sensors: PlantSensor[];
}

export async function getPlantGeoJson(signal?: AbortSignal): Promise<PlantGeoJson> {
  return request<PlantGeoJson>('/api/plant/geojson', { signal });
}

export type GraphNodeType = 'equipment' | 'permit' | 'risk';

export interface GraphNode {
  id: string;
  label: string;
  type: GraphNodeType;
  x: number;
  y: number;
  details: string;
  zoneId?: string;
  refId?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  kind?: string;
}

export interface PlantGraph {
  nodes: GraphNode[];
  links: GraphLink[];
  plant: string;
  degraded: boolean;
  source: string;
}

export async function getPlantGraph(signal?: AbortSignal): Promise<PlantGraph> {
  return request<PlantGraph>('/api/plant/graph', { signal });
}
