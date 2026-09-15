import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import { expFeatures, formatExp, validateExpParams, type ExpParams } from './expMath';
import { formatNum } from './quadraticMath';

const { yellow: YELLOW, red: RED, purple: PURPLE } = FEATURE_COLORS;

export function ExponentialActivity({ activity }: { activity: ActivityModel }) {
  const sourceVariable = activity.math.source_variable ?? 'x';
  const dependentVariable = activity.math.dependent_variable ?? 'y';
  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 2,
      c: activity.math.c ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) => formatExp(p as unknown as ExpParams, sourceVariable, dependentVariable),
    [dependentVariable, sourceVariable],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => {
    const q = p as unknown as ExpParams;
    const { base } = expFeatures(q);
    return q.a * Math.pow(base, x) + q.c;
  }, []);

  const validate = useCallback(
    (p: Record<string, number>) => validateExpParams(p as unknown as ExpParams),
    [],
  );

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const f = expFeatures(params as unknown as ExpParams);
    const aEls = ctx.pool('asymptote', 1, 'line', [
      [-10, 0],
      [10, 0],
    ], {
      strokeColor: PURPLE,
      strokeWidth: 2,
      dash: 2,
      visible: false,
      label: { text: 'Tiệm cận ngang', position: 'rt', offset: [8, 8] },
    });
    aEls.forEach((el) => {
      ctx.setPos(el, [
        [-10, f.horizontalAsymptote],
        [10, f.horizontalAsymptote],
      ]);
      ctx.setVisible(el, revealed.has('asymptote'));
    });
    const yEls = ctx.pool('yint', 1, 'point', [0, 0], {
      name: 'Giao điểm trục tung',
      size: 3,
      color: RED,
      fixed: true,
      visible: false,
      showInfobox: true,
    });
    yEls.forEach((el) => {
      ctx.setPos(el, [0, f.yIntercept]);
      ctx.setVisible(el, revealed.has('y_intercept'));
    });
    const rEls = ctx.pool('root', f.xIntercept === null ? 0 : 1, 'point', [0, 0], {
      name: 'Giao điểm trục hoành',
      size: 3,
      color: YELLOW,
      fixed: true,
      visible: false,
      showInfobox: true,
    });
    rEls.forEach((el) => {
      ctx.setPos(el, [f.xIntercept as number, 0]);
      ctx.setVisible(el, revealed.has('root'));
    });
  }, []);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const f = expFeatures(params as unknown as ExpParams);
    return (
      <>
        {revealed.has('asymptote') && (
          <span className="stat">
            Tiệm cận ngang: {dependentVariable} = {formatNum(f.horizontalAsymptote)}
          </span>
        )}
        {revealed.has('y_intercept') && (
          <span className="stat">
            Cắt trục {dependentVariable} tại {dependentVariable} = {formatNum(f.yIntercept)}
          </span>
        )}
        {revealed.has('root') &&
          (f.xIntercept === null ? (
            <span className="stat">Không cắt trục hoành</span>
          ) : (
            <span className="stat">
               Giao điểm trục {sourceVariable}: ({formatNum(f.xIntercept)}, 0)
            </span>
          ))}
        <span className="stat muted">
          Cơ số b = {formatNum(f.base)} ({f.direction === 'up' ? 'đồng biến' : 'nghịch biến'})
        </span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="exponential-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      validate={validate}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[
        { key: 'asymptote', label: 'Hiện tiệm cận ngang' },
        { key: 'y_intercept', label: 'Hiện giao điểm trục tung' },
        { key: 'root', label: 'Hiện giao điểm trục hoành' },
      ]}
      sliders={[
        { key: 'a', min: -5, max: 5 },
        { key: 'b', min: 0.1, max: 5, step: 0.1 },
        { key: 'c', min: -10, max: 10 },
      ]}
      steps={activity.steps ?? []}
    />
  );
}
