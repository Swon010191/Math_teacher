import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ActivityFrame } from '../src/features/activities/ActivityFrame';
import type { ActivityModel } from '../src/features/activities/activityTypes';

vi.mock('../src/features/activities/activityRegistry', () => ({
  activityWidgetFor: () => () => <div data-testid="graph-widget">graph</div>,
}));

vi.mock('../src/features/knowledge/KnowledgeActivity', () => ({
  KnowledgeActivity: () => <div data-testid="knowledge-activity">knowledge</div>,
}));

const activity: ActivityModel = {
  schemaVersion: '1.0',
  type: 'linear_function',
  source: { latex: 'y=2x+1', confidence: 1, confirmed: true },
  math: { expression: '2*x+1' },
  widgets: [{ type: 'graph' }],
  steps: [],
  solution: {
    original_equation: '2*x+1=0', canonical_equation: '2*x+1=0', variables: ['x'],
    solve_for: 'x', degree: 1, classification: 'linear', status: 'solved',
    answers: [{ exact: '-1/2', latex: '-\\frac12' }], cases: [], steps: [], verified: true,
  },
  copilot: {
    summary: 'Gợi ý đã duyệt', key_points: ['Điểm chính'], questions: [], examples: [],
    teaching_steps: [], provider: 'rule_based', confidence: 1,
  },
};

describe('ActivityFrame', () => {
  it('chỉ render nội dung tab đang chọn trong một content wrapper', () => {
    const { container } = render(
      <ActivityFrame
        obj={{ id: 'object', type: 'activity', activityId: 'activity', x: 10, y: 20, width: 420, height: 340 }}
        activity={activity}
        viewport={{ x: 5, y: 6, scale: 1.5 }}
        selected
        onSelect={vi.fn()}
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onOpenCopilot={vi.fn()}
      />,
    );

    expect(screen.getAllByRole('tab')).toHaveLength(4);
    expect(screen.getByRole('tab', { name: 'Đồ thị' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('graph-widget')).toBeInTheDocument();
    expect(container.querySelectorAll('.activity-content')).toHaveLength(1);
    expect(container.querySelector('.activity-frame')).toHaveStyle({ width: '420px', height: '340px' });
    expect(container.querySelector('.activity-frame')?.getAttribute('style')).toContain('scale(1.5)');

    fireEvent.click(screen.getByRole('tab', { name: 'Lời giải' }));
    expect(screen.queryByTestId('graph-widget')).not.toBeInTheDocument();
    expect(screen.getByTestId('solution-activity')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Kiến thức' }));
    expect(screen.queryByTestId('solution-activity')).not.toBeInTheDocument();
    expect(screen.getByTestId('knowledge-activity')).toBeInTheDocument();
  });
});
