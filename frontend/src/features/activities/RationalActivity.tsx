import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import { formatNum } from './quadraticMath';
import {
  formatRational,
  rationalFeatures,
  type RationalParams,
} from './rationalMath';

const { yellow: YELLOW, purple: PURPLE } = FEATURE_COLORS;

export function RationalActivity({ activity }: { activity: ActivityModel }) {
  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 1,
      c: activity.math.c ?? 1,
      d: activity.math.d ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) => formatRational(p as unknown as RationalParams),
    [],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => {
    const q = p as unknown as RationalParams;
    const den = q.c * x + q.d;
    if (Math.abs(den) < 1e-9) return NaN;
    return (q.a * x + q.b) / den;
  }, []);

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const f = rationalFeatures(params as unknown as RationalParams);
    const vEls = ctx.pool('vasym', f.poles.length, 'line', [
      [-10, 0],
      [10, 0],
    ], {
      strokeColor: PURPLE,
      strokeWidth: 2,
      dash: 2,
      visible: false,
      label: { text: 'Tiệm cận đứng', position: 'rt', offset: [8, -8] },
    });
    vEls.forEach((el, i) => {
      ctx.setPos(el, [
        [f.poles[i], -10],
        [f.poles[i], 10],
      ]);
      ctx.setVisible(el, revealed.has('vertical_asymptotes'));
    });
    const hEls = ctx.pool('hasym', f.horizontal === null ? 0 : 1, 'line', [
      [-10, 0],
      [10, 0],
    ], {
      strokeColor: PURPLE,
      strokeWidth: 2,
      dash: 2,
      visible: false,
      label: { text: 'Tiệm cận ngang', position: 'rt', offset: [8, 8] },
    });
    hEls.forEach((el) => {
      ctx.setPos(el, [
        [-10, f.horizontal as number],
        [10, f.horizontal as number],
      ]);
      ctx.setVisible(el, revealed.has('horizontal_asymptote'));
    });
    const rEls = ctx.pool('root', f.root === null ? 0 : 1, 'point', [0, 0], {
      name: 'Giao điểm',
      size: 3,
      color: YELLOW,
      fixed: true,
      visible: false,
      showInfobox: true,
    });
    rEls.forEach((el) => {
      ctx.setPos(el, [f.root as number, 0]);
      ctx.setVisible(el, revealed.has('root'));
    });
  }, []);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const f = rationalFeatures(params as unknown as RationalParams);
    return (
      <>
        {revealed.has('vertical_asymptotes') && f.poles.length > 0 && (
          <span className="stat">
            Tiệm cận đứng: x = {formatNum(f.poles[0])}
          </span>
        )}
        {revealed.has('horizontal_asymptote') && f.horizontal !== null && (
          <span className="stat">
            Tiệm cận ngang: y = {formatNum(f.horizontal)}
          </span>
        )}
        {revealed.has('root') && f.root !== null && (
          <span className="stat">
            Giao điểm trục x: ({formatNum(f.root)}, 0)
          </span>
        )}
        <span className="stat muted">Tập xác định: {f.domain}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="rational-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[
        { key: 'vertical_asymptotes', label: 'Hiện tiệm cận đứng' },
        { key: 'horizontal_asymptote', label: 'Hiện tiệm cận ngang' },
        { key: 'root', label: 'Hiện giao điểm' },
      ]}
      sliders={[
        { key: 'a', min: -5, max: 5 },
        { key: 'b', min: -5, max: 5 },
        { key: 'c', min: -5, max: 5 },
        { key: 'd', min: -5, max: 5 },
      ]}
      steps={activity.steps ?? []}
    />
  );
}