import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LinearActivity } from '../src/features/activities/LinearActivity';
import type { ActivityModel } from '../src/features/activities/activityTypes';

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
  type: 'linear_function',
  source: { latex: 'y=2x+1', confidence: 1, confirmed: true },
  math: { expression: '2*x + 1', a: 2, b: 1, root: -0.5, y_intercept: 1 },
  widgets: [
    { type: 'graph' },
    { type: 'parameter_slider', parameters: ['a', 'b'] },
  ],
  steps: [{ visible: ['graph'] }, { visible: ['graph', 'root'] }],
};

describe('LinearActivity', () => {
  it('hiển thị nút hiện giao điểm trục x', () => {
    render(<LinearActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện giao điểm trục x' })).toBeInTheDocument();
  });

  it('có 2 slider a, b', () => {
    render(<LinearActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<LinearActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });

  it('hiển thị đúng biến nguồn và biến phụ thuộc', () => {
    const renamed = { ...activity, math: { ...activity.math, source_variable: 't', dependent_variable: 'z' } };
    const { container } = render(<LinearActivity activity={renamed} />);
    expect(container.querySelector('.activity-formula')?.textContent).toContain('z');
    expect(container.querySelector('.activity-formula')?.textContent).toContain('t');
  });
});
