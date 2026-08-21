import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import { formatNum } from './quadraticMath';

const { yellow: YELLOW } = FEATURE_COLORS;

export function LinearActivity({ activity }: { activity: ActivityModel }) {
  const sourceVariable = activity.math.source_variable ?? 'x';
  const dependentVariable = activity.math.dependent_variable ?? 'y';
  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) =>
      `${dependentVariable} = ${formatNum(p.a)}${sourceVariable}${p.b >= 0 ? '+' : '-'}${formatNum(Math.abs(p.b))}`,
    [dependentVariable, sourceVariable],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => p.a * x + p.b, []);

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const root = params.a !== 0 ? -params.b / params.a : null;
    const rootEls = ctx.pool('root', root === null ? 0 : 1, 'point', [0, 0], {
      name: 'Giao điểm',
      size: 3,
      color: YELLOW,
      fixed: true,
      visible: false,
      showInfobox: true,
    });
    rootEls.forEach((el) => {
      ctx.setPos(el, [root as number, 0]);
      ctx.setVisible(el, revealed.has('root') && root !== null);
    });
  }, []);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const root = params.a !== 0 ? -params.b / params.a : null;
    return (
      <>
        {revealed.has('root') && root !== null && (
          <span className="stat">
            Giao điểm trục {sourceVariable}: ({formatNum(root)}, 0)
          </span>
        )}
        <span className="stat muted">Cắt trục {dependentVariable} tại {dependentVariable} = {formatNum(params.b)}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="linear-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[{ key: 'root', label: 'Hiện giao điểm trục x' }]}
      sliders={[
        { key: 'a', min: -5, max: 5 },
        { key: 'b', min: -10, max: 10 },
      ]}
      steps={activity.steps ?? []}
    />
  );
}
