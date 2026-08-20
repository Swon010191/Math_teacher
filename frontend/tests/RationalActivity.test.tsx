import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ActivityModel } from '../src/features/activities/activityTypes';
import { RationalActivity } from '../src/features/activities/RationalActivity';

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
  type: 'rational_function',
  source: { latex: 'y=(2x+1)/(x-1)', confidence: 1, confirmed: true },
  math: {
    expression: '(2*x+1)/(x-1)',
    a: 2,
    b: 1,
    c: 1,
    d: -1,
    asymptotes: ['x = 1', 'y = 2'],
    domain: 'x ≠ 1',
  },
  widgets: [{ type: 'graph' }, { type: 'parameter_slider', parameters: ['a', 'b', 'c', 'd'] }],
  steps: [
    { visible: ['graph'] },
    { visible: ['graph', 'vertical_asymptotes'] },
    { visible: ['graph', 'vertical_asymptotes', 'horizontal_asymptote'] },
    { visible: ['graph', 'vertical_asymptotes', 'horizontal_asymptote', 'root'] },
  ],
};

describe('RationalActivity', () => {
  it('hiển thị nút hiện tiệm cận và giao điểm', () => {
    render(<RationalActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện tiệm cận đứng' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện tiệm cận ngang' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện giao điểm' })).toBeInTheDocument();
  });

  it('có 4 slider a, b, c, d', () => {
    render(<RationalActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số c' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số d' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<RationalActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });
});