import { useCallback, useMemo } from 'react';

import type { ActivityModel } from './activityTypes';
import {
  ActivityCanvas,
  FEATURE_COLORS,
  type FeatureCtx,
} from './ActivityCanvas';
import { formatNum } from './quadraticMath';
import { formatTrig, trigFeatures, validateTrigParams, type TrigParams } from './trigMath';

const { yellow: YELLOW, green: GREEN } = FEATURE_COLORS;

export function TrigActivity({ activity }: { activity: ActivityModel }) {
  const func: 'sin' | 'cos' = activity.math.func === 'cos' ? 'cos' : 'sin';
  const sourceVariable = activity.math.source_variable ?? 'x';
  const dependentVariable = activity.math.dependent_variable ?? 'y';

  const initial = useMemo<Record<string, number>>(
    () => ({
      a: activity.math.a ?? 1,
      b: activity.math.b ?? 1,
      c: activity.math.c ?? 0,
      d: activity.math.d ?? 0,
    }),
    [activity],
  );

  const formula = useCallback(
    (p: Record<string, number>) => formatTrig(p as unknown as TrigParams, func, sourceVariable, dependentVariable),
    [dependentVariable, func, sourceVariable],
  );

  const curve = useCallback(
    (x: number, p: Record<string, number>) => {
      const q = p as unknown as TrigParams;
      const arg = q.b * x + q.c;
      return q.a * (func === 'sin' ? Math.sin(arg) : Math.cos(arg)) + q.d;
    },
    [func],
  );

  const validate = useCallback(
    (p: Record<string, number>) => validateTrigParams(p as unknown as TrigParams),
    [],
  );

  const drawFeatures = useCallback(
    (ctx: FeatureCtx) => {
      const { params, revealed } = ctx;
      const f = trigFeatures(params as unknown as TrigParams, func);
      const mEls = ctx.pool('midline', 1, 'line', [
        [-10, 0],
        [10, 0],
      ], {
        strokeColor: GREEN,
        strokeWidth: 2,
        dash: 2,
        visible: false,
        label: { text: 'Đường trung bình', position: 'rt', offset: [8, 8] },
      });
      mEls.forEach((el) => {
        ctx.setPos(el, [
          [-10, f.midline],
          [10, f.midline],
        ]);
        ctx.setVisible(el, revealed.has('midline'));
      });
      const eEls = ctx.pool('extr', 2, 'point', [0, 0], {
        size: 3,
        fixed: true,
        visible: false,
        showInfobox: true,
      });
      eEls.forEach((el, i) => {
        const [px, py] = i === 0 ? [f.xMax, f.maxValue] : [f.xMin, f.minValue];
        ctx.setPos(el, [px, py]);
        ctx.setVisible(el, revealed.has('max_min'));
      });
      const rEls = ctx.pool('root', f.roots.length, 'point', [0, 0], {
        name: 'Nghiệm',
        size: 3,
        color: YELLOW,
        fixed: true,
        visible: false,
      });
      rEls.forEach((el, i) => {
        ctx.setPos(el, [f.roots[i], 0]);
        ctx.setVisible(el, revealed.has('roots'));
      });
    },
    [func],
  );

  const stats = (params: Record<string, number>, revealed: Set<string>) => {
    const f = trigFeatures(params as unknown as TrigParams, func);
    return (
      <>
        {revealed.has('midline') && (
          <span className="stat">Đường trung bình: {dependentVariable} = {formatNum(f.midline)}</span>
        )}
        {revealed.has('max_min') && (
          <span className="stat">
            Giá trị: max {formatNum(f.maxValue)}, min {formatNum(f.minValue)}
          </span>
        )}
        {revealed.has('roots') && (
          <span className="stat">
            Nghiệm:{' '}
            {f.roots.length === 0
              ? 'không có'
               : f.roots.map((r) => `${sourceVariable} = ${formatNum(r)}`).join(', ')}
          </span>
        )}
        <span className="stat muted">Chu kỳ T = {formatNum(f.period)}</span>
      </>
    );
  };

  return (
    <ActivityCanvas
      testId="trig-activity"
      initial={initial}
      formula={formula}
      curve={curve}
      validate={validate}
      drawFeatures={drawFeatures}
      stats={stats}
      chips={[
        { key: 'midline', label: 'Hiện đường trung bình' },
        { key: 'max_min', label: 'Hiện giá trị max/min' },
        { key: 'roots', label: 'Hiện nghiệm' },
      ]}
      sliders={[
        { key: 'a', min: -5, max: 5 },
        { key: 'b', min: -5, max: 5 },
        { key: 'c', min: -10, max: 10 },
        { key: 'd', min: -10, max: 10 },
      ]}
      steps={activity.steps ?? []}
    />
  );
}
