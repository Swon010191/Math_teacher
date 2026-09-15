import { useEffect, useRef, useState } from 'react';

import {
  checkHealth,
  getRecognitionProvider,
  getRecognitionProviderStatus,
  setRecognitionProvider,
  type HealthInfo,
  type ProviderStatus,
} from '../../api/client';
import { useAppStore } from '../../stores/appStore';
import type { Tool } from './types';

const TOOLS: { id: Tool; label: string; icon: string }[] = [
  { id: 'pan', label: 'Di chuyển', icon: '✋' },
  { id: 'select', label: 'Chọn', icon: '✥' },
  { id: 'pen', label: 'Bút', icon: '✎' },
  { id: 'text', label: 'Văn bản', icon: 'T' },
  { id: 'ai', label: 'Nhận dạng', icon: '✦' },
  { id: 'erase', label: 'Tẩy vùng', icon: '⌫' },
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
  const [providerStatus, setProviderStatus] = useState<ProviderStatus[]>([]);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const providerChangeVersionRef = useRef(0);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      const providerVersion = providerChangeVersionRef.current;
      const info = await checkHealth();
      if (!alive) return;
      setHealth((previous) => providerVersion === providerChangeVersionRef.current
        ? info
        : { ...info, provider: previous?.provider ?? info.provider });
      if (info.connected) {
        try {
          const state = await getRecognitionProvider();
          if (alive && providerVersion === providerChangeVersionRef.current) {
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

  const refreshStatus = async () => {
    if (!connected) return;
    const providerVersion = providerChangeVersionRef.current;
    setCheckingStatus(true);
    try {
      const status = await getRecognitionProviderStatus();
      if (providerVersion === providerChangeVersionRef.current) {
        setProviderStatus(status);
      }
    } catch {
      if (providerVersion === providerChangeVersionRef.current) {
        setProviderStatus([]);
      }
    } finally {
      if (providerVersion === providerChangeVersionRef.current) {
        setCheckingStatus(false);
      }
    }
  };

  useEffect(() => {
    if (popoverOpen) void refreshStatus();
  }, [popoverOpen]);

  const changeProvider = async (name: string) => {
    if (!connected || name === health?.provider || switching) return;
    providerChangeVersionRef.current += 1;
    setSwitching(true);
    try {
      const state = await setRecognitionProvider(name);
      setHealth((prev) => (prev ? { ...prev, provider: state.provider } : prev));
      setPopoverOpen(false);
      const status = providerStatus.find((s) => s.provider === state.provider);
      if (status && !status.available) {
        showToast(`Provider chưa khả dụng: ${status.detail}`);
      } else {
        showToast(
          `Đã chuyển sang provider: ${PROVIDER_LABELS[state.provider] ?? state.provider}`,
        );
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Không đổi được provider');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="toolbar" role="toolbar" aria-label="Thanh công cụ">
      <div className="toolbar-actions">
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
        <div className="toolbar-hint">Di chuyển: kéo để dời bảng · Bút để vẽ · Chọn/Tẩy vùng: khoanh vùng để chọn hoặc xóa · Nhận dạng: khoanh vùng công thức · Lăn chuột để phóng to</div>
      </div>
      <div className="backend-status-wrap" ref={containerRef}>
        <button
          className={`backend-status ${health === null ? 'checking' : connected ? 'online' : 'offline'}`}
          onClick={() => setPopoverOpen((o) => !o)}
          aria-expanded={popoverOpen}
          aria-haspopup="dialog"
          aria-controls="backend-provider-popover"
          aria-label={`Trạng thái máy chủ AI: ${health === null ? 'đang kiểm tra' : connected ? 'sẵn sàng' : 'chưa kết nối'}`}
        >
          <span className="dot" aria-hidden="true" />
          <span>AI</span>
        </button>
        {popoverOpen && (
          <div id="backend-provider-popover" className="backend-popover" role="dialog" aria-label="Thông tin AI">
            <div className="backend-popover-title">Nhận dạng AI</div>
            <div className="backend-popover-status">
              {connected ? 'Máy chủ AI: sẵn sàng' : 'Máy chủ AI: chưa kết nối'}
            </div>
            <div className="backend-popover-label">Provider đang dùng:</div>
            <div className="backend-popover-options" role="radiogroup" aria-label="Chọn provider nhận dạng">
              {providerList.map((name) => {
                const status = providerStatus.find((s) => s.provider === name);
                return (
                  <label key={name} className="backend-popover-option">
                    <input
                      type="radio"
                      name="recognition-provider"
                      value={name}
                      checked={health?.provider === name}
                      disabled={!connected || switching}
                      onChange={() => changeProvider(name)}
                    />
                    <span className="backend-popover-option-main">
                      <span>{PROVIDER_LABELS[name] ?? name}</span>
                      {status && (
                        <span
                          className={`backend-provider-status ${
                            status.available ? 'ok' : 'bad'
                          }`}
                          title={status.detail}
                        >
                          <span className="dot" />
                          {status.available ? 'Khả dụng' : 'Chưa khả dụng'} — {status.detail}
                        </span>
                      )}
                    </span>
                  </label>
                );
              })}
            </div>
            <div className="backend-popover-actions">
              <button
                className="tool-btn"
                onClick={() => void refreshStatus()}
                disabled={!connected || checkingStatus}
                title="Kiểm tra lại trạng thái của từng provider"
              >
                {checkingStatus ? 'Đang kiểm tra...' : 'Kiểm tra lại'}
              </button>
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
