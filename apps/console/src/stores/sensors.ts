import { create } from 'zustand';
import type { Ribbon, Health } from '@/types';

interface SensorsState {
  ribbon: Ribbon | null;
  health: Health | null;
  isLoading: boolean;
  error: string | null;

  setRibbon: (ribbon: Ribbon) => void;
  setHealth: (health: Health) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSensorsStore = create<SensorsState>((set) => ({
  ribbon: null,
  health: null,
  isLoading: false,
  error: null,

  setRibbon: (ribbon) => set({ ribbon, error: null }),
  setHealth: (health) => set({ health, error: null }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
