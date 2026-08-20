import { useEffect, useState } from 'react';
import katex from 'katex';

interface RecognitionModalProps {
  open: boolean;
  latex: string;
  expression: string;
  confidence: number;
  onCancel: () => void;
  onConfirm: (expression: string) => void;
}

export function RecognitionModal({
  open,
  latex,
  expression,
  confidence,
  onCancel,
  onConfirm,
}: RecognitionModalProps) {
  const [value, setValue] = useState(expression);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) {
      setValue(expression);
      setBusy(false);
    }
  }, [open, expression]);

  if (!open) return null;

  const previewHtml = (() => {
    try {
      return katex.renderToString(value || '\\text{(trống)}', { throwOnError: true });
    } catch {
      return katex.renderToString('\\text{Không phân tích được biểu thức này}', { throwOnError: false });
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
    try {
      await onConfirm(value);
    } catch {
      // Parent đã báo lỗi qua toast; không để rò unhandled rejection.
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Xác nhận kết quả nhận dạng">
      <div className="modal">
        <h3>Xác nhận công thức</h3>
        <p className="modal-note">
          Nhận dạng (độ tin cậy {(confidence * 100).toFixed(0)}%):{' '}
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
        <label className="modal-label" htmlFor="recog-input">
          Biểu thức chuẩn hóa (có thể sửa trước khi phân tích):
        </label>
        <input
          id="recog-input"
          className="modal-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') onCancel();
          }}
          placeholder="ví dụ: x**2 - 4*x + 3"
          autoFocus
        />
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onCancel}>
            Hủy
          </button>
          <button className="btn btn-primary" onClick={handleConfirm} disabled={busy}>
            {busy ? 'Đang phân tích...' : 'Xác nhận và tạo activity'}
          </button>
        </div>
      </div>
    </div>
  );
}