import { useEffect, useState } from 'react';
import katex from 'katex';

import { classifyMathInput, extractVariables, normalizeMathInput, type MathInputIntent } from '../math/classifyMathInput';

interface RecognitionModalProps {
  open: boolean;
  latex: string;
  expression: string;
  confidence: number;
  source?: 'typed' | 'ocr';
  onCancel: () => void;
  onConfirm: (
    expression: string,
    options: { intent: MathInputIntent; solveFor?: string },
  ) => void | Promise<void>;
}

export function RecognitionModal({
  open,
  latex,
  expression,
  confidence,
  source = 'ocr',
  onCancel,
  onConfirm,
}: RecognitionModalProps) {
  const [value, setValue] = useState(expression);
  const [busy, setBusy] = useState(false);
  const [solveFor, setSolveFor] = useState('');
  const [intent, setIntent] = useState<MathInputIntent>('function');
  const [errorMessage, setErrorMessage] = useState('');
  const classification = classifyMathInput(value);
  const solveVariables = extractVariables(value);

  useEffect(() => {
    if (open) {
      setValue(expression);
      setBusy(false);
      setErrorMessage('');
      const initial = classifyMathInput(expression);
      setIntent(initial.intent);
      setSolveFor(initial.intent === 'solve' && initial.variables.length === 1 ? initial.variables[0] : '');
    }
  }, [open, expression]);

  if (!open) return null;

  const previewHtml = (() => {
    // Chuyển cú pháp Python (x**2) sang LaTeX (x^2) chỉ để xem trước;
    // giá trị gửi backend vẫn giữ nguyên.
    const previewSource = (value || '\\text{(trống)}').replace(/\*\*/g, '^');
    try {
      return katex.renderToString(previewSource, { throwOnError: true });
    } catch {
      return katex.renderToString('\\text{Không xem trước được biểu thức này}', { throwOnError: false });
    }
  })();

  const latexHtml = (() => {
    try {
      return katex.renderToString(latex, { throwOnError: true });
    } catch {
      return null;
    }
  })();

  const handleConfirm = async () => {
    setBusy(true);
    setErrorMessage('');
    try {
      await onConfirm(value.trim(), {
        intent,
        ...(intent === 'solve' && solveFor ? { solveFor } : {}),
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Không thể xử lý công thức này.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Xác nhận kết quả nhận dạng"
      onKeyDown={(event) => { if (event.key === 'Escape' && !busy) onCancel(); }}
    >
      <div className="modal">
        <h3>Xác nhận công thức</h3>
        <p className="modal-note">
          {source === 'typed' ? 'Công thức đã nhập' : `Nhận dạng (độ tin cậy ${(confidence * 100).toFixed(0)}%)`}:{' '}
          {latexHtml ? (
            <span
              className="modal-latex"
              dangerouslySetInnerHTML={{ __html: latexHtml }}
            />
          ) : (
            <span className="modal-latex">{latex}</span>
          )}
        </p>
        <div
          className="math-preview"
          dangerouslySetInnerHTML={{ __html: previewHtml }}
        />
        <p className="modal-classification" data-testid="auto-classification">
          Tự động phân loại:{' '}
          <strong>{classification.intent === 'solve' ? 'Giải phương trình' : 'Phân tích hàm số'}</strong>
        </p>
        <div className="intent-control" role="group" aria-label="Cách xử lý công thức">
          <button type="button" aria-pressed={intent === 'function'} onClick={() => { setIntent('function'); setSolveFor(''); setErrorMessage(''); }}>
            Hàm số
          </button>
          <button type="button" aria-pressed={intent === 'solve'} onClick={() => { setIntent('solve'); setSolveFor(solveVariables.length === 1 ? solveVariables[0] : ''); setErrorMessage(''); }}>
            Giải phương trình
          </button>
        </div>
        {intent === 'function' && (
          <p className="modal-interpretation" data-testid="normalized-interpretation">
            Diễn giải: <code>{normalizeMathInput(value, 'function')}</code>
          </p>
        )}
        <label className="modal-label" htmlFor="recog-input">
          Công thức đầy đủ (có thể sửa trước khi phân tích):
        </label>
        <input
          id="recog-input"
          className="modal-input"
          value={value}
          onChange={(e) => {
            const nextValue = e.target.value;
            const next = classifyMathInput(nextValue);
            setValue(nextValue);
            setErrorMessage('');
            setIntent(next.intent);
            setSolveFor((current) => {
              if (next.intent !== 'solve') return '';
              if (next.variables.length === 1) return next.variables[0];
              return next.variables.includes(current) ? current : '';
            });
          }}
          placeholder="ví dụ: x**2 - 4*x + 3"
          autoFocus
        />
        {intent === 'solve' && solveVariables.length > 1 && (
          <label className="modal-label" htmlFor="solve-for-select">
            Biến cần giải:
            <select
              id="solve-for-select"
              className="modal-input"
              value={solveFor}
              onChange={(event) => setSolveFor(event.target.value)}
            >
              <option value="">Chọn biến</option>
              {solveVariables.map((variable) => (
                <option key={variable} value={variable}>{variable}</option>
              ))}
            </select>
          </label>
        )}
        {errorMessage && <div className="modal-error" role="alert">{errorMessage}</div>}
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onCancel} disabled={busy}>
            Hủy
          </button>
          <button
            className="btn btn-primary"
            onClick={handleConfirm}
            disabled={busy || !value.trim() || (intent === 'solve' && !solveFor)}
          >
            {busy ? 'Đang phân tích...' : 'Xác nhận và tạo activity'}
          </button>
        </div>
      </div>
    </div>
  );
}
