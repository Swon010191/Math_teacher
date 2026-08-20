/** Các loại đối tượng trên bảng (board objects). */

export interface StrokeObject {
  id: string;
  type: 'stroke';
  points: number[];
  color: string;
  strokeWidth: number;
  x: number;
  y: number;
}

export interface TextObject {
  id: string;
  type: 'text';
  text: string;
  x: number;
  y: number;
  fontSize: number;
  color: string;
}

export interface ActivityObject {
  id: string;
  type: 'activity';
  activityId: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export type BoardObject = StrokeObject | TextObject | ActivityObject;

export type Tool = 'pan' | 'select' | 'pen' | 'text' | 'erase' | 'ai';

export interface Viewport {
  x: number;
  y: number;
  scale: number;
}

export interface Region {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** Hình chữ nhật bao (bbox) của đối tượng trong tọa độ bảng. */
export function objectBounds(obj: BoardObject): Region {
  if (obj.type === 'stroke') {
    let x0 = Infinity;
    let y0 = Infinity;
    let x1 = -Infinity;
    let y1 = -Infinity;
    for (let i = 0; i < obj.points.length; i += 2) {
      const px = obj.x + obj.points[i];
      const py = obj.y + obj.points[i + 1];
      x0 = Math.min(x0, px);
      y0 = Math.min(y0, py);
      x1 = Math.max(x1, px);
      y1 = Math.max(y1, py);
    }
    return { x0, y0, x1, y1 };
  }
  if (obj.type === 'text') {
    const width = obj.fontSize * obj.text.length * 0.6;
    return { x0: obj.x, y0: obj.y, x1: obj.x + width, y1: obj.y + obj.fontSize };
  }
  return { x0: obj.x, y0: obj.y, x1: obj.x + obj.width, y1: obj.y + obj.height };
}

export function regionIntersects(region: Region, bounds: Region): boolean {
  return (
    region.x0 <= bounds.x1 &&
    region.x1 >= bounds.x0 &&
    region.y0 <= bounds.y1 &&
    region.y1 >= bounds.y0
  );
}

export function normalizeRegion(region: Region): Region {
  return {
    x0: Math.min(region.x0, region.x1),
    y0: Math.min(region.y0, region.y1),
    x1: Math.max(region.x0, region.x1),
    y1: Math.max(region.y0, region.y1),
  };
}
