import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ActivityModel } from '../src/features/activities/activityTypes';
import { LogarithmicActivity } from '../src/features/activities/LogarithmicActivity';

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
  type: 'logarithmic_function',
  source: { latex: 'y=2*log10(x)-1', confidence: 1, confirmed: true },
  math: {
    expression: '2*log(x,10)-1',
    a: 2,
    b: 10,
    c: -1,
    base: 10,
    asymptotes: ['x = 0'],
    domain: 'x > 0',
    root: Math.pow(10, 0.5),
  },
  widgets: [{ type: 'graph' }, { type: 'parameter_slider', parameters: ['a', 'b', 'c'] }],
  steps: [
    { visible: ['graph'] },
    { visible: ['graph', 'asymptote'] },
    { visible: ['graph', 'asymptote', 'root'] },
  ],
};

describe('LogarithmicActivity', () => {
  it('hiển thị nút hiện tiệm cận và giao điểm', () => {
    render(<LogarithmicActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện tiệm cận đứng' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện giao điểm trục hoành' })).toBeInTheDocument();
  });

  it('có 3 slider a, b, c', () => {
    render(<LogarithmicActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số c' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<LogarithmicActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });
});