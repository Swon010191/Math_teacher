import { useCallback, useMemo, useState } from 'react';

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
  validateRationalParams,
  type RationalParams,
} from './rationalMath';

const { yellow: YELLOW, purple: PURPLE } = FEATURE_COLORS;

export function RationalActivity({ activity }: { activity: ActivityModel }) {
  const [paramsChanged, setParamsChanged] = useState(false);
  const sourceVariable = activity.math.source_variable ?? 'x';
  const dependentVariable = activity.math.dependent_variable ?? 'y';
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
    (p: Record<string, number>) => formatRational(p as unknown as RationalParams, sourceVariable, dependentVariable),
    [dependentVariable, sourceVariable],
  );

  const curve = useCallback((x: number, p: Record<string, number>) => {
    const q = p as unknown as RationalParams;
    const den = q.c * x + q.d;
    if (Math.abs(den) < 1e-9) return NaN;
    return (q.a * x + q.b) / den;
  }, []);

  const validate = useCallback(
    (p: Record<string, number>) => validateRationalParams(p as unknown as RationalParams),
    [],
  );

  const features = useCallback(
    (params: Record<string, number>) => {
      const calculated = rationalFeatures(params as unknown as RationalParams);
      if (paramsChanged) return calculated;
      return {
        ...calculated,
        holes: activity.math.holes ?? calculated.holes,
        root:
          activity.math.root === undefined ? calculated.root : activity.math.root,
        domain: activity.math.domain ?? calculated.domain,
      };
    },
    [
      activity.math.domain,
      activity.math.holes,
      activity.math.root,
      paramsChanged,
    ],
  );

  const holeY = (
    hole: number,
    params: Record<string, number>,
    horizontal: number | null,
  ): number | null => {
    const denominator = params.c * hole + params.d;
    return denominator !== 0
      ? (params.a * hole + params.b) / denominator
      : horizontal;
  };

  const drawFeatures = useCallback((ctx: FeatureCtx) => {
    const { params, revealed } = ctx;
    const f = features(params);
    const vEls = ctx.pool('vasym', f.verticalAsymptotes.length, 'line', [
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
        [f.verticalAsymptotes[i], -10],
        [f.verticalAsymptotes[i], 10],
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
    const holeEls = ctx.pool('hole', f.holes.length, 'point', [0, 0], {
      name: 'Điểm khuyết',
      size: 4,
      strokeColor: YELLOW,
      fillColor: '#ffffff',
      fillOpacity: 1,
      fixed: true,
      visible: true,
      showInfobox: true,
    });
    holeEls.forEach((el, i) => {
      const y = holeY(f.holes[i], params, f.horizontal);
      if (y !== null && Number.isFinite(y)) ctx.setPos(el, [f.holes[i], y]);
      ctx.setVisible(el, y !== null && Number.isFinite(y));
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
  }, [features]);

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const f = features(params);
    return (
      <>
        {revealed.has('vertical_asymptotes') && f.verticalAsymptotes.length > 0 && (
          <span className="stat">
            Tiệm cận đứng: {sourceVariable} = {formatNum(f.verticalAsymptotes[0])}
          </span>
        )}
        {revealed.has('horizontal_asymptote') && f.horizontal !== null && (
          <span className="stat">
            Tiệm cận ngang: {dependentVariable} = {formatNum(f.horizontal)}
          </span>
        )}
        {revealed.has('root') && f.root !== null && (
          <span className="stat">
            Giao điểm trục {sourceVariable}: ({formatNum(f.root)}, 0)
          </span>
        )}
        {f.holes.map((hole) => {
          const y = holeY(hole, params, f.horizontal);
          return y === null || !Number.isFinite(y) ? null : (
            <span className="stat" key={`hole-${hole}`}>
              Điểm khuyết: ({formatNum(hole)}, {formatNum(y)})
            </span>
          );
        })}
        <span className="stat muted">Tập xác định: {f.domain.replace(/\bx\b/g, sourceVariable)}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="rational-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      validate={validate}
      onParamsChanged={() => setParamsChanged(true)}
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
