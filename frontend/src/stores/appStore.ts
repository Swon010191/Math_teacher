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
  source?: 'typed' | 'ocr';
}

interface AppState {
  objects: BoardObject[];
  activities: Record<string, unknown>;
  tool: Tool;
  viewport: Viewport;
  selectedIds: string[];
  confirm: ConfirmState;
  toast: string | null;

  setTool: (tool: Tool) => void;
  setViewport: (viewport: Viewport) => void;
  setSelected: (ids: string[]) => void;
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
  try {
    // crypto.randomUUID có sẵn trên trình duyệt hiện đại + môi trường test.
    return crypto.randomUUID();
  } catch {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  }
}

const initialConfirm: ConfirmState = {
  mode: 'none',
  latex: '',
  expression: '',
  confidence: 0,
  x: 0,
  y: 0,
  source: 'ocr',
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      objects: [],
      activities: {},
      tool: 'pen',
      viewport: { x: 0, y: 0, scale: 1 },
      selectedIds: [],
      confirm: initialConfirm,
      toast: null,

      setTool: (tool) => set({ tool, selectedIds: [] }),
      setViewport: (viewport) => set({ viewport }),
      setSelected: (ids) => set({ selectedIds: ids }),

      addObject: (obj) =>
        set((state) => ({ objects: [...state.objects, obj] })),

      updateObject: (id, patch) =>
        set((state) => ({
          objects: state.objects.map((o) =>
            o.id === id ? ({ ...o, ...patch } as BoardObject) : o,
          ),
        })),

      removeObject: (id) =>
        set((state) => {
          const removed = state.objects.find((object) => object.id === id);
          const activities = { ...state.activities };
          if (removed?.type === 'activity') delete activities[removed.activityId];
          return {
            objects: state.objects.filter((object) => object.id !== id),
            activities,
            selectedIds: state.selectedIds.filter((selectedId) => selectedId !== id),
          };
        }),

      setActivities: (activities) => set({ activities }),
      upsertActivity: (id, activity) =>
        set((state) => ({ activities: { ...state.activities, [id]: activity } })),

      setConfirm: (confirm) => set({ confirm }),
      clearConfirm: () => set({ confirm: initialConfirm }),

      showToast: (message) => set({ toast: message }),
      clearToast: () => set({ toast: null }),

      loadBoard: (objects, activities) =>
        set({
          objects,
          activities,
          selectedIds: [],
          // Mở/nhập bảng mới thì bỏ chọn, đóng hộp xác nhận và toast cũ
          // để không còn trạng thái treo từ bảng trước đó.
          confirm: initialConfirm,
          toast: null,
        }),
    }),
    {
      name: 'ai-teaching-assistant-board',
      partialize: (state) => ({
        objects: state.objects,
        activities: state.activities,
        viewport: state.viewport,
        // Giữ lại công cụ đang dùng khi reload; hộp xác nhận, vùng chọn
        // và toast thì không lưu để tránh trạng thái treo.
        tool: state.tool,
      }),
    },
  ),
);

export { makeId };
