import { beforeEach, describe, expect, it, vi } from 'vitest';

const konvaMock = vi.hoisted(() => {
  class Node {
    attrs: Record<string, unknown>;
    children: Node[] = [];

    constructor(attrs: Record<string, unknown> = {}) {
      this.attrs = attrs;
    }

    add(...children: Node[]) {
      this.children.push(...children);
      return this;
    }
  }

  class Stage extends Node {
    static instances: Stage[] = [];
    destroyed = false;
    toDataURL = vi.fn(() => 'data:image/png;base64,captured');

    constructor(attrs: Record<string, unknown>) {
      super(attrs);
      Stage.instances.push(this);
    }

    destroy() {
      this.destroyed = true;
    }
  }

  class Layer extends Node {}
  class Rect extends Node {}
  class Line extends Node {}
  class Text extends Node {}

  return { Stage, Layer, Rect, Line, Text };
});

vi.mock('konva', () => ({ default: konvaMock }));
vi.mock('react-konva', () => ({
  Layer: () => null,
  Line: () => null,
  Rect: () => null,
  Stage: () => null,
  Text: () => null,
}));

import { captureBoardRegion } from '../src/features/board/BoardStage';
import type { BoardObject } from '../src/features/board/types';

describe('captureBoardRegion', () => {
  beforeEach(() => {
    konvaMock.Stage.instances.length = 0;
    document.body.replaceChildren();
  });

  it('rasterizes text and strokes in object order over a white background', () => {
    const objects: BoardObject[] = [
      {
        id: 'text-1',
        type: 'text',
        text: 'x + 1',
        x: 20,
        y: 30,
        fontSize: 24,
        color: '#123456',
      },
      {
        id: 'stroke-1',
        type: 'stroke',
        points: [0, 0, 15, 10],
        color: '#654321',
        strokeWidth: 5,
        x: 40,
        y: 50,
      },
    ];

    expect(captureBoardRegion(objects, { x0: 100, y0: 90, x1: 10, y1: 20 })).toBe(
      'data:image/png;base64,captured',
    );

    const stage = konvaMock.Stage.instances[0];
    const layer = stage.children[0];
    expect(stage.attrs).toMatchObject({ width: 90, height: 70 });
    expect(layer.children.map((node) => node.constructor)).toEqual([
      konvaMock.Rect,
      konvaMock.Text,
      konvaMock.Line,
    ]);
    expect(layer.children[0].attrs).toEqual({
      x: 0,
      y: 0,
      width: 90,
      height: 70,
      fill: '#ffffff',
      listening: false,
    });
    expect(layer.children[1].attrs).toEqual({
      x: 10,
      y: 10,
      text: 'x + 1',
      fontSize: 24,
      fill: '#123456',
    });
    expect(layer.children[2].attrs).toEqual({
      points: [0, 0, 15, 10],
      stroke: '#654321',
      strokeWidth: 5,
      lineCap: 'round',
      lineJoin: 'round',
      x: 30,
      y: 30,
    });
    expect(stage.toDataURL).toHaveBeenCalledWith({ pixelRatio: 2 });
    expect(stage.destroyed).toBe(true);
    expect(document.body).toBeEmptyDOMElement();
  });

  it('returns null without creating a canvas when the region has no drawable object', () => {
    const objects: BoardObject[] = [
      {
        id: 'activity-1',
        type: 'activity',
        activityId: 'quadratic',
        x: 0,
        y: 0,
        width: 100,
        height: 100,
      },
    ];

    expect(captureBoardRegion(objects, { x0: 0, y0: 0, x1: 50, y1: 50 })).toBeNull();
    expect(konvaMock.Stage.instances).toHaveLength(0);
    expect(document.body).toBeEmptyDOMElement();
  });
});
