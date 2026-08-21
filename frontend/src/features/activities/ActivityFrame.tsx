import { useEffect, useState } from 'react';

import type { BoardObject, ActivityObject, Viewport } from '../board/types';
import { KnowledgeActivity } from '../knowledge/KnowledgeActivity';
import type { KnowledgeActivityType } from '../knowledge/knowledgeCache';
import { activityWidgetFor } from './activityRegistry';
import type { ActivityModel } from './activityTypes';
import { SolutionActivity } from './SolutionActivity';

type ActivityTab = 'graph' | 'solution' | 'knowledge' | 'hint';

export function knowledgeTypeFor(activity?: ActivityModel): KnowledgeActivityType | null {
  if (!activity) return null;
  if (activity.type === 'linear_function' || activity.type === 'quadratic_function') {
    return activity.type;
  }
  const classification = activity.solution?.classification.toLowerCase() ?? '';
  const degree = activity.solution?.degree;
  if (classification.includes('linear') || degree === 1) return 'linear_equation';
  if (classification.includes('quadratic') || degree === 2) return 'quadratic_equation';
  return null;
}

export function ActivityFrame({
  obj,
  activity,
  viewport,
  selected,
  onSelect,
  onDeselect = () => undefined,
  onUpdate,
  onRemove,
  onOpenCopilot,
}: {
  obj: ActivityObject;
  activity?: ActivityModel;
  viewport: Viewport;
  selected: boolean;
  onSelect: () => void;
  onDeselect?: () => void;
  onUpdate: (id: string, patch: Partial<BoardObject>) => void;
  onRemove: (id: string) => void;
  onOpenCopilot: () => void;
}) {
  const [dragging, setDragging] = useState(false);
  const [resizing, setResizing] = useState(false);
  const Widget = activity ? activityWidgetFor(activity.type) : null;
  const knowledgeType = knowledgeTypeFor(activity);
  const tabs: ActivityTab[] = [];
  if (activity && Widget && activity.type !== 'equation_solution') tabs.push('graph');
  if (activity?.solution) tabs.push('solution');
  if (knowledgeType) tabs.push('knowledge');
  if (activity?.copilot) tabs.push('hint');
  const defaultTab: ActivityTab = activity?.type === 'equation_solution' ? 'solution' : 'graph';
  const [activeTab, setActiveTab] = useState<ActivityTab>(defaultTab);
  const visibleTab = tabs.includes(activeTab) ? activeTab : tabs[0];

  useEffect(() => {
    setActiveTab(activity?.type === 'equation_solution' ? 'solution' : 'graph');
  }, [activity?.type]);

  const style: React.CSSProperties = {
    transform: `translate(${viewport.x + obj.x * viewport.scale}px, ${viewport.y + obj.y * viewport.scale}px) scale(${viewport.scale})`,
    transformOrigin: 'top left',
    width: obj.width,
    height: obj.height,
    zIndex: selected ? 2 : 1,
  };

  const onHeaderPointerDown = (event: React.PointerEvent) => {
    if ((event.target as HTMLElement).closest('button')) return;
    event.preventDefault();
    onSelect();
    const { clientX: startX, clientY: startY } = event;
    const { x: startObjX, y: startObjY } = obj;
    setDragging(true);
    const move = (next: PointerEvent) => onUpdate(obj.id, {
      x: startObjX + (next.clientX - startX) / viewport.scale,
      y: startObjY + (next.clientY - startY) / viewport.scale,
    });
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      setDragging(false);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  const onResizePointerDown = (event: React.PointerEvent) => {
    event.preventDefault();
    event.stopPropagation();
    onSelect();
    const { clientX: startX, clientY: startY } = event;
    const { width: startWidth, height: startHeight } = obj;
    setResizing(true);
    const move = (next: PointerEvent) => onUpdate(obj.id, {
      width: Math.max(280, startWidth + (next.clientX - startX) / viewport.scale),
      height: Math.max(220, startHeight + (next.clientY - startY) / viewport.scale),
    });
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      setResizing(false);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  const labels: Record<ActivityTab, string> = {
    graph: 'Đồ thị',
    solution: 'Lời giải',
    knowledge: 'Kiến thức',
    hint: 'Gợi ý',
  };

  return (
    <section
      className={`activity-frame${dragging ? ' dragging' : ''}${resizing ? ' resizing' : ''}${selected ? ' selected' : ''}`}
      style={style}
      onPointerDown={onSelect}
    >
      <header className="activity-header" onPointerDown={onHeaderPointerDown} title="Kéo để di chuyển">
        <span className="activity-title">Hoạt động: {activity?.source.latex ?? '...'}</span>
        <div className="activity-header-actions">
          {activity?.type !== 'equation_solution' && (
            <button className="activity-copilot-btn" onPointerDown={(e) => e.stopPropagation()} onClick={onOpenCopilot} title="Mở trợ lý giảng dạy">
              Gợi ý
            </button>
          )}
          <button
            className="activity-collapse"
            onPointerDown={(event) => event.stopPropagation()}
            onClick={onDeselect}
            title="Thu nhỏ hoạt động"
            aria-label="Thu nhỏ hoạt động"
          >
            −
          </button>
          <button className="activity-close" onPointerDown={(e) => e.stopPropagation()} onClick={() => onRemove(obj.id)} title="Xóa hoạt động" aria-label="Xóa hoạt động">×</button>
        </div>
      </header>
      {tabs.length > 0 && (
        <div className="activity-tabs" role="tablist" aria-label="Nội dung hoạt động">
          {tabs.map((tab) => (
            <button
              key={tab}
              role="tab"
              aria-selected={visibleTab === tab}
              tabIndex={visibleTab === tab ? 0 : -1}
              className={visibleTab === tab ? 'active' : ''}
              onClick={() => setActiveTab(tab)}
            >
              {labels[tab]}
            </button>
          ))}
        </div>
      )}
      <div className="activity-content" role="tabpanel" tabIndex={0}>
        {!activity && <div className="activity-loading">Đang tải activity...</div>}
        {activity && visibleTab === 'graph' && Widget && <Widget activity={activity} />}
        {activity && visibleTab === 'solution' && <SolutionActivity activity={activity} embedded />}
        {activity && knowledgeType && visibleTab === 'knowledge' && (
          <KnowledgeActivity expression={activity.math.expression} activityType={knowledgeType} />
        )}
        {activity?.copilot && visibleTab === 'hint' && (
          <div className="activity-copilot" data-testid="activity-copilot">
            <div className="activity-copilot-body">
              <h3>Gợi ý giảng dạy (đã duyệt)</h3>
              <p className="copilot-summary">{activity.copilot.summary}</p>
              <ul>{activity.copilot.key_points.slice(0, 4).map((point) => <li key={point}>{point}</li>)}</ul>
              <p className="copilot-provider-note">Đề xuất bởi Copilot · kiểm tra trước khi sử dụng</p>
            </div>
          </div>
        )}
      </div>
      <div className="activity-resize" onPointerDown={onResizePointerDown} title="Kéo để thay đổi kích thước" />
    </section>
  );
}
