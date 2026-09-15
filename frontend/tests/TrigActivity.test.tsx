import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ActivityModel } from '../src/features/activities/activityTypes';
import { TrigActivity } from '../src/features/activities/TrigActivity';

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
  type: 'trig_function',
  source: { latex: 'y=2sin(3x+1)+4', confidence: 1, confirmed: true },
  math: {
    expression: '2*sin(3*x+1)+4',
    a: 2,
    b: 3,
    c: 1,
    d: 4,
    func: 'sin',
    amplitude: 2,
    period: (2 * Math.PI) / 3,
    phase_shift: -1 / 3,
    midline: 4,
    max_value: 6,
    min_value: 2,
  },
  widgets: [{ type: 'graph' }, { type: 'parameter_slider', parameters: ['a', 'b', 'c', 'd'] }],
  steps: [
    { visible: ['graph'] },
    { visible: ['graph', 'midline'] },
    { visible: ['graph', 'midline', 'max_min'] },
    { visible: ['graph', 'midline', 'max_min', 'roots'] },
  ],
};

describe('TrigActivity', () => {
  it('hiển thị nút hiện đường trung bình, max/min, nghiệm', () => {
    render(<TrigActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Hiện đường trung bình' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện giá trị max/min' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hiện nghiệm' })).toBeInTheDocument();
  });

  it('có 4 slider a, b, c, d', () => {
    render(<TrigActivity activity={activity} />);
    expect(screen.getByRole('slider', { name: 'Hệ số a' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số b' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số c' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Hệ số d' })).toBeInTheDocument();
  });

  it('có điều hướng bước giảng dạy', () => {
    render(<TrigActivity activity={activity} />);
    expect(screen.getByRole('button', { name: 'Bước trước' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bước tiếp' })).toBeInTheDocument();
  });

  it('chuyển invalid → valid khi b đi qua 0', () => {
    render(<TrigActivity activity={activity} />);
    const slider = screen.getByRole('slider', { name: 'Hệ số b' });
    fireEvent.change(slider, { target: { value: '0' } });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('b = 0')).toBeInTheDocument();
    fireEvent.change(slider, { target: { value: '1' } });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
