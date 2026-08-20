import { useAppStore } from '../../stores/appStore';
import type { Tool } from './types';

const TOOLS: { id: Tool; label: string; icon: string }[] = [
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
      <div className="toolbar-hint">Bút để vẽ · Chọn/Xóa: khoanh vùng để chọn hoặc xóa · AI: khoanh vùng công thức để nhận dạng · Lăn chuột để phóng to</div>
    </div>
  );
}