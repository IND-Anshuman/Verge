import { create } from 'zustand';
import type { UserInfo } from '@/types';

interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;

  setUser: (user: UserInfo) => void;
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: true }),
  clearUser: () => set({ user: null, isAuthenticated: false }),
}));
