import { create } from 'zustand';
import type { ConnectionStatus } from '@/types';

interface ConnectionState {
  status: ConnectionStatus;
  lastConnected: string | null;
  reconnectAttempts: number;

  setStatus: (status: ConnectionStatus) => void;
  setLastConnected: (timestamp: string) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  status: 'disconnected',
  lastConnected: null,
  reconnectAttempts: 0,

  setStatus: (status) => set({ status }),
  setLastConnected: (lastConnected) => set({ lastConnected }),
  incrementReconnectAttempts: () =>
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),
  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
}));
