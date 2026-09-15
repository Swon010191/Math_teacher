/** Validate + làm sạch dữ liệu bảng khi mở/lưu/nhập JSON (thuần, không phụ thuộc Konva). */

import type { ActivityObject, BoardObject } from './types';

export const MAX_IMPORT_BYTES = 5 * 1024 * 1024;

export function isValidBoardObject(value: unknown): value is BoardObject {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  if (typeof obj.id !== 'string' || !obj.id) return false;
  if (obj.type === 'stroke') {
    return (
      Array.isArray(obj.points) &&
      (obj.points as unknown[]).every((n) => typeof n === 'number' && Number.isFinite(n)) &&
      typeof obj.color === 'string' &&
      typeof obj.strokeWidth === 'number' &&
      typeof obj.x === 'number' &&
      typeof obj.y === 'number'
    );
  }
  if (obj.type === 'text') {
    return (
      typeof obj.text === 'string' &&
      typeof obj.x === 'number' &&
      typeof obj.y === 'number' &&
      typeof obj.fontSize === 'number' &&
      typeof obj.color === 'string'
    );
  }
  if (obj.type === 'activity') {
    return (
      typeof obj.activityId === 'string' &&
      typeof obj.x === 'number' &&
      typeof obj.y === 'number' &&
      typeof obj.width === 'number' &&
      typeof obj.height === 'number'
    );
  }
  return false;
}

export function sanitizeBoard(
  objects: unknown,
  activities: unknown,
): { objects: BoardObject[]; activities: Record<string, unknown> } | null {
  if (!Array.isArray(objects) || typeof activities !== 'object' || activities === null) {
    return null;
  }
  // Lọc bỏ object bẩn, dọn activity mồ côi (activity không còn object nào trỏ tới).
  const cleanObjects = objects.filter(isValidBoardObject);
  const referenced = new Set(
    cleanObjects
      .filter((o): o is ActivityObject => o.type === 'activity')
      .map((o) => o.activityId),
  );
  const cleanActivities: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(activities as Record<string, unknown>)) {
    if (referenced.has(key)) cleanActivities[key] = value;
  }
  return { objects: cleanObjects, activities: cleanActivities };
}
