import { useState } from 'react';

interface MathInputBarProps {
  onCancel: () => void;
  onSubmit: (expression: string) => void;
}

/** Ô nhập công thức bằng bàn phím - phương án dự phòng khi Recognition không có. */
export function MathInputBar({ onCancel, onSubmit }: MathInputBarProps) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async () => {
    if (!value.trim() || busy) return;
    setBusy(true);
    try {
      await onSubmit(value.trim());
    } catch {
      // Parent đã báo lỗi qua toast; không để rò unhandled rejection.
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="math-input-bar" role="dialog" aria-label="Nhập công thức">
      <span className="math-input-prefix">y =</span>
      <input
        className="math-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') void handleSubmit();
          if (e.key === 'Escape') onCancel();
        }}
        placeholder="x^2 - 4x + 3"
        autoFocus
      />
      <button className="btn btn-primary" onClick={() => void handleSubmit()} disabled={busy}>
        {busy ? 'Đang phân tích...' : 'Phân tích'}
      </button>
      <button className="btn btn-secondary" onClick={onCancel}>
        Hủy
      </button>
    </div>
  );
}