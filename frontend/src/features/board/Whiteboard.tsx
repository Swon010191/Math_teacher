import { useCallback, useEffect, useRef, useState } from 'react';

import {
  analyzeExpression,
  createActivity,
  recognizeRegion,
  type ActivityModel,
} from '../../api/client';
import { clearBoard, loadBoard, saveBoard } from '../../api/storage';
import { makeId, useAppStore } from '../../stores/appStore';
import { activityKindLabel, activityWidgetFor } from '../activities/activityRegistry';
import { CopilotPanel } from '../copilot/CopilotPanel';
import type { CopilotSuggestion } from '../copilot/copilotTypes';
import { MathInputBar } from '../math/MathInputBar';
import { RecognitionModal } from '../recognition/RecognitionModal';
import { Toast } from '../../components/Toast';
import { BoardStage } from './BoardStage';
import { Toolbar } from './Toolbar';
import type { ActivityObject, BoardObject } from './types';

export function Whiteboard() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const objects = useAppStore((s) => s.objects);
  const activities = useAppStore((s) => s.activities);
  const viewport = useAppStore((s) => s.viewport);
  const confirm = useAppStore((s) => s.confirm);
  const toast = useAppStore((s) => s.toast);
  const addObject = useAppStore((s) => s.addObject);
  const updateObject = useAppStore((s) => s.updateObject);
  const removeObject = useAppStore((s) => s.removeObject);
  const upsertActivity = useAppStore((s) => s.upsertActivity);
  const setConfirm = useAppStore((s) => s.setConfirm);
  const clearConfirm = useAppStore((s) => s.clearConfirm);
  const showToast = useAppStore((s) => s.showToast);
  const clearToast = useAppStore((s) => s.clearToast);
  const restoreBoard = useAppStore((s) => s.loadBoard);
  const setTool = useAppStore((s) => s.setTool);
  const setSelected = useAppStore((s) => s.setSelected);
  const selectedIds = useAppStore((s) => s.selectedIds);

  const [mathInputOpen, setMathInputOpen] = useState(false);
  const [copilotFor, setCopilotFor] = useState<string | null>(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(clearToast, 3200);
    return () => clearTimeout(timer);
  }, [toast, clearToast]);

  const handleRecognizeRegion = useCallback(
    async (imageBase64: string, hint: string, x: number, y: number) => {
      try {
        showToast('Đang nhận dạng...');
        const result = await recognizeRegion(imageBase64, hint);
        setConfirm({
          mode: 'math',
          latex: result.latex,
          expression: result.expression,
          confidence: result.confidence,
          x,
          y,
        });
      } catch (error) {
        showToast(`Lỗi nhận dạng: ${(error as Error).message}`);
      }
    },
    [setConfirm, showToast],
  );

  const handleConfirmExpression = useCallback(
    async (expression: string) => {
      try {
        const activity = await createActivity(expression);
        const activityId = makeId();
        upsertActivity(activityId, activity);
        const obj: ActivityObject = {
          id: makeId(),
          type: 'activity',
          activityId,
          x: confirm.x,
          y: confirm.y,
          width: 420,
          height: 340,
        };
        addObject(obj);
        clearConfirm();
        showToast('Đã tạo hoạt động giảng dạy trên bảng');
      } catch (error) {
        showToast(`Lỗi tạo activity: ${(error as Error).message}`);
      }
    },
    [confirm.x, confirm.y, upsertActivity, addObject, clearConfirm, showToast],
  );

  const handleTypedInput = useCallback(
    async (raw: string) => {
      setMathInputOpen(false);
      try {
        const analysis = await analyzeExpression(raw);
        const activity = await createActivity(raw);
        const activityId = makeId();
        upsertActivity(activityId, activity);
        const center = {
          x: (-viewport.x + 120) / viewport.scale,
          y: (-viewport.y + 80) / viewport.scale,
        };
        addObject({
          id: makeId(),
          type: 'activity',
          activityId,
          x: center.x,
          y: center.y,
          width: 420,
          height: 340,
        } as ActivityObject);
        showToast(`Đã phân tích ${activityKindLabel(analysis.kind)}: ${activity.math.expression}`);
      } catch (error) {
        showToast(`Lỗi: ${(error as Error).message}`);
      }
    },
    [viewport, upsertActivity, addObject, showToast],
  );

  const handleAddText = useCallback(
    (x: number, y: number) => {
      const text = window.prompt('Nhập nội dung text:');
      if (!text || !text.trim()) return;
      addObject({
        id: makeId(),
        type: 'text',
        text: text.trim(),
        x,
        y,
        fontSize: 24,
        color: '#1a1a2e',
      });
    },
    [addObject],
  );

  const handleSave = useCallback(async () => {
    try {
      await saveBoard({ objects, activities, savedAt: new Date().toISOString() });
      showToast('Đã lưu bảng trên máy');
    } catch (error) {
      showToast(`Lỗi lưu: ${(error as Error).message}`);
    }
  }, [objects, activities, showToast]);

  const handleOpen = useCallback(async () => {
    const board = await loadBoard();
    if (!board) {
      showToast('Chưa có bảng đã lưu');
      return;
    }
    restoreBoard(board.objects, board.activities);
    showToast('Đã mở bảng đã lưu');
  }, [restoreBoard, showToast]);

  const handleExport = useCallback(() => {
    const payload = JSON.stringify({ objects, activities, exportedAt: new Date().toISOString() }, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-teaching-board-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Đã xuất file JSON');
  }, [objects, activities, showToast]);

  const handleImport = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text) as { objects?: BoardObject[]; activities?: Record<string, unknown> };
        restoreBoard(parsed.objects ?? [], parsed.activities ?? {});
        showToast('Đã nhập bảng từ JSON');
      } catch (error) {
        showToast(`File không hợp lệ: ${(error as Error).message}`);
      }
    };
    input.click();
  }, [loadBoard, showToast]);

  const handleClear = useCallback(() => {
    if (!window.confirm('Xóa toàn bộ nội dung bảng?')) return;
    restoreBoard([], {});
    void clearBoard();
    showToast('Đã xóa bảng');
  }, [restoreBoard, showToast]);

  const handleApproveCopilot = useCallback(
    (activityId: string, suggestion: CopilotSuggestion) => {
      const current = activities[activityId] as ActivityModel | undefined;
      if (current) upsertActivity(activityId, { ...current, copilot: suggestion });
      setCopilotFor(null);
      showToast('Đã đưa gợi ý giảng dạy lên bảng');
    },
    [activities, upsertActivity, showToast],
  );

  return (
    <div className="whiteboard">
      <Toolbar
        onSave={handleSave}
        onOpen={handleOpen}
        onExport={handleExport}
        onImport={handleImport}
        onClear={handleClear}
        onTypedInput={() => {
          setMathInputOpen(true);
          setTool('select');
        }}
      />
      <div className="board-container" ref={containerRef}>
        <BoardStage
          containerRef={containerRef}
          onRecognizeRegion={handleRecognizeRegion}
          onAddText={handleAddText}
        />
        <div className="activity-layer">
          {objects
            .filter((o): o is ActivityObject => o.type === 'activity')
            .map((obj) => (
              <ActivityFrame
                key={obj.id}
                obj={obj}
                activity={activities[obj.activityId] as ActivityModel | undefined}
                viewport={viewport}
                selected={selectedIds.includes(obj.id)}
                onSelect={() => setSelected([obj.id])}
                onUpdate={updateObject}
                onRemove={removeObject}
                onOpenCopilot={() => setCopilotFor(obj.activityId)}
              />
            ))}
        </div>
        {mathInputOpen && (
          <MathInputBar
            onCancel={() => setMathInputOpen(false)}
            onSubmit={handleTypedInput}
          />
        )}
      </div>
      <RecognitionModal
        open={confirm.mode !== 'none'}
        latex={confirm.latex}
        expression={confirm.expression}
        confidence={confirm.confidence}
        onCancel={clearConfirm}
        onConfirm={handleConfirmExpression}
      />
      <CopilotPanel
        open={copilotFor !== null}
        activity={
          copilotFor
            ? (activities[copilotFor] as ActivityModel | undefined)
            : undefined
        }
        onClose={() => setCopilotFor(null)}
        onApprove={(s) => handleApproveCopilot(copilotFor!, s)}
      />
      <Toast message={toast} />
    </div>
  );
}

function ActivityFrame({
  obj,
  activity,
  viewport,
  selected,
  onSelect,
  onUpdate,
  onRemove,
  onOpenCopilot,
}: {
  obj: ActivityObject;
  activity?: ActivityModel;
  viewport: { x: number; y: number; scale: number };
  selected: boolean;
  onSelect: () => void;
  onUpdate: (id: string, patch: Partial<BoardObject>) => void;
  onRemove: (id: string) => void;
  onOpenCopilot: () => void;
}) {
  const [dragging, setDragging] = useState(false);
  const [resizing, setResizing] = useState(false);
  const [showCopilot, setShowCopilot] = useState(true);

  const style: React.CSSProperties = {
    transform: `translate(${viewport.x + obj.x * viewport.scale}px, ${viewport.y + obj.y * viewport.scale}px)`,
    width: obj.width * viewport.scale,
    height: obj.height * viewport.scale,
  };

  const onHeaderPointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startObjX = obj.x;
    const startObjY = obj.y;
    setDragging(true);
    const move = (ev: PointerEvent) => {
      onUpdate(obj.id, {
        x: startObjX + (ev.clientX - startX) / viewport.scale,
        y: startObjY + (ev.clientY - startY) / viewport.scale,
      });
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      setDragging(false);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  const onResizePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const startX = e.clientX;
    const startY = e.clientY;
    const startW = obj.width * viewport.scale;
    const startH = obj.height * viewport.scale;
    setResizing(true);
    const move = (ev: PointerEvent) => {
      onUpdate(obj.id, {
        width: Math.max(260, (startW + ev.clientX - startX) / viewport.scale),
        height: Math.max(200, (startH + ev.clientY - startY) / viewport.scale),
      });
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      setResizing(false);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };

  const Widget = activity ? activityWidgetFor(activity.type) : null;

  return (
    <div
      className={`activity-frame${dragging ? ' dragging' : ''}${resizing ? ' resizing' : ''}${selected ? ' selected' : ''}`}
      style={style}
    >
      <div
        className="activity-header"
        onPointerDown={(e) => {
          onSelect();
          onHeaderPointerDown(e);
        }}
        title="Kéo để di chuyển"
      >
        <span>Hoạt động: {activity?.source.latex ?? '...'}</span>
        <button
          className="activity-copilot-btn"
          onClick={onOpenCopilot}
          title="Mở trợ lý giảng dạy (Teacher Copilot)"
        >
          💡 Gợi ý
        </button>
        <button className="activity-close" onClick={() => onRemove(obj.id)} title="Xóa hoạt động">
          ×
        </button>
      </div>
      {activity && Widget ? (
        <Widget activity={activity} />
      ) : (
        <div className="activity-loading">Đang tải activity...</div>
      )}
      {activity?.copilot && (
        <div className="activity-copilot" data-testid="activity-copilot">
          <button
            className="activity-copilot-toggle"
            onClick={() => setShowCopilot((s) => !s)}
            title="Hiện/ẩn gợi ý giảng dạy"
          >
            {showCopilot ? '▼' : '▶'} 💡 Gợi ý giảng dạy (đã duyệt)
          </button>
          {showCopilot && (
            <div className="activity-copilot-body">
              <p className="copilot-summary">{activity.copilot.summary}</p>
              <ul>
                {activity.copilot.key_points.slice(0, 4).map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
              <p className="copilot-provider-note">
                Đề xuất bởi Copilot · kiểm tra trước khi sử dụng
              </p>
            </div>
          )}
        </div>
      )}
      <div className="activity-resize" onPointerDown={onResizePointerDown} title="Kéo để thay đổi kích thước" />
    </div>
  );
}