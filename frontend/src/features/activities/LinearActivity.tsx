import JXG from 'jsxgraph';
import katex from 'katex';
import { useEffect, useMemo, useRef, useState } from 'react';

import type { ActivityModel } from './activityTypes';
import { formatNum } from './quadraticMath';

const BLUE = '#2563eb';
const YELLOW = '#eab308';

/** Tập con API JSXGraph mà activity dùng (tránh phụ thuộc type phức tạp). */
interface JxgElement {
  setPosition: (type: number, coords: number[]) => void;
  setAttribute: (attrs: Record<string, unknown>) => void;
}

interface LinearParams {
  a: number;
  b: number;
}

export function LinearActivity({ activity }: { activity: ActivityModel }) {
  const boardRef = useRef<HTMLDivElement | null>(null);
  const board = useRef<JXG.Board | null>(null);
  const line = useRef<JXG.GeometryElement | null>(null);
  const rootPoint = useRef<JxgElement | null>(null);

  const initial = useMemo<LinearParams>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 0,
    }),
    [activity],
  );

  const [params, setParams] = useState<LinearParams>(initial);
  const [revealed, setRevealed] = useState<Set<string>>(new Set(['graph']));
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!boardRef.current) return;
    const jxgBoard = JXG.JSXGraph.initBoard(boardRef.current, {
      boundingbox: [-10, 10, 10, -10],
      axis: true,
      grid: true,
      showNavigation: false,
      pan: { needTwoFingers: false },
      resize: { enabled: false, throttle: 100 },
    });
    board.current = jxgBoard;

    line.current = jxgBoard.create(
      'functiongraph',
      [(_x: number) => 0, -10, 10],
      { strokeColor: BLUE, strokeWidth: 3 },
    ) as unknown as JXG.GeometryElement;
    rootPoint.current = jxgBoard.create(
      'point',
      [0, 0],
      {
        name: 'Giao điểm',
        size: 3,
        color: YELLOW,
        fixed: true,
        visible: false,
        showInfobox: true,
      },
    ) as unknown as JxgElement;

    return () => {
      JXG.JSXGraph.freeBoard(jxgBoard);
      board.current = null;
    };
  }, []);

  const root = useMemo(() => (params.a !== 0 ? -params.b / params.a : null), [params]);

  useEffect(() => {
    const b = board.current;
    if (b) {
      if (line.current) b.removeObject(line.current);
      line.current = b.create(
        'functiongraph',
        [(x: number) => params.a * x + params.b, -10, 10],
        { strokeColor: BLUE, strokeWidth: 3 },
      ) as unknown as JXG.GeometryElement;
    }
    if (root !== null) {
      rootPoint.current?.setPosition(JXG.COORDS_BY_USER, [root, 0]);
    }
    rootPoint.current?.setAttribute({ visible: revealed.has('root') && root !== null });
  }, [params, root, revealed]);

  const steps = activity.steps ?? [];
  const currentVisible = steps[Math.min(stepIndex, steps.length - 1)]?.visible ?? [];

  const applyStep = (index: number) => {
    const visible = new Set(steps[Math.min(index, steps.length - 1)]?.visible ?? ['graph']);
    setStepIndex(index);
    setRevealed(visible);
  };

  const toggle = (key: string) => {
    setRevealed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const formulaLatex = useMemo(
    () =>
      `${formatNum(params.a)}x${params.b >= 0 ? '+' : '-'}${formatNum(Math.abs(params.b))}`,
    [params],
  );

  const formulaHtml = useMemo(
    () => katex.renderToString(formulaLatex, { throwOnError: false }),
    [formulaLatex],
  );

  const slider = (key: keyof LinearParams, min: number, max: number) => (
    <label className="slider-row" key={key}>
      <span className="slider-label">{key} = {formatNum(params[key])}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={0.1}
        value={params[key]}
        onChange={(e) => setParams({ ...params, [key]: Number(e.target.value) })}
        aria-label={`Hệ số ${key}`}
      />
    </label>
  );

  return (
    <div className="linear-activity" data-testid="linear-activity">
      <div className="activity-formula" dangerouslySetInnerHTML={{ __html: formulaHtml }} />
      <div className="jsxgraph-container" ref={boardRef} data-testid="jsxgraph-container" />
      <div className="activity-controls">
        <div className="reveal-controls">
          <button
            className={`chip${revealed.has('root') ? ' on' : ''}`}
            onClick={() => toggle('root')}
          >
            Hiện giao điểm trục x
          </button>
        </div>
        <div className="sliders">
          {slider('a', -5, 5)}
          {slider('b', -10, 10)}
        </div>
        {steps.length > 0 && (
          <div className="steps-control">
            <button
              className="btn btn-secondary"
              onClick={() => applyStep(Math.max(0, stepIndex - 1))}
              disabled={stepIndex === 0}
            >
              Bước trước
            </button>
            <span className="steps-status">
              Bước {stepIndex + 1}/{steps.length}
              {currentVisible.length > 0 && (
                <span className="steps-visible">: {currentVisible.join(', ')}</span>
              )}
            </span>
            <button
              className="btn btn-secondary"
              onClick={() => applyStep(Math.min(steps.length - 1, stepIndex + 1))}
              disabled={stepIndex >= steps.length - 1}
            >
              Bước tiếp
            </button>
          </div>
        )}
        <div className="activity-stats">
          {revealed.has('root') && root !== null && (
            <span className="stat">Giao điểm trục x: ({formatNum(root)}, 0)</span>
          )}
          <span className="stat muted">Cắt trục y tại y = {formatNum(params.b)}</span>
        </div>
      </div>
    </div>
  );
}