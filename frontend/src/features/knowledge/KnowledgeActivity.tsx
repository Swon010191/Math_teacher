import { useEffect, useState } from 'react';

import { getRelatedKnowledge } from '../../api/client';
import {
  loadKnowledgeCache,
  saveKnowledgeCache,
  type KnowledgeActivityType,
} from './knowledgeCache';
import { isKnowledgeResponse, type KnowledgeResponse } from './knowledgeTypes';

type LanguageView = 'vi' | 'original';

const translationLabels: Record<string, string> = {
  original: 'Bản gốc',
  machine_translated: 'Dịch máy (machine translation)',
  unavailable: 'Không có bản dịch (translation unavailable)',
  not_requested: 'Không yêu cầu dịch',
};

function displayDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('vi-VN');
}

export function KnowledgeActivity({
  expression,
  activityType,
}: {
  expression: string;
  activityType: KnowledgeActivityType;
}) {
  const [language, setLanguage] = useState<LanguageView>('vi');
  const [response, setResponse] = useState<KnowledgeResponse | null>(null);
  const [fromCache, setFromCache] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setResponse(null);
    setFromCache(false);
    setLoading(true);
    setError('');

    const controller = new AbortController();
    const load = async () => {
      // Hiển thị cache ngay (nếu có), đồng thời refresh từ mạng;
      // bản mạng mới sẽ thay thế và được lưu lại (stale-while-revalidate).
      const currentRequest = getRelatedKnowledge(expression, true, true, controller.signal);
      void currentRequest.catch(() => undefined);
      let cached: KnowledgeResponse | null = null;
      try {
        cached = await loadKnowledgeCache(activityType, expression);
        if (active && cached) {
          setResponse(cached);
          setFromCache(true);
        }
      } catch {
        // IndexedDB may be unavailable in private/restricted browser contexts.
      }

      try {
        const current = await currentRequest;
        if (!isKnowledgeResponse(current)) throw new Error('Phản hồi kiến thức không hợp lệ.');
        if (!active) return;
        setResponse(current);
        setFromCache(false);
        setError('');
        void saveKnowledgeCache(activityType, expression, current).catch(() => undefined);
      } catch (reason) {
        if (!active) return;
        setError(cached
          ? 'Không thể cập nhật dữ liệu. Đang hiển thị bản đã lưu trên thiết bị.'
          : reason instanceof Error ? reason.message : 'Không thể tải kiến thức liên quan.');
      } finally {
        if (active) setLoading(false);
      }
    };

    void load();
    return () => {
      active = false;
      controller.abort();
    };
  }, [activityType, expression]);

  return (
    <section className="knowledge-activity" data-testid="knowledge-activity">
      <div className="knowledge-toolbar">
        <h3>Kiến thức liên quan</h3>
        <div className="knowledge-language" role="group" aria-label="Ngôn ngữ tài liệu">
          <button type="button" aria-pressed={language === 'vi'} onClick={() => setLanguage('vi')}>Tiếng Việt (Vietnamese)</button>
          <button type="button" aria-pressed={language === 'original'} onClick={() => setLanguage('original')}>Original</button>
        </div>
      </div>

      {loading && !response && <p className="knowledge-state">Đang tải kiến thức...</p>}
      {error && <p className="knowledge-error" role="status">{error}</p>}
      {response && (
        <>
          <div className="knowledge-provenance">
            <span className="knowledge-badge source">Chủ đề: {response.topic.replaceAll('_', ' ')}</span>
            <span className="knowledge-badge cache">{fromCache ? 'Bộ nhớ thiết bị' : `Nguồn: ${response.cache.statuses.join(', ')}`}</span>
          </div>
          <div className="knowledge-items">
            {response.items.map((item) => {
              const citation = response.citations.find((entry) => entry.id === item.citation_id);
              const vietnameseAvailable = Boolean(item.vietnamese_text);
              const useOriginal = language === 'original' || !vietnameseAvailable;
              const text = useOriginal ? item.original_text ?? item.vietnamese_text : item.vietnamese_text;
              const unavailable = language === 'vi' && !vietnameseAvailable;
              return (
                <article className="knowledge-item" key={item.id}>
                  <div className="knowledge-item-heading">
                    <h4>{item.title}</h4>
                    <div className="knowledge-item-badges">
                      <span className="knowledge-badge source">{item.source_id}</span>
                      <span className="knowledge-badge cache">{item.cache_status}</span>
                      <span className={`knowledge-badge translation ${item.translation_status}`}>
                        {unavailable ? 'Không có bản dịch (translation unavailable) · hiển thị nguyên bản' : translationLabels[item.translation_status] ?? item.translation_status}
                      </span>
                    </div>
                  </div>
                  <p className="knowledge-text">{text || 'Nội dung không khả dụng.'}</p>
                  {citation && (
                    <footer className="knowledge-citation">
                      <a href={citation.url} target="_blank" rel="noopener noreferrer">Nguồn đầy đủ: {citation.title}</a>
                      <a href={citation.contributors_url} target="_blank" rel="noopener noreferrer">Tác giả / người đóng góp</a>
                      <a href={citation.license_url} target="_blank" rel="noopener noreferrer">{citation.license_name}</a>
                      <span>Bản sửa đổi: {citation.revision}</span>
                      <span>Truy xuất: {displayDate(citation.retrieved_at)}</span>
                    </footer>
                  )}
                </article>
              );
            })}
          </div>
          <p className="knowledge-warning">{response.warning}</p>
        </>
      )}
    </section>
  );
}
