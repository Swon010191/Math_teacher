import { useState } from 'react';

interface MathInputBarProps {
  onCancel: () => void;
  onSubmit: (expression: string) => void;
}

const LATEX_SNIPPETS: { label: string; insert: string; title: string }[] = [
  { label: '½', insert: '\\frac{}{}', title: 'Phân số \\frac{}{}' },
  { label: '√', insert: '\\sqrt{}', title: 'Căn \\sqrt{}' },
  { label: '∫', insert: 'Integral(exp(-x**2), (x, 0, oo))', title: 'Tích phân (ví dụ Gauss)' },
  { label: '∑', insert: 'Sum(1/x**2, (x, 1, oo))', title: 'Tổng Sum' },
  { label: 'Γ', insert: 'gamma(x)', title: 'Gamma gamma()' },
  { label: 'erf', insert: 'erf(x)', title: 'erf(x)' },
  { label: '∞', insert: 'oo', title: 'Vô cùng oo' },
  { label: 'π', insert: 'pi', title: 'pi' },
];

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

  const insertSnippet = (snippet: string) => {
    setValue((prev) => (prev ? `${prev} ${snippet}` : snippet));
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
      <div className="math-toolbar-snippets" role="group" aria-label="Chèn nhanh LaTeX">
        {LATEX_SNIPPETS.map((s) => (
          <button key={s.label} type="button" className="btn btn-ghost snippet-btn" title={s.title} onClick={() => insertSnippet(s.insert)}>
            {s.label}
          </button>
        ))}
      </div>
      <button className="btn btn-primary" onClick={() => void handleSubmit()} disabled={busy}>
        {busy ? 'Đang phân tích...' : 'Phân tích'}
      </button>
      <button className="btn btn-secondary" onClick={onCancel}>
        Hủy
      </button>
    </div>
  );
}
