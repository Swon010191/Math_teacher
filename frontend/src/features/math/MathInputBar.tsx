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
      <label className="math-input-prefix" htmlFor="typed-math-input">Công thức</label>
      <input
        id="typed-math-input"
        className="math-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') void handleSubmit();
          if (e.key === 'Escape') onCancel();
        }}
        placeholder="z=2t+1 hoặc 2u+3=9"
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
