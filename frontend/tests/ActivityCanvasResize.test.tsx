import { render, screen } from '@testing-library/react';
import { StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ActivityCanvas } from '../src/features/activities/ActivityCanvas';

const jsxgraph = vi.hoisted(() => ({
  boards: [] as Array<{
    resizeContainer: ReturnType<typeof vi.fn>;
    fullUpdate: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
    removeObject: ReturnType<typeof vi.fn>;
  }>,
  initBoard: vi.fn(),
  freeBoard: vi.fn(),
}));

const observers: MockResizeObserver[] = [];

class MockResizeObserver implements ResizeObserver {
  readonly observe = vi.fn();
  readonly unobserve = vi.fn();
  readonly disconnect = vi.fn();

  constructor(readonly callback: ResizeObserverCallback) {
    observers.push(this);
  }
}

vi.mock('jsxgraph', () => ({
  default: {
    JSXGraph: {
      initBoard: jsxgraph.initBoard,
      freeBoard: jsxgraph.freeBoard,
    },
    COORDS_BY_USER: 0,
  },
}));

const canvas = (
  <ActivityCanvas
    testId="canvas"
    initial={{ a: 1 }}
    sliders={[]}
    chips={[]}
    steps={[]}
    formula={() => 'x'}
    curve={(x) => x}
  />
);

describe('ActivityCanvas resize', () => {
  beforeEach(() => {
    observers.length = 0;
    jsxgraph.boards.length = 0;
    jsxgraph.initBoard.mockReset();
    jsxgraph.freeBoard.mockReset();
    jsxgraph.initBoard.mockImplementation(() => {
      const board = {
        resizeContainer: vi.fn(),
        fullUpdate: vi.fn(),
        create: vi.fn(() => ({})),
        removeObject: vi.fn(),
      };
      jsxgraph.boards.push(board);
      return board;
    });
    vi.stubGlobal('ResizeObserver', MockResizeObserver);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('resizes JSXGraph when its stable container grows and shrinks', () => {
    render(canvas);
    const container = screen.getByTestId('jsxgraph-container');
    let width = 640;
    let height = 360;
    Object.defineProperties(container, {
      clientWidth: { configurable: true, get: () => width },
      clientHeight: { configurable: true, get: () => height },
    });

    expect(jsxgraph.initBoard).toHaveBeenCalledWith(container, expect.any(Object));
    expect(observers[0].observe).toHaveBeenCalledWith(container);

    observers[0].callback([], observers[0]);
    expect(jsxgraph.boards[0].resizeContainer).toHaveBeenLastCalledWith(640, 360, true);

    width = 320;
    height = 180;
    observers[0].callback([], observers[0]);

    expect(jsxgraph.boards[0].resizeContainer).toHaveBeenLastCalledWith(320, 180, true);
    expect(jsxgraph.boards[0].fullUpdate).toHaveBeenCalledTimes(2);
  });

  it('cleans up each StrictMode board and ignores callbacks after cleanup', () => {
    const { unmount } = render(<StrictMode>{canvas}</StrictMode>);

    expect(jsxgraph.boards).toHaveLength(2);
    expect(observers).toHaveLength(2);
    expect(jsxgraph.initBoard.mock.calls[1][0]).toBe(jsxgraph.initBoard.mock.calls[0][0]);
    expect(jsxgraph.boards[1].removeObject).not.toHaveBeenCalled();
    expect(jsxgraph.freeBoard).toHaveBeenCalledWith(jsxgraph.boards[0]);
    expect(observers[0].unobserve).toHaveBeenCalledWith(
      jsxgraph.initBoard.mock.calls[0][0],
    );
    expect(observers[0].disconnect).toHaveBeenCalledOnce();

    observers[0].callback([], observers[0]);
    expect(jsxgraph.boards[0].resizeContainer).not.toHaveBeenCalled();

    unmount();
    expect(jsxgraph.freeBoard).toHaveBeenCalledTimes(2);
    expect(jsxgraph.freeBoard).toHaveBeenLastCalledWith(jsxgraph.boards[1]);
    expect(observers[1].unobserve).toHaveBeenCalledWith(
      jsxgraph.initBoard.mock.calls[1][0],
    );
    expect(observers[1].disconnect).toHaveBeenCalledOnce();

    observers[1].callback([], observers[1]);
    expect(jsxgraph.boards[1].resizeContainer).not.toHaveBeenCalled();
  });
});
