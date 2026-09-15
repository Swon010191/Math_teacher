import { fireEvent, render, screen } from '@testing-library/react';
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

  it('chuyển invalid → valid khi mẫu số đi qua trạng thái đồng nhất 0', () => {
    render(<RationalActivity activity={activity} />);
    fireEvent.change(screen.getByRole('slider', { name: 'Hệ số d' }), {
      target: { value: '0' },
    });
    fireEvent.change(screen.getByRole('slider', { name: 'Hệ số c' }), {
      target: { value: '0' },
    });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('c = 0')).toBeInTheDocument();
    expect(screen.getByText('d = 0')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('slider', { name: 'Hệ số d' }), {
      target: { value: '1' },
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('dùng verified hole ban đầu, tính đúng y và bỏ metadata sau khi slider đổi', () => {
    render(
      <RationalActivity
        activity={{
          ...activity,
          math: { ...activity.math, a: 1, b: -1, c: 1, d: -2, holes: [1] },
        }}
      />,
    );
    expect(screen.getByText('Điểm khuyết: (1, 0)')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('slider', { name: 'Hệ số a' }), {
      target: { value: '2' },
    });
    expect(screen.queryByText(/Điểm khuyết:/)).not.toBeInTheDocument();
  });

  it('không suy ngược tọa độ từ chuỗi tiệm cận đã đổi tên', () => {
    render(
      <RationalActivity
        activity={{
          ...activity,
          math: {
            ...activity.math,
            a: 1,
            b: -1.000000000000001,
            c: 1,
            d: -1,
            holes: [],
            asymptotes: ['x = 1', 'y = 1'],
            domain: 'x ≠ 1 (verified)',
          },
        }}
      />,
    );
    expect(screen.queryByText(/Điểm khuyết:/)).not.toBeInTheDocument();
    expect(screen.getByText('Tập xác định: x ≠ 1 (verified)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Hiện tiệm cận đứng' }));
    expect(screen.queryByText(/Tiệm cận đứng: x =/)).not.toBeInTheDocument();
  });

  it('tọa độ y của verified hole lấy từ biểu thức rút gọn, không fallback 0', () => {
    render(
      <RationalActivity
        activity={{
          ...activity,
          math: {
            ...activity.math,
            a: 0,
            b: 0.9,
            c: 0,
            d: 0.3,
            holes: [2],
            asymptotes: [],
            domain: 'x ≠ 2',
          },
        }}
      />,
    );
    expect(screen.getByText('Điểm khuyết: (2, 3)')).toBeInTheDocument();
  });
});
