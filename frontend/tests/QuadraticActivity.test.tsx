import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { QuadraticActivity } from '../src/features/activities/QuadraticActivity';
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
  type: 'quadratic_function',
  source: { latex: 'y=x^2-4x+3', confidence: 1, confirmed: true },
  math: { expression: 'x**2-4*x+3', a: 1, b: -4, c: 3, vertex: [2, -1], roots: [1, 3], axis: 'x=2' },
  widgets: [
    { type: 'graph' },
    { type: 'parameter_slider', parameters: ['a', 'b', 'c'] },
  ],
  steps: [
    { visible: ['graph'] },
    { visible: ['graph', 'axis'] },
    { visible: ['graph', 'axis', 'vertex', 'roots'] },
  ],
};

describe('QuadraticActivity', () => {
  it('hiển thị nút hiện/ẩn đỉnh, nghiệm, trục', () => {
    render(<QuadraticActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện đỉnh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện nghiệm' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện trục' })).toBeInTheDocument();
  });

  it('có 3 slider a, b, c', () => {
    render(<QuadraticActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số c' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<QuadraticActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });
});