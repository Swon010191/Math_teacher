import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  checkHealth,
  getRecognitionProvider,
  setRecognitionProvider,
} from '../src/api/client';
import { Toolbar } from '../src/features/board/Toolbar';
import { useAppStore } from '../src/stores/appStore';

vi.mock('../src/api/client', () => ({
  checkHealth: vi.fn(),
  getRecognitionProvider: vi.fn(),
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
  vi.mocked(checkHealth).mockResolvedValue({
    connected: true,
    provider: 'mock',
  });
  vi.mocked(getRecognitionProvider).mockResolvedValue({
    provider: 'mock',
    available: ['mock', 'ollama_vision', 'pix2text'],
  });
  vi.mocked(setRecognitionProvider).mockResolvedValue({
    provider: 'ollama_vision',
    available: ['mock', 'ollama_vision', 'pix2text'],
  });
});

describe('Toolbar - trạng thái AI', () => {
  it('backend kết nối: hiện "AI sẵn sàng"', async () => {
    renderToolbar();
    expect(await screen.findByText('AI sẵn sàng')).toBeInTheDocument();
  });

  it('backend ngắt kết nối: hiện "AI chưa kết nối"', async () => {
    vi.mocked(checkHealth).mockResolvedValue({ connected: false, provider: '' });
    renderToolbar();
    expect(await screen.findByText('AI chưa kết nối')).toBeInTheDocument();
  });

  it('bấm vào trạng thái: popover hiện provider đang dùng', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByText('Provider đang dùng:')).toBeInTheDocument();
    expect(screen.getByLabelText('Mock (giả lập)')).toBeChecked();
  });

  it('chọn provider Ollama Vision: gọi API đổi provider và hiện trạng thái mới', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    fireEvent.click(await screen.findByLabelText('Ollama Vision (AI thật)'));
    await waitFor(() => {
      expect(setRecognitionProvider).toHaveBeenCalledWith('ollama_vision');
    });
    expect(useAppStore.getState().toast).toBe(
      'Đã chuyển sang provider: Ollama Vision (AI thật)',
    );
    fireEvent.click(screen.getByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByLabelText('Ollama Vision (AI thật)')).toBeChecked();
  });

  it('Escape đóng popover', async () => {
    renderToolbar();
    fireEvent.click(await screen.findByRole('button', { name: /Trạng thái máy chủ AI/ }));
    expect(await screen.findByText('Provider đang dùng:')).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText('Provider đang dùng:')).not.toBeInTheDocument();
  });
});