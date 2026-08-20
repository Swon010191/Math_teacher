import { useEffect, useRef, useState } from 'react';

import {
  checkHealth,
  getRecognitionProvider,
  setRecognitionProvider,
  type HealthInfo,
} from '../../api/client';
import { useAppStore } from '../../stores/appStore';
import type { Tool } from './types';

const TOOLS: { id: Tool; label: string; icon: string }[] = [
  { id: 'pan', label: 'Di chuyển', icon: '✋' },
  { id: 'select', label: 'Chọn', icon: '✥' },
  { id: 'pen', label: 'Bút', icon: '✎' },
  { id: 'text', label: 'Text', icon: 'T' },
  { id: 'ai', label: 'AI', icon: '✦' },
  { id: 'erase', label: 'Xóa', icon: '⌫' },
];

const DEFAULT_PROVIDERS = ['mock', 'ollama_vision', 'pix2text'];

const PROVIDER_LABELS: Record<string, string> = {
  mock: 'Mock (giả lập)',
  ollama_vision: 'Ollama Vision (AI thật)',
  pix2text: 'Pix2Text (AI thật)',
};

interface ToolbarProps {
  onSave: () => void;
  onOpen: () => void;
  onExport: () => void;
  onImport: () => void;
  onClear: () => void;
  onTypedInput: () => void;
}

export function Toolbar({ onSave, onOpen, onExport, onImport, onClear, onTypedInput }: ToolbarProps) {
  const tool = useAppStore((s) => s.tool);
  const setTool = useAppStore((s) => s.setTool);
  const showToast = useAppStore((s) => s.showToast);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [providerList, setProviderList] = useState<string[]>(DEFAULT_PROVIDERS);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      const info = await checkHealth();
      if (!alive) return;
      setHealth(info);
      if (info.connected) {
        try {
          const state = await getRecognitionProvider();
          if (alive) {
            setProviderList(state.available.length ? state.available : DEFAULT_PROVIDERS);
            setHealth((prev) =>
              prev ? { ...prev, provider: state.provider } : prev,
            );
          }
        } catch {
          /* giữ danh sách mặc định */
        }
      }
    };
    check();
    const timer = setInterval(check, 10_000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!popoverOpen) return;
    const onDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setPopoverOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPopoverOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [popoverOpen]);

  const connected = health?.connected ?? false;

  const changeProvider = async (name: string) => {
    if (!connected || name === health?.provider || switching) return;
    setSwitching(true);
    try {
      const state = await setRecognitionProvider(name);
      setHealth((prev) => (prev ? { ...prev, provider: state.provider } : prev));
      setPopoverOpen(false);
      showToast(`Đã chuyển sang provider: ${PROVIDER_LABELS[state.provider] ?? state.provider}`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Không đổi được provider');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="toolbar" role="toolbar" aria-label="Thanh công cụ">
      <div className="toolbar-group" role="group" aria-label="Công cụ vẽ">
        {TOOLS.map((t) => (
          <button
            key={t.id}
            className={`tool-btn${tool === t.id ? ' active' : ''}`}
            onClick={() => setTool(t.id)}
            title={t.label}
            aria-pressed={tool === t.id}
          >
            <span className="tool-icon">{t.icon}</span>
            <span className="tool-label">{t.label}</span>
          </button>
        ))}
      </div>
      <div className="toolbar-group" role="group" aria-label="Bảng">
        <button className="tool-btn" onClick={onTypedInput} title="Nhập công thức bằng bàn phím">
          <span className="tool-icon">ƒ(x)</span>
          <span className="tool-label">Công thức</span>
        </button>
        <button className="tool-btn" onClick={onSave} title="Lưu bảng trên máy">
          <span className="tool-icon">💾</span>
          <span className="tool-label">Lưu</span>
        </button>
        <button className="tool-btn" onClick={onOpen} title="Mở bảng đã lưu">
          <span className="tool-icon">📂</span>
          <span className="tool-label">Mở</span>
        </button>
      </div>
      <div className="toolbar-group" role="group" aria-label="Xuất nhập dữ liệu">
        <button className="tool-btn" onClick={onExport} title="Xuất toàn bộ bảng ra file JSON">
          <span className="tool-icon">⇪</span>
          <span className="tool-label">Xuất JSON</span>
        </button>
        <button className="tool-btn" onClick={onImport} title="Nhập bảng từ file JSON">
          <span className="tool-icon">⇩</span>
          <span className="tool-label">Nhập JSON</span>
        </button>
        <button className="tool-btn danger" onClick={onClear} title="Xóa toàn bộ bảng">
          <span className="tool-icon">🗑</span>
          <span className="tool-label">Xóa bảng</span>
        </button>
      </div>
      <div className="toolbar-hint">Di chuyển: kéo để dời bảng · Bút để vẽ · Chọn/Xóa: khoanh vùng để chọn hoặc xóa · AI: khoanh vùng công thức để nhận dạng · Lăn chuột để phóng to</div>
      <div className="backend-status-wrap" ref={containerRef}>
        <button
          className={`backend-status ${health === null ? 'checking' : connected ? 'online' : 'offline'}`}
          onClick={() => setPopoverOpen((o) => !o)}
          aria-expanded={popoverOpen}
          aria-haspopup="dialog"
          aria-label="Trạng thái máy chủ AI và provider nhận dạng"
        >
          <span className="dot" />
          <span>{health === null ? 'Đang kiểm tra...' : connected ? 'AI sẵn sàng' : 'AI chưa kết nối'}</span>
        </button>
        {popoverOpen && (
          <div className="backend-popover" role="dialog" aria-label="Thông tin AI">
            <div className="backend-popover-title">Nhận dạng AI</div>
            <div className="backend-popover-status">
              {connected ? 'Máy chủ AI: sẵn sàng' : 'Máy chủ AI: chưa kết nối'}
            </div>
            <div className="backend-popover-label">Provider đang dùng:</div>
            <div className="backend-popover-options" role="radiogroup" aria-label="Chọn provider nhận dạng">
              {providerList.map((name) => (
                <label key={name} className="backend-popover-option">
                  <input
                    type="radio"
                    name="recognition-provider"
                    value={name}
                    checked={health?.provider === name}
                    disabled={!connected || switching}
                    onChange={() => changeProvider(name)}
                  />
                  <span>{PROVIDER_LABELS[name] ?? name}</span>
                </label>
              ))}
            </div>
            <div className="backend-popover-note">
              Đổi trong lúc chạy; khởi động lại backend sẽ trở về provider trong .env
            </div>
          </div>
        )}
      </div>
    </div>
  );
}