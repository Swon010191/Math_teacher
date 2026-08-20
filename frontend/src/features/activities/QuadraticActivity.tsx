import JXG from 'jsxgraph';
import katex from 'katex';
import { useEffect, useMemo, useRef, useState } from 'react';

import type { ActivityModel } from './activityTypes';
import { formatNum, formatQuadratic, quadraticFeatures, type QuadraticParams } from './quadraticMath';

const YELLOW = '#eab308';
const BLUE = '#2563eb';
const RED = '#dc2626';
const PURPLE = '#7c3aed';

/** Tập con API JSXGraph mà activity dùng (tránh phụ thuộc type phức tạp). */
interface JxgElement {
  setPosition: (type: number, coords: [number, number] | [[number, number], [number, number]]) => void;
  setAttribute: (attrs: Record<string, unknown>) => void;
}

interface JxgCurve extends JxgElement {
  setFunction: (f: (x: number) => number, min: number, max: number) => void;
}

export function QuadraticActivity({ activity }: { activity: ActivityModel }) {
  const boardRef = useRef<HTMLDivElement | null>(null);
  const board = useRef<JXG.Board | null>(null);
  const curve = useRef<JxgCurve | null>(null);
  const vertexPoint = useRef<JxgElement | null>(null);
  const rootPoints = useRef<JxgElement[]>([]);
  const axisLine = useRef<JxgElement | null>(null);

  const initial = useMemo<QuadraticParams>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 0,
      c: activity.math.c ?? 0,
    }),
    [activity],
  );

  const [params, setParams] = useState<QuadraticParams>(initial);
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

    curve.current = jxgBoard.create(
      'functiongraph',
      [(_x: number) => 0, -10, 10],
      { strokeColor: BLUE, strokeWidth: 3 },
    ) as unknown as JxgCurve;
    vertexPoint.current = jxgBoard.create(
      'point',
      [0, 0],
      {
        name: 'Đỉnh',
        size: 3,
        color: RED,
        fixed: true,
        visible: false,
        showInfobox: true,
      },
    ) as unknown as JxgElement;
    axisLine.current = jxgBoard.create(
      'line',
      [
        [-10, 0],
        [10, 0],
      ],
      {
        strokeColor: PURPLE,
        strokeWidth: 2,
        dash: 2,
        visible: false,
        label: { text: 'Trục đối xứng', position: 'rt', offset: [8, -8] },
      },
    ) as unknown as JxgElement;

    return () => {
      JXG.JSXGraph.freeBoard(jxgBoard);
      board.current = null;
      rootPoints.current = [];
    };
  }, []);

  useEffect(() => {
    const { a, h, k, roots } = quadraticFeatures(params);
    curve.current?.setFunction((x: number) => a * x * x + params.b * x + params.c, -10, 10);

    vertexPoint.current?.setPosition(JXG.COORDS_BY_USER, [h, k]);
    vertexPoint.current?.setAttribute({ visible: revealed.has('vertex') });

    while (rootPoints.current.length < roots.length) {
      const p = board.current?.create('point', [0, 0], {
        name: 'Nghiệm',
        size: 3,
        color: YELLOW,
        fixed: true,
        visible: false,
      });
      if (p) rootPoints.current.push(p as unknown as JxgElement);
    }
    while (rootPoints.current.length > roots.length) {
      const p = rootPoints.current.pop();
      if (p) board.current?.removeObject(p as unknown as JXG.GeometryElement);
    }
    rootPoints.current.forEach((p, i) => {
      p.setPosition(JXG.COORDS_BY_USER, [roots[i], 0]);
      p.setAttribute({ visible: revealed.has('roots') });
    });

    axisLine.current?.setPosition(JXG.COORDS_BY_USER, [
      [h, -10],
      [h, 10],
    ]);
    axisLine.current?.setAttribute({ visible: revealed.has('axis') });
  }, [params, revealed]);

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

  const formulaLatex = useMemo(() => formatQuadratic(params), [params]);

  const formulaHtml = useMemo(
    () => katex.renderToString(formulaLatex, { throwOnError: false }),
    [formulaLatex],
  );

  const { discriminant: d } = quadraticFeatures(params);

  const slider = (key: keyof QuadraticParams, min: number, max: number) => (
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
    <div className="quadratic-activity" data-testid="quadratic-activity">
      <div className="activity-formula" dangerouslySetInnerHTML={{ __html: formulaHtml }} />
      <div className="jsxgraph-container" ref={boardRef} data-testid="jsxgraph-container" />
      <div className="activity-controls">
        <div className="reveal-controls">
          <button
            className={`chip${revealed.has('vertex') ? ' on' : ''}`}
            onClick={() => toggle('vertex')}
          >
            Hiện đỉnh
          </button>
          <button
            className={`chip${revealed.has('roots') ? ' on' : ''}`}
            onClick={() => toggle('roots')}
          >
            Hiện nghiệm
          </button>
          <button
            className={`chip${revealed.has('axis') ? ' on' : ''}`}
            onClick={() => toggle('axis')}
          >
            Hiện trục
          </button>
        </div>
        <div className="sliders">
          {slider('a', -5, 5)}
          {slider('b', -10, 10)}
          {slider('c', -10, 10)}
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
          {revealed.has('vertex') && (
            <span className="stat">Đỉnh ({formatNum(quadraticFeatures(params).h)}, {formatNum(quadraticFeatures(params).k)})</span>
          )}
          {revealed.has('roots') && (
            <span className="stat">
              Nghiệm: {quadraticFeatures(params).roots.length === 0 ? 'vô nghiệm' : quadraticFeatures(params).roots.map((r) => `x = ${formatNum(r)}`).join(', ')}
            </span>
          )}
          {revealed.has('axis') && <span className="stat">Trục x = {formatNum(quadraticFeatures(params).h)}</span>}
          <span className="stat muted">Δ = {formatNum(d)}</span>
        </div>
      </div>
    </div>
  );
}