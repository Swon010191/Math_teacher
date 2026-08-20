import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { suggestCopilot } from '../src/api/client';
import { CopilotPanel } from '../src/features/copilot/CopilotPanel';
import type { CopilotSuggestion } from '../src/features/copilot/copilotTypes';
import type { ActivityModel } from '../src/features/activities/activityTypes';

vi.mock('../src/api/client', () => ({
  suggestCopilot: vi.fn(),
}));

const SUGGESTION: CopilotSuggestion = {
  provider: 'rule_based',
  summary: 'Hàm số bậc hai có đồ thị là một parabol.',
  key_points: ['Trục đối xứng x = 2.', 'Đỉnh I(2; -1).'],
  questions: ['Parabol có bề lõm hướng lên hay xuống?'],
  examples: [{ prompt: 'Tìm đỉnh?', solution: 'Đỉnh I(2; -1).' }],
  teaching_steps: ['Quan sát đồ thị.', 'Xác định hệ số.'],
  confidence: 0.85,
};

function makeActivity(copilot?: CopilotSuggestion): ActivityModel {
  return {
    schemaVersion: '1.0',
    type: 'quadratic_function',
    source: { latex: 'y = x^2 - 4x + 3', confidence: 0.94, confirmed: true },
    math: {
      expression: 'x**2 - 4*x + 3',
      a: 1,
      b: -4,
      c: 3,
      vertex: [2, -1],
      roots: [1, 3],
      axis: 'x = 2',
      y_intercept: 3,
      direction: 'up',
    },
    widgets: [{ type: 'graph' }],
    steps: [{ visible: ['graph'] }],
    copilot,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(suggestCopilot).mockResolvedValue(SUGGESTION);
});

describe('CopilotPanel', () => {
  it('mở panel: gọi API, hiện nội dung đề xuất và nút Đưa lên bảng', async () => {
    render(
      <CopilotPanel
        open
        activity={makeActivity()}
        onClose={vi.fn()}
        onApprove={vi.fn()}
      />,
    );

    expect(suggestCopilot).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Hàm số bậc hai có đồ thị là một parabol.')).toBeInTheDocument();
    expect(screen.getByText('Parabol có bề lõm hướng lên hay xuống?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Đưa lên bảng' })).toBeEnabled();
  });

  it('bấm Đưa lên bảng: trả nội dung cho parent', async () => {
    const onApprove = vi.fn();
    render(
      <CopilotPanel open activity={makeActivity()} onClose={vi.fn()} onApprove={onApprove} />,
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Đưa lên bảng' }));
    await waitFor(() => expect(onApprove).toHaveBeenCalledTimes(1));
    expect(onApprove).toHaveBeenCalledWith(SUGGESTION);
  });

  it('activity đã có gợi ý: không gọi lại API, hiện nút Đã đưa lên bảng', async () => {
    render(
      <CopilotPanel
        open
        activity={makeActivity(SUGGESTION)}
        onClose={vi.fn()}
        onApprove={vi.fn()}
      />,
    );

    expect(await screen.findByText('Hàm số bậc hai có đồ thị là một parabol.')).toBeInTheDocument();
    expect(suggestCopilot).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Đã đưa lên bảng' })).toBeDisabled();
  });

  it('API lỗi: hiện thông báo lỗi, vẫn đóng được', async () => {
    vi.mocked(suggestCopilot).mockRejectedValue(new Error('Không kết nối được Ollama'));
    const onClose = vi.fn();
    render(
      <CopilotPanel open activity={makeActivity()} onClose={onClose} onApprove={vi.fn()} />,
    );

    expect(await screen.findByText('Không kết nối được Ollama')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Đóng' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});