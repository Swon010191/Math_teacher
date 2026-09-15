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
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeDisabled();

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(screen.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();
      expect(screen.getByRole('alert')).toHaveTextContent('Biểu thức không hợp lệ');
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

  it('bắt buộc chọn biến cần giải cho phương trình nhiều biến', async () => {
    const onConfirm = vi.fn();
    render(
      <RecognitionModal
        open
        latex="x+y=2"
        expression="x+y=2"
        confidence={1}
        onCancel={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    expect(screen.getByTestId('auto-classification')).toHaveTextContent('Giải phương trình');
    const confirmButton = screen.getByRole('button', { name: 'Xác nhận và tạo activity' });
    expect(confirmButton).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Biến cần giải:'), { target: { value: 'y' } });
    fireEvent.click(confirmButton);

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith('x+y=2', {
      intent: 'solve',
      solveFor: 'y',
    }));
  });

  it('diễn giải hàm viết ngược và cho phép override intent', async () => {
    const onConfirm = vi.fn();
    render(
      <RecognitionModal open latex="2x+1=y" expression="2x+1=y" confidence={1} source="typed" onCancel={vi.fn()} onConfirm={onConfirm} />,
    );

    expect(screen.getByTestId('normalized-interpretation')).toHaveTextContent('y=2x+1');
    expect(screen.getByRole('button', { name: 'Hàm số' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Giải phương trình' }));
    fireEvent.change(screen.getByLabelText('Biến cần giải:'), { target: { value: 'y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận và tạo activity' }));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith('2x+1=y', { intent: 'solve', solveFor: 'y' }));
  });
});
