import type { Ribbon, Health } from '@/types';
import { request } from './client';

export async function getSensorRibbon(signal?: AbortSignal): Promise<Ribbon> {
  return request<Ribbon>('/api/sensors/ribbon', { signal });
}

export async function getSystemHealth(signal?: AbortSignal): Promise<Health> {
  return request<Health>('/health', { signal });
}
