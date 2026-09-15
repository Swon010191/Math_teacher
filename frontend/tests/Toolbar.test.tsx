import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  checkHealth,
  getRecognitionProvider,
  getRecognitionProviderStatus,
  setRecognitionProvider,
} from '../src/api/client';
import { Toolbar } from '../src/features/board/Toolbar';
import { useAppStore } from '../src/stores/appStore';

vi.mock('../src/api/client', () => ({
  checkHealth: vi.fn(),
  getRecognitionProvider: vi.fn(),
  getRecognitionProviderStatus: vi.fn(),
  setRecognitionProvider: vi.fn(),
}));

const noop = vi.fn();

function renderToolbar() {
  return render(
    <Toolbar
      onSave={noop}
      onOpen={noop}
      onExport={noop}
      onImport={noop}
      onClear={noop}
      onTypedInput={noop}
    />,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(checkHealth).mockResolvedValue({
    connected: true,
    provider: 'mock',
  });
  vi.mocked(getRecognitionProvider).mockResolvedValue({
    provider: 'mock',
    available: ['mock', 'ollama_vision', 'pix2text'],
  });
  vi.mocked(setRecognitionProvider).mockImplementation(async (provider) => ({
    provider,
    available: ['mock', 'ollama_vision', 'pix2text'],
  }));
  vi.mocked(getRecognitionProviderStatus).mockResolvedValue([
    { provider: 'mock', available: true, detail: 'Giả lập, không cần kết nối' },
    {
      provider: 'ollama_vision',
      available: true,
      detail: "Ollama sẵn sàng (model 'llava' đã cài)",
    },
    {
      provider: 'pix2text',
      available: false,
      detail: "Chưa kết nối được Pix2Text (http://localhost:8503). Cài bằng 'pip install pix2text[serve]' rồi chạy 'p2t serve'",
    },
  ]);
});

describe('Toolbar - trạng thái AI', () => {
  it('backend kết nối: hiện nút AI với trạng thái truy cập được', async () => {
    const { container } = renderToolbar();
    const button = await screen.findByRole('button', { name: /Trạng thái máy chủ AI: sẵn sàng/ });
    expect(button).toHaveTextContent('AI');
    expect(button).toHaveClass('online');
    expect(button.closest('.backend-status-wrap')).not.toBe(container.querySelector('.toolbar-actions'));
  });

  it('backend ngắt kết nối: phản ánh trạng thái trong accessible name', async () => {
    vi.mocked(checkHealth).mockResolvedValue({ connected: false, provider: '' });
    renderToolbar();
    expect(await screen.findByRole('button', { name: /Trạng thái máy chủ AI: chưa kết nối/ })).toHaveClass('offline');
  });

  it('ẩn chi tiết mặc định và bấm lần hai để đóng', async () => {
    renderToolbar();
    const button = await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('dialog', { name: 'Thông tin AI' })).not.toBeInTheDocument();

    fireEvent.click(button);
    expect(await screen.findByRole('dialog', { name: 'Thông tin AI' })).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(button);
    expect(screen.queryByRole('dialog', { name: 'Thông tin AI' })).not.toBeInTheDocument();
  });

  it('bấm vào trạng thái: popover hiện provider đang dùng', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByText('Provider đang dùng:')).toBeInTheDocument();
    expect(screen.getByLabelText(/Mock \(giả lập\)/)).toBeChecked();
  });

  it('chọn provider Ollama Vision: gọi API đổi provider và hiện trạng thái mới', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    fireEvent.click(await screen.findByLabelText(/Ollama Vision \(AI thật\)/));
    await waitFor(() => {
      expect(setRecognitionProvider).toHaveBeenCalledWith('ollama_vision');
    });
    expect(useAppStore.getState().toast).toBe(
      'Đã chuyển sang provider: Ollama Vision (AI thật)',
    );
    fireEvent.click(screen.getByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByLabelText(/Ollama Vision \(AI thật\)/)).toBeChecked();
  });

  it('Escape đóng popover', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByText('Provider đang dùng:')).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText('Provider đang dùng:')).not.toBeInTheDocument();
  });

  it('popover hiển thị trạng thái khả dụng của từng provider', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));

    expect(await screen.findByText('Khả dụng — Giả lập, không cần kết nối')).toBeInTheDocument();
    expect(
      screen.getByText(/Khả dụng — Ollama sẵn sàng/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Chưa khả dụng — Chưa kết nối được Pix2Text/),
    ).toBeInTheDocument();
    expect(getRecognitionProviderStatus).toHaveBeenCalledTimes(1);
  });

  it('nút Kiểm tra lại gọi lại API trạng thái provider', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    await screen.findByText(/Chưa khả dụng — Chưa kết nối được Pix2Text/);

    fireEvent.click(screen.getByRole('button', { name: 'Kiểm tra lại' }));
    await waitFor(() => {
      expect(getRecognitionProviderStatus).toHaveBeenCalledTimes(2);
    });
  });

  it('chọn provider chưa khả dụng: toast hiện hướng dẫn cài đặt', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    fireEvent.click(await screen.findByLabelText(/Pix2Text \(AI thật\)/));

    await waitFor(() => {
      expect(setRecognitionProvider).toHaveBeenCalledWith('pix2text');
    });
    expect(useAppStore.getState().toast).toContain('Provider chưa khả dụng');
    expect(useAppStore.getState().toast).toContain('p2t serve');
  });
});
