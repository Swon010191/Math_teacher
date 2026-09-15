import { useCallback, useEffect, useRef, useState } from 'react';

import {
  createActivity,
  recognizeRegion,
  solveEquation,
  type ActivityModel,
} from '../../api/client';
import { clearBoard, loadBoard, saveBoard } from '../../api/storage';
import { makeId, useAppStore } from '../../stores/appStore';
import { ActivityFrame } from '../activities/ActivityFrame';
import { normalizeMathInput, type MathInputIntent } from '../math/classifyMathInput';
import { CopilotPanel } from '../copilot/CopilotPanel';
import type { CopilotSuggestion } from '../copilot/copilotTypes';
import { MathInputBar } from '../math/MathInputBar';
import { RecognitionModal } from '../recognition/RecognitionModal';
import { Toast } from '../../components/Toast';
import { BoardStage } from './BoardStage';
import { Toolbar } from './Toolbar';
import { MAX_IMPORT_BYTES, sanitizeBoard } from './boardValidation';
import type { ActivityObject } from './types';

export function Whiteboard() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const objects = useAppStore((s) => s.objects);
  const activities = useAppStore((s) => s.activities);
  const viewport = useAppStore((s) => s.viewport);
  const setViewport = useAppStore((s) => s.setViewport);
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
  const [textInputAt, setTextInputAt] = useState<{ x: number; y: number } | null>(null);
  const [textDraft, setTextDraft] = useState('');

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
          source: 'ocr',
        });
      } catch (error) {
        showToast(`Lỗi nhận dạng: ${(error as Error).message}`);
      }
    },
    [setConfirm, showToast],
  );

  const handleConfirmExpression = useCallback(
    async (
      expression: string,
      options: { intent: MathInputIntent; solveFor?: string },
    ) => {
      try {
        let activity: ActivityModel;
        if (options.intent === 'solve') {
          const solution = await solveEquation(expression, options.solveFor);
          activity = {
            schemaVersion: '1.0',
            type: 'equation_solution',
            source: {
              latex: expression === confirm.expression ? confirm.latex : expression,
              confidence: confirm.confidence,
              confirmed: true,
            },
            math: {
              expression: solution.original_equation,
              source_variable: solution.solve_for,
              dependent_variable: null,
            },
            widgets: [{ type: 'solution' }],
            steps: [],
            solution,
          };
        } else {
          const created = await createActivity(normalizeMathInput(expression, 'function'));
          activity = {
            ...created,
            source: {
              ...created.source,
              latex: expression === confirm.expression ? confirm.latex : created.source.latex,
              confidence: confirm.confidence,
              confirmed: true,
            },
          };
        }
        const activityId = makeId();
        upsertActivity(activityId, activity);
        const activityCount = objects.filter((item) => item.type === 'activity').length;
        const offset = (activityCount % 8) * 24;
        const obj: ActivityObject = {
          id: makeId(),
          type: 'activity',
          activityId,
          x: confirm.x + offset,
          y: confirm.y + offset,
          width: 420,
          height: 340,
        };
        addObject(obj);
        setSelected([obj.id]);
        clearConfirm();
        showToast(options.intent === 'solve' ? 'Đã giải phương trình' : 'Đã tạo hoạt động giảng dạy trên bảng');
      } catch (error) {
        showToast(`Lỗi tạo activity: ${(error as Error).message}`);
        throw error;
      }
    },
    [confirm, objects, upsertActivity, addObject, setSelected, clearConfirm, showToast],
  );

  const handleTypedInput = useCallback(
    async (raw: string) => {
      setMathInputOpen(false);
      const center = {
        x: (-viewport.x + 120) / viewport.scale,
        y: (-viewport.y + 80) / viewport.scale,
      };
      setConfirm({
        mode: 'math',
        latex: raw,
        expression: raw,
        confidence: 1,
        x: center.x,
        y: center.y,
        source: 'typed',
      });
    },
    [viewport, setConfirm],
  );

  const handleAddText = useCallback(
    (x: number, y: number) => {
      setTextDraft('');
      setTextInputAt({ x, y });
    },
    [],
  );

  const handleConfirmText = useCallback(() => {
    if (!textInputAt) return;
    const text = textDraft.trim().slice(0, 200);
    setTextInputAt(null);
    if (!text) return;
    addObject({
      id: makeId(),
      type: 'text',
      text,
      x: textInputAt.x,
      y: textInputAt.y,
      fontSize: 24,
      color: '#1a1a2e',
    });
  }, [textInputAt, textDraft, addObject]);

  const handleSave = useCallback(async () => {
    try {
      await saveBoard({ objects, activities, savedAt: new Date().toISOString() });
      showToast('Đã lưu bảng trên máy');
    } catch (error) {
      showToast(`Lỗi lưu: ${(error as Error).message}`);
    }
  }, [objects, activities, showToast]);

  const handleOpen = useCallback(async () => {
    let board: { objects: unknown; activities: unknown } | null = null;
    try {
      board = await loadBoard();
    } catch {
      showToast('Dữ liệu đã lưu bị hỏng, không mở được');
      return;
    }
    if (!board) {
      showToast('Chưa có bảng đã lưu');
      return;
    }
    const clean = sanitizeBoard(board.objects, board.activities);
    if (!clean) {
      showToast('Dữ liệu đã lưu bị hỏng, không mở được');
      return;
    }
    restoreBoard(clean.objects, clean.activities);
    showToast('Đã mở bảng đã lưu');
  }, [restoreBoard, showToast]);

  const handleExport = useCallback(() => {
    const payload = JSON.stringify({ objects, activities, exportedAt: new Date().toISOString() }, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-teaching-board-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Đã xuất file JSON');
  }, [objects, activities, showToast]);

  const handleImport = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = async () => {
      const file = input.files?.[0];
      input.value = '';
      input.remove();
      if (!file) return;
      try {
        if (file.size > MAX_IMPORT_BYTES) {
          showToast('File quá lớn (tối đa 5MB)');
          return;
        }
        const text = await file.text();
        const parsed = JSON.parse(text) as { objects?: unknown; activities?: unknown };
        const clean = sanitizeBoard(parsed.objects, parsed.activities);
        if (!clean) {
          showToast('File không đúng định dạng bảng giảng dạy');
          return;
        }
        restoreBoard(clean.objects, clean.activities);
        showToast('Đã nhập bảng từ JSON');
      } catch (error) {
        showToast(`File không hợp lệ: ${(error as Error).message}`);
      }
    };
    input.click();
  }, [restoreBoard, showToast]);

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

  const zoomAtCenter = useCallback((nextScale: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    const centerX = (rect?.width ?? 800) / 2;
    const centerY = (rect?.height ?? 600) / 2;
    const scale = Math.min(3, Math.max(0.3, nextScale));
    setViewport({
      scale,
      x: centerX - ((centerX - viewport.x) / viewport.scale) * scale,
      y: centerY - ((centerY - viewport.y) / viewport.scale) * scale,
    });
  }, [setViewport, viewport]);

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
                onDeselect={() => setSelected([])}
                onUpdate={updateObject}
                onRemove={removeObject}
                onOpenCopilot={() => setCopilotFor(obj.activityId)}
              />
            ))}
        </div>
        <div className="zoom-controls" role="group" aria-label="Thu phóng bảng">
          <button onClick={() => zoomAtCenter(viewport.scale / 1.2)} aria-label="Thu nhỏ">−</button>
          <output aria-live="polite">{Math.round(viewport.scale * 100)}%</output>
          <button onClick={() => zoomAtCenter(viewport.scale * 1.2)} aria-label="Phóng to">+</button>
          <button onClick={() => zoomAtCenter(1)} aria-label="Đặt lại thu phóng">↺</button>
        </div>
        {mathInputOpen && (
          <MathInputBar
            onCancel={() => setMathInputOpen(false)}
            onSubmit={handleTypedInput}
          />
        )}
        {textInputAt && (
          <div
            className="modal-backdrop"
            role="dialog"
            aria-modal="true"
            aria-label="Thêm văn bản"
            onKeyDown={(event) => {
              if (event.key === 'Escape') setTextInputAt(null);
            }}
          >
            <div className="modal">
              <h3>Thêm văn bản</h3>
              <label className="modal-label" htmlFor="board-text-input">
                Nội dung (tối đa 200 ký tự):
              </label>
              <input
                id="board-text-input"
                className="modal-input"
                value={textDraft}
                maxLength={200}
                onChange={(e) => setTextDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleConfirmText(); }}
                placeholder="Nhập nội dung text..."
                autoFocus
              />
              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={() => setTextInputAt(null)}>
                  Hủy
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleConfirmText}
                  disabled={!textDraft.trim()}
                >
                  Thêm
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      <RecognitionModal
        open={confirm.mode !== 'none'}
        latex={confirm.latex}
        expression={confirm.expression}
        confidence={confirm.confidence}
        source={confirm.source}
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
