import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { BoardObject, Tool, Viewport } from '../features/board/types';

export type ConfirmMode = 'none' | 'math' | 'activity';

export interface ConfirmState {
  mode: ConfirmMode;
  latex: string;
  expression: string;
  confidence: number;
  x: number;
  y: number;
}

interface AppState {
  objects: BoardObject[];
  activities: Record<string, unknown>;
  tool: Tool;
  viewport: Viewport;
  selectedId: string | null;
  confirm: ConfirmState;
  toast: string | null;

  setTool: (tool: Tool) => void;
  setViewport: (viewport: Viewport) => void;
  select: (id: string | null) => void;
  addObject: (obj: BoardObject) => void;
  updateObject: (id: string, patch: Partial<BoardObject>) => void;
  removeObject: (id: string) => void;
  setActivities: (activities: Record<string, unknown>) => void;
  upsertActivity: (id: string, activity: unknown) => void;
  setConfirm: (state: ConfirmState) => void;
  clearConfirm: () => void;
  showToast: (message: string) => void;
  clearToast: () => void;
  loadBoard: (objects: BoardObject[], activities: Record<string, unknown>) => void;
}

function makeId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

const initialConfirm: ConfirmState = {
  mode: 'none',
  latex: '',
  expression: '',
  confidence: 0,
  x: 0,
  y: 0,
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      objects: [],
      activities: {},
      tool: 'pen',
      viewport: { x: 0, y: 0, scale: 1 },
      selectedId: null,
      confirm: initialConfirm,
      toast: null,

      setTool: (tool) => set({ tool, selectedId: null }),
      setViewport: (viewport) => set({ viewport }),
      select: (id) => set({ selectedId: id }),

      addObject: (obj) =>
        set((state) => ({ objects: [...state.objects, obj] })),

      updateObject: (id, patch) =>
        set((state) => ({
          objects: state.objects.map((o) =>
            o.id === id ? ({ ...o, ...patch } as BoardObject) : o,
          ),
        })),

      removeObject: (id) =>
        set((state) => ({
          objects: state.objects.filter((o) => o.id !== id),
          selectedId: state.selectedId === id ? null : state.selectedId,
        })),

      setActivities: (activities) => set({ activities }),
      upsertActivity: (id, activity) =>
        set((state) => ({ activities: { ...state.activities, [id]: activity } })),

      setConfirm: (confirm) => set({ confirm }),
      clearConfirm: () => set({ confirm: initialConfirm }),

      showToast: (message) => set({ toast: message }),
      clearToast: () => set({ toast: null }),

      loadBoard: (objects, activities) =>
        set({ objects, activities, selectedId: null }),
    }),
    {
      name: 'ai-teaching-assistant-board',
      partialize: (state) => ({
        objects: state.objects,
        activities: state.activities,
        viewport: state.viewport,
      }),
    },
  ),
);

export { makeId };
