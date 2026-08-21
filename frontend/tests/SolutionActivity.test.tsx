import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SolutionActivity } from '../src/features/activities/SolutionActivity';
import type { ActivityModel } from '../src/features/activities/activityTypes';

const activity: ActivityModel = {
  schemaVersion: '1.0',
  type: 'equation_solution',
  source: { latex: 'x^2=1', confidence: 1, confirmed: true },
  math: { expression: 'x^2=1', source_variable: 'x' },
  widgets: [{ type: 'solution' }],
  steps: [],
  solution: {
    original_equation: 'x^2=1',
    canonical_equation: 'x^2 - 1 = 0',
    variables: ['x'],
    solve_for: 'x',
    degree: 2,
    classification: 'quadratic',
    status: 'solved',
    answers: [
      { exact: '-1', latex: '-1', approximate: -1 },
      { exact: '1', latex: '1', condition: 'x thuộc R' },
    ],
    cases: [],
    steps: [
      {
        expression: '(x-1)(x+1)=0',
        explanation: 'Phân tích thành nhân tử.',
        metadata: { kind: 'quadratic_formula', rule: 'factorization' },
      },
      {
        expression: '(-1)^2=1',
        explanation: 'Thế nghiệm vào phương trình ban đầu.',
        metadata: { kind: 'verification', rule: 'substitution' },
      },
    ],
    verified: true,
  },
};

describe('SolutionActivity', () => {
  it('hiển thị đáp án, bước giải và trạng thái kiểm chứng', () => {
    render(<SolutionActivity activity={activity} />);
    expect(screen.getByTestId('solution-activity')).toHaveAttribute('open');
    expect(screen.getByText('Đã kiểm chứng')).toBeInTheDocument();
    expect(screen.getByText('Phân tích thành nhân tử.')).toBeInTheDocument();
    expect(screen.getByText('Áp dụng công thức nghiệm')).toBeInTheDocument();
    expect(screen.getByText('Kiểm tra nghiệm')).toBeInTheDocument();
    expect(screen.getByText('Đã đối chiếu')).toBeInTheDocument();
    expect(screen.getByText('Điều kiện: x thuộc R')).toBeInTheDocument();
  });

  it('vẫn hiển thị bước giải cũ không có metadata', () => {
    const legacy = structuredClone(activity);
    legacy.solution!.steps = [{ expression: 'x=1', explanation: 'Bước giải cũ.' }];
    render(<SolutionActivity activity={legacy} />);
    expect(screen.getByText('Bước giải cũ.')).toBeInTheDocument();
    expect(screen.getByText('Bước 1')).toBeInTheDocument();
  });

  it('có thể thu gọn khi gắn kèm đồ thị', () => {
    render(<SolutionActivity activity={activity} collapsible />);
    const details = screen.getByTestId('solution-activity');
    expect(details).not.toHaveAttribute('open');
    fireEvent.click(screen.getByText('Đáp án & lời giải'));
    expect(details).toHaveAttribute('open');
  });
});
