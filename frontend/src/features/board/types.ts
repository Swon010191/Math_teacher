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

export type Tool = 'select' | 'pen' | 'text' | 'erase' | 'ai';

export interface Viewport {
  x: number;
  y: number;
  scale: number;
}
