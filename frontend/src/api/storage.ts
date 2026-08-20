/** Lưu bảng local bằng IndexedDB (idb-keyval). */

import { del, get, set } from 'idb-keyval';

import type { BoardObject } from '../features/board/types';

export interface SavedBoard {
  objects: BoardObject[];
  activities: Record<string, unknown>;
  savedAt: string;
}

const BOARD_KEY = 'saved-board';

export async function saveBoard(board: SavedBoard): Promise<void> {
  await set(BOARD_KEY, board);
}

export async function loadBoard(): Promise<SavedBoard | null> {
  const board = await get<SavedBoard>(BOARD_KEY);
  return board ?? null;
}

export async function clearBoard(): Promise<void> {
  await del(BOARD_KEY);
}