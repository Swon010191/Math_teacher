import { useEffect, useState } from 'react';

import {
  getCopilotProvider,
  setCopilotProvider,
  suggestCopilot,
} from '../../api/client';
import { useAppStore } from '../../stores/appStore';
import type { ActivityModel } from '../activities/activityTypes';
import type { CopilotSuggestion } from './copilotTypes';

interface CopilotPanelProps {
  open: boolean;
  activity: ActivityModel | undefined;
  onClose: () => void;
  onApprove: (suggestion: CopilotSuggestion) => void;
}

const DEFAULT_PROVIDERS = ['rule_based', 'ollama'];

const PROVIDER_LABELS: Record<string, string> = {
  rule_based: 'Gợi ý có sẵn (không cần AI)',
  ollama: 'Ollama (AI local)',
};

export function CopilotPanel({ open, activity, onClose, onApprove }: CopilotPanelProps) {
  const showToast = useAppStore((s) => s.showToast);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<CopilotSuggestion | null>(null);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>(DEFAULT_PROVIDERS);
  const [switching, setSwitching] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    getCopilotProvider()
      .then((state) => {
        if (!alive) return;
        setActiveProvider(state.provider);
        setAvailableProviders(state.available.length ? state.available : DEFAULT_PROVIDERS);
      })
      .catch(() => {
        /* backend chưa kết nối - giữ lựa chọn mặc định */
      });
    return () => {
      alive = false;
    };
  }, [open]);

  useEffect(() => {
    if (!open || !activity) return;
    if (activity.copilot) {
      setSuggestion(activity.copilot);
      setError(null);
      setLoading(false);
      return;
    }
    let alive = true;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSuggestion(null);
    suggestCopilot(activity, 'THCS', controller.signal)
      .then((s) => {
        if (alive) setSuggestion(s);
      })
      .catch((err) => {
        // Request cũ bị hủy (đổi provider/đóng panel): bỏ qua để không đè mới.
        if (!alive) return;
        setError(err instanceof Error ? err.message : 'Lỗi Copilot');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
      controller.abort();
    };
  }, [open, activity, reloadKey]);

  if (!open || !activity) return null;

  const approved = Boolean(activity.copilot);
  const currentProvider = activeProvider ?? suggestion?.provider ?? 'rule_based';

  const changeProvider = async (name: string) => {
    if (name === currentProvider || switching) return;
    setSwitching(true);
    try {
      const state = await setCopilotProvider(name);
      setActiveProvider(state.provider);
      showToast(`Đã chuyển nguồn gợi ý: ${PROVIDER_LABELS[state.provider] ?? state.provider}`);
      if (!activity.copilot) setReloadKey((k) => k + 1);
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Không đổi được nguồn gợi ý');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div
      className="copilot-overlay"
      onClick={onClose}
      onKeyDown={(event) => { if (event.key === 'Escape') onClose(); }}
    >
      <div
        className="copilot-panel"
        role="dialog"
        aria-label="Trợ lý giảng dạy (Teacher Copilot)"
        data-testid="copilot-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="copilot-header">
          <span>💡 Trợ lý giảng dạy — {activity.source.latex}</span>
          <button className="copilot-close" onClick={onClose} title="Đóng">
            ×
          </button>
        </div>
        <div className="copilot-provider-row">
          <label className="copilot-provider-select">
            Nguồn gợi ý:
            <select
              value={availableProviders.includes(currentProvider) ? currentProvider : ''}
              onChange={(e) => changeProvider(e.target.value)}
              disabled={switching}
              aria-label="Nguồn gợi ý"
            >
              {availableProviders.map((name) => (
                <option key={name} value={name}>
                  {PROVIDER_LABELS[name] ?? name}
                </option>
              ))}
            </select>
          </label>
          <span className="copilot-provider-hint">
            Đổi trong lúc chạy; khởi động lại backend trở về .env
          </span>
        </div>

        {loading && <div className="copilot-loading">Đang đề xuất nội dung giảng dạy...</div>}

        {error && (
          <>
            <div className="copilot-error">
              <p>{error}</p>
              <p className="copilot-error-note">
                Gợi ý: khởi động backend hoặc đổi nguồn gợi ý sang "Gợi ý có sẵn (không cần AI)".
              </p>
            </div>
            <div className="copilot-footer">
              <div className="copilot-actions">
                <button className="tool-btn" onClick={onClose}>
                  Đóng
                </button>
              </div>
            </div>
          </>
        )}

        {!loading && !error && suggestion && (
          <>
            <div className="copilot-body">
              <section>
                <h4>Tóm tắt</h4>
                <p>{suggestion.summary}</p>
              </section>
              <section>
                <h4>Kiến thức trọng tâm</h4>
                <ul>
                  {suggestion.key_points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </section>
              <section>
                <h4>Câu hỏi gợi mở</h4>
                <ol>
                  {suggestion.questions.map((q) => (
                    <li key={q}>{q}</li>
                  ))}
                </ol>
              </section>
              <section>
                <h4>Ví dụ minh họa</h4>
                {suggestion.examples.map((ex, i) => (
                  <div className="copilot-example" key={`${ex.prompt}-${i}`}>
                    <p>
                      <strong>Bài {i + 1}:</strong> {ex.prompt}
                    </p>
                    <p className="copilot-example-solution">
                      <em>Giải:</em> {ex.solution}
                    </p>
                  </div>
                ))}
              </section>
              <section>
                <h4>Chuỗi bước giảng dạy</h4>
                <ol>
                  {suggestion.teaching_steps.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ol>
              </section>
            </div>
            <div className="copilot-footer">
              <p className="copilot-note">
                {PROVIDER_LABELS[suggestion.provider] ?? suggestion.provider} · Độ tin cậy{' '}
                {Math.round(suggestion.confidence * 100)}% — hãy kiểm tra trước khi sử dụng.
              </p>
              <div className="copilot-actions">
                {!approved && (
                  <button
                    className="tool-btn primary"
                    onClick={() => onApprove(suggestion)}
                    title="Đưa nội dung đã duyệt lên bảng"
                  >
                    Đưa lên bảng
                  </button>
                )}
                {approved && (
                  <button className="tool-btn" disabled title="Đã đưa lên bảng">
                    Đã đưa lên bảng
                  </button>
                )}
                <button className="tool-btn" onClick={onClose}>
                  Đóng
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}