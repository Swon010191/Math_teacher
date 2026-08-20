import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MathInputBar } from '../src/features/math/MathInputBar';

describe('MathInputBar', () => {
  it('khi phân tích thất bại: nút thoát khỏi trạng thái "Đang phân tích" và Hủy vẫn bấm được', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('Không phân tích được biểu thức'));
    const onCancel = vi.fn();
    render(<MathInputBar onSubmit={onSubmit} onCancel={onCancel} />);

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'abc' } });
    fireEvent.click(screen.getByRole('button', { name: 'Phân tích' }));
    expect(screen.getByRole('button', { name: 'Đang phân tích...' })).toBeDisabled();

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith('abc');
      expect(screen.getByRole('button', { name: 'Phân tích' })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('phím Escape hủy nhập liệu', () => {
    const onCancel = vi.fn();
    render(<MathInputBar onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});