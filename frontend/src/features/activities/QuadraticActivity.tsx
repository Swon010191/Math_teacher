import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import {
  formatNum,
  formatQuadratic,
  quadraticFeatures,
  type QuadraticParams,
} from './quadraticMath';

const { red: RED, yellow: YELLOW, purple: PURPLE } = FEATURE_COLORS;

export function QuadraticActivity({ activity }: { activity: ActivityModel }) {
  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 0,
      c: activity.math.c ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) => formatQuadratic(p as unknown as QuadraticParams),
    [],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => {
    const q = p as unknown as QuadraticParams;
    return q.a * x * x + q.b * x + q.c;
  }, []);

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const { h, k, roots } = quadraticFeatures(params as unknown as QuadraticParams);
    const vertex = ctx.pool('vertex', 1, 'point', [0, 0], {
      name: 'Đỉnh',
      size: 3,
      color: RED,
      fixed: true,
      visible: false,
      showInfobox: true,
    })[0];
    if (vertex) {
      ctx.setPos(vertex, [h, k]);
      ctx.setVisible(vertex, revealed.has('vertex'));
    }
    const rootEls = ctx.pool('root', roots.length, 'point', [0, 0], {
      name: 'Nghiệm',
      size: 3,
      color: YELLOW,
      fixed: true,
      visible: false,
    });
    rootEls.forEach((el, i) => {
      ctx.setPos(el, [roots[i], 0]);
      ctx.setVisible(el, revealed.has('roots'));
    });
    const axis = ctx.pool('axis', 1, 'line', [
      [-10, 0],
      [10, 0],
    ], {
      strokeColor: PURPLE,
      strokeWidth: 2,
      dash: 2,
      visible: false,
      label: { text: 'Trục đối xứng', position: 'rt', offset: [8, -8] },
    })[0];
    if (axis) {
      ctx.setPos(axis, [
        [h, -10],
        [h, 10],
      ]);
      ctx.setVisible(axis, revealed.has('axis'));
    }
  }, []);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const { h, k, roots, discriminant } = quadraticFeatures(
      params as unknown as QuadraticParams,
    );
    return (
      <>
        {revealed.has('vertex') && (
          <span className="stat">
            Đỉnh ({formatNum(h)}, {formatNum(k)})
          </span>
        )}
        {revealed.has('roots') && (
          <span className="stat">
            Nghiệm:{' '}
            {roots.length === 0
              ? 'vô nghiệm'
              : roots.map((r) => `x = ${formatNum(r)}`).join(', ')}
          </span>
        )}
        {revealed.has('axis') && <span className="stat">Trục x = {formatNum(h)}</span>}
        <span className="stat muted">Δ = {formatNum(discriminant)}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="quadratic-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[
        { key: 'vertex', label: 'Hiện đỉnh' },
        { key: 'roots', label: 'Hiện nghiệm' },
        { key: 'axis', label: 'Hiện trục' },
      ]}
      sliders={[
        { key: 'a', min: -5, max: 5 },
        { key: 'b', min: -10, max: 10 },
        { key: 'c', min: -10, max: 10 },
      ]}
      steps={activity.steps ?? []}
    />
  );
}