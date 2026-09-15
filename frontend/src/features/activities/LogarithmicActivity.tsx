import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import { formatNum } from './quadraticMath';
import { formatLog, logFeatures, validateLogParams, type LogParams } from './logMath';

const { yellow: YELLOW, purple: PURPLE } = FEATURE_COLORS;

export function LogarithmicActivity({ activity }: { activity: ActivityModel }) {
  const sourceVariable = activity.math.source_variable ?? 'x';
  const dependentVariable = activity.math.dependent_variable ?? 'y';
  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 10,
      c: activity.math.c ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) => formatLog(p as unknown as LogParams, sourceVariable, dependentVariable),
    [dependentVariable, sourceVariable],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => {
    if (x <= 0) return NaN;
    const q = p as unknown as LogParams;
    const { base } = logFeatures(q);
    return (q.a * Math.log(x)) / Math.log(base) + q.c;
  }, []);

  const validate = useCallback(
    (p: Record<string, number>) => validateLogParams(p as unknown as LogParams),
    [],
  );

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const f = logFeatures(params as unknown as LogParams);
    const aEls = ctx.pool('asymptote', 1, 'line', [
      [0, -10],
      [0, 10],
    ], {
      strokeColor: PURPLE,
      strokeWidth: 2,
      dash: 2,
      visible: false,
      label: { text: 'Tiệm cận đứng', position: 'rt', offset: [8, -8] },
    });
    aEls.forEach((el) => {
      ctx.setPos(el, [
        [0, -10],
        [0, 10],
      ]);
      ctx.setVisible(el, revealed.has('asymptote'));
    });
    const rEls = ctx.pool('root', 1, 'point', [0, 0], {
      name: 'Giao điểm trục hoành',
      size: 3,
      color: YELLOW,
      fixed: true,
      visible: false,
      showInfobox: true,
    });
    rEls.forEach((el) => {
      ctx.setPos(el, [f.xIntercept, 0]);
      ctx.setVisible(el, revealed.has('root'));
    });
  }, []);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const f = logFeatures(params as unknown as LogParams);
    return (
      <>
        {revealed.has('asymptote') && (
          <span className="stat">Tiệm cận đứng: {sourceVariable} = 0</span>
        )}
        {revealed.has('root') && (
          <span className="stat">
            Giao điểm trục {sourceVariable}: ({formatNum(f.xIntercept)}, 0)
          </span>
        )}
        <span className="stat muted">Tập xác định: {f.domain.replace(/\bx\b/g, sourceVariable)}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="logarithmic-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      validate={validate}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[
        { key: 'asymptote', label: 'Hiện tiệm cận đứng' },
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
