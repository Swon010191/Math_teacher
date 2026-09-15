import JXG from 'jsxgraph';
import katex from 'katex';
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import type { ActivityStep } from './activityTypes';
import { formatNum } from './quadraticMath';

export const CURVE_COLOR = '#2563eb';
export const FEATURE_COLORS = {
  red: '#dc2626',
  yellow: '#eab308',
  purple: '#7c3aed',
  green: '#16a34a',
};

export interface SliderDef {
  key: string;
  min: number;
  max: number;
  step?: number;
}

export interface ChipDef {
  key: string;
  label: string;
}

export interface FeatureCtx {
  board: JXG.Board;
  params: Record<string, number>;
  revealed: Set<string>;
  create: (
    key: string,
    type: string,
    args: unknown[],
    attrs: Record<string, unknown>,
  ) => JXG.GeometryElement;
  pool: (
    prefix: string,
    count: number,
    type: string,
    args: unknown[],
    attrs: Record<string, unknown>,
  ) => JXG.GeometryElement[];
  setVisible: (el: JXG.GeometryElement | null | undefined, visible: boolean) => void;
  setPos: (el: JXG.GeometryElement | null | undefined, coords: number[] | number[][]) => void;
}

interface ActivityCanvasProps {
  testId: string;
  initial: Record<string, number>;
  sliders: SliderDef[];
  chips: ChipDef[];
  steps: ActivityStep[];
  formula: (params: Record<string, number>) => string;
  curve: (x: number, params: Record<string, number>) => number;
  validate?: (params: Record<string, number>) => string | null;
  onParamsChanged?: () => void;
  drawFeatures?: (ctx: FeatureCtx) => void;
  stats?: (params: Record<string, number>, revealed: Set<string>) => ReactNode;
}

/** Khung dùng chung cho mọi widget activity: đồ thị, slider, chips hiện/ẩn, bước giảng dạy, stats. */
export function ActivityCanvas({
  testId,
  initial,
  sliders,
  chips,
  steps,
  formula,
  curve,
  validate,
  onParamsChanged,
  drawFeatures,
  stats,
}: ActivityCanvasProps) {
  const boardRef = useRef<HTMLDivElement | null>(null);
  const board = useRef<JXG.Board | null>(null);
  const curveEl = useRef<JXG.GeometryElement | null>(null);
  const elements = useRef<Map<string, JXG.GeometryElement>>(new Map());

  const [params, setParams] = useState<Record<string, number>>(initial);
  const [revealed, setRevealed] = useState<Set<string>>(new Set(['graph']));
  const [stepIndex, setStepIndex] = useState(0);
  const validationError = useMemo(() => validate?.(params) ?? null, [params, validate]);

  useEffect(() => {
    const container = boardRef.current;
    if (!container) return;
    const jxgBoard = JXG.JSXGraph.initBoard(container, {
      boundingbox: [-10, 10, 10, -10],
      axis: true,
      grid: true,
      showNavigation: false,
      pan: { needTwoFingers: false },
      resize: { enabled: false, throttle: 100 },
    });
    board.current = jxgBoard;
    let active = true;
    const resize = () => {
      if (!active) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width > 0 && height > 0) {
        jxgBoard.resizeContainer(width, height, true);
        jxgBoard.fullUpdate();
      }
    };
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(resize);
    observer?.observe(container);
    resize();
    return () => {
      active = false;
      observer?.unobserve(container);
      observer?.disconnect();
      JXG.JSXGraph.freeBoard(jxgBoard);
      if (board.current === jxgBoard) {
        board.current = null;
        curveEl.current = null;
        elements.current.clear();
      }
    };
  }, []);

  const create = (
    key: string,
    type: string,
    args: unknown[],
    attrs: Record<string, unknown>,
  ) => {
    const b = board.current;
    if (!b) throw new Error('Board chưa sẵn sàng.');
    const el = b.create(type, args as never, attrs) as unknown as JXG.GeometryElement;
    elements.current.set(key, el);
    return el;
  };

  const pool = (
    prefix: string,
    count: number,
    type: string,
    args: unknown[],
    attrs: Record<string, unknown>,
  ) => {
    const b = board.current;
    if (!b) return [];
    const out: JXG.GeometryElement[] = [];
    for (let i = 0; i < count; i++) {
      const key = `${prefix}-${i}`;
      let el = elements.current.get(key) ?? null;
      if (!el) {
        el = b.create(type, args as never, attrs) as unknown as JXG.GeometryElement;
        elements.current.set(key, el);
      }
      out.push(el);
    }
    let i = count;
    for (;;) {
      const key = `${prefix}-${i}`;
      const el = elements.current.get(key);
      if (!el) break;
      b.removeObject(el);
      elements.current.delete(key);
      i++;
    }
    return out;
  };

  const setVisible = (el: JXG.GeometryElement | null | undefined, visible: boolean) => {
    el?.setAttribute({ visible });
  };

  const setPos = (el: JXG.GeometryElement | null | undefined, coords: number[] | number[][]) => {
    el?.setPosition(JXG.COORDS_BY_USER, coords as never);
  };

  useEffect(() => {
    const b = board.current;
    if (!b) return;
    if (curveEl.current) b.removeObject(curveEl.current);
    curveEl.current = null;
    if (validationError) {
      elements.current.forEach((el) => setVisible(el, false));
      return;
    }
    curveEl.current = b.create(
      'functiongraph',
      [(x: number) => curve(x, params), -10, 10],
      { strokeColor: CURVE_COLOR, strokeWidth: 3 },
    ) as unknown as JXG.GeometryElement;
    drawFeatures?.({ board: b, params, revealed, create, pool, setVisible, setPos });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, revealed, curve, drawFeatures, validationError]);

  const formulaLatex = useMemo(() => formula(params), [formula, params]);
  const formulaHtml = useMemo(
    () => katex.renderToString(formulaLatex, { throwOnError: false }),
    [formulaLatex],
  );

  const stepsList = steps ?? [];
  const currentVisible = stepsList[Math.min(stepIndex, stepsList.length - 1)]?.visible ?? [];

  const applyStep = (index: number) => {
    const visible = new Set(stepsList[Math.min(index, stepsList.length - 1)]?.visible ?? ['graph']);
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

  return (
    <div className="activity-canvas" data-testid={testId}>
      <div className="activity-formula" dangerouslySetInnerHTML={{ __html: formulaHtml }} />
      {validationError && <div role="alert">{validationError}</div>}
      <div className="jsxgraph-container" ref={boardRef} data-testid="jsxgraph-container" />
      <div className="activity-controls">
        {chips.length > 0 && (
          <div className="reveal-controls">
            {chips.map((chip) => (
              <button
                key={chip.key}
                className={`chip${revealed.has(chip.key) ? ' on' : ''}`}
                onClick={() => toggle(chip.key)}
                aria-pressed={revealed.has(chip.key)}
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}
        {sliders.length > 0 && (
          <div className="sliders">
            {sliders.map((slider) => (
              <label className="slider-row" key={slider.key}>
                <span className="slider-label">
                  {slider.key} = {formatNum(params[slider.key])}
                </span>
                <input
                  type="range"
                  min={slider.min}
                  max={slider.max}
                  step={slider.step ?? 0.1}
                  value={params[slider.key]}
                  onChange={(e) =>
                    {
                      onParamsChanged?.();
                      setParams({ ...params, [slider.key]: Number(e.target.value) });
                    }
                  }
                  aria-label={`Hệ số ${slider.key}`}
                />
              </label>
            ))}
          </div>
        )}
        {stepsList.length > 0 && (
          <div className="steps-control">
            <button
              className="btn btn-secondary"
              onClick={() => applyStep(Math.max(0, stepIndex - 1))}
              disabled={stepIndex === 0}
            >
              Bước trước
            </button>
            <span className="steps-status">
              Bước {stepIndex + 1}/{stepsList.length}
              {currentVisible.length > 0 && (
                <span className="steps-visible">: {currentVisible.join(', ')}</span>
              )}
            </span>
            <button
              className="btn btn-secondary"
              onClick={() => applyStep(Math.min(stepsList.length - 1, stepIndex + 1))}
              disabled={stepIndex >= stepsList.length - 1}
            >
              Bước tiếp
            </button>
          </div>
        )}
        {stats && !validationError && (
          <div className="activity-stats">{stats(params, revealed)}</div>
        )}
      </div>
    </div>
  );
}
