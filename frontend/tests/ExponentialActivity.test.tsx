import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ActivityModel } from '../src/features/activities/activityTypes';
import { ExponentialActivity } from '../src/features/activities/ExponentialActivity';

vi.mock('jsxgraph', () => ({
  default: {
    JSXGraph: {
      initBoard: () => ({
        create: () => ({
          setFunction: vi.fn(),
          setPosition: vi.fn(),
          setAttribute: vi.fn(),
        }),
        removeObject: vi.fn(),
      }),
      freeBoard: vi.fn(),
    },
    COORDS_BY_USER: 0,
  },
}));

const activity: ActivityModel = {
  schemaVersion: '1.0',
  type: 'exponential_function',
  source: { latex: 'y=2*3^x-1', confidence: 1, confirmed: true },
  math: {
    expression: '2*3**x-1',
    a: 2,
    b: 3,
    c: -1,
    base: 3,
    direction: 'up',
    asymptotes: ['y = -1'],
    y_intercept: 1,
    root: 0.6309,
  },
  widgets: [{ type: 'graph' }, { type: 'parameter_slider', parameters: ['a', 'b', 'c'] }],
  steps: [
    { visible: ['graph'] },
    { visible: ['graph', 'asymptote'] },
    { visible: ['graph', 'asymptote', 'y_intercept'] },
    { visible: ['graph', 'asymptote', 'y_intercept', 'root'] },
  ],
};

describe('ExponentialActivity', () => {
  it('hiển thị nút hiện tiệm cận và giao điểm', () => {
    render(<ExponentialActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện tiệm cận ngang' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện giao điểm trục tung' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện giao điểm trục hoành' })).toBeInTheDocument();
  });

  it('có 3 slider a, b, c', () => {
    render(<ExponentialActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số c' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<ExponentialActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });
});