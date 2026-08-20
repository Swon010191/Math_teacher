import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RecognitionModal } from '../src/features/recognition/RecognitionModal';

describe('RecognitionModal', () => {
  it('khi xác nhận thất bại: nút thoát khỏi trạng thái "Đang phân tích" và Hủy vẫn bấm được', async () => {
    const onConfirm = vi.fn().mockRejectedValue(new Error('Biểu thức không hợp lệ'));
    const onCancel = vi.fn();
    render(
      <RecognitionModal
        open
        latex="y = x^2 - 4x + 3"
        expression="x**2 - 4*x + 3"
        confidence={0.94}
        onCancel={onCancel}
        onConfirm={onConfirm}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận và tạo activity' }));
    expect(screen.getByRole('button', { name: 'Đang phân tích...' })).toBeDisabled();

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(screen.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('phím Escape đóng modal', () => {
    const onCancel = vi.fn();
    render(
      <RecognitionModal
        open
        latex="y = x^2 - 4x + 3"
        expression="x**2 - 4*x + 3"
        confidence={0.94}
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );

    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});