import { useEffect, useState } from 'react';

import { checkHealth } from '../../api/client';
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
  const [backendUp, setBackendUp] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      const up = await checkHealth();
      if (alive) setBackendUp(up);
    };
    check();
    const timer = setInterval(check, 10_000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

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
      <div
        className={`backend-status ${backendUp === null ? 'checking' : backendUp ? 'online' : 'offline'}`}
        title={backendUp ? 'Đã kết nối máy chủ AI' : 'Chưa kết nối máy chủ AI. Chạy: uvicorn app.main:app --port 8000'}
        role="status"
        aria-label="Trạng thái máy chủ AI"
      >
        <span className="dot" />
        <span>{backendUp === null ? 'Đang kiểm tra...' : backendUp ? 'AI sẵn sàng' : 'AI chưa kết nối'}</span>
      </div>
    </div>
  );
}