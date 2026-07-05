import { create } from 'zustand';

export type PanelType =
  | 'findings-board'
  | 'digital-twin-map'
  | 'sensor-health-table'
  | 'knowledge-panel'
  | 'permits-panel'
  | 'audit-chain-view'
  | 'alert-fatigue-metrics'
  | 'response-orchestrator'
  | 'replay-controls'
  | 'fleet-command';

interface LayoutState {
  sidebarCollapsed: boolean;
  activePanels: PanelType[];

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  togglePanel: (panel: PanelType) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  sidebarCollapsed: false,
  activePanels: ['findings-board'],

  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  togglePanel: (panel) =>
    set((state) => ({
      activePanels: state.activePanels.includes(panel)
        ? state.activePanels.filter((p) => p !== panel)
        : [...state.activePanels, panel],
    })),
}));
