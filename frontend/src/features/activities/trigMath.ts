/** Tính toán thuần cho activity hàm lượng giác y = a*sin(bx + c) + d hoặc a*cos(bx + c) + d. */

import { formatNum } from './quadraticMath';

export interface TrigParams {
  a: number;
  b: number;
  c: number;
  d: number;
}

export interface TrigFeatures {
  amplitude: number;
  period: number;
  phaseShift: number;
  midline: number;
  maxValue: number;
  minValue: number;
  xMax: number;
  xMin: number;
  roots: number[];
}

export function validateTrigParams(p: TrigParams): string | null {
  if (p.a === 0) return 'Tham số không hợp lệ: a phải khác 0.';
  if (p.b === 0) return 'Tham số không hợp lệ: b phải khác 0.';
  return null;
}

function ulp(value: number): number {
  if (value === 0) return Number.MIN_VALUE;
  const exponent = Math.floor(Math.log2(Math.abs(value)));
  return exponent < -1022 ? Number.MIN_VALUE : 2 ** (exponent - 52);
}

function analyticalRoots(
  p: TrigParams,
  func: 'sin' | 'cos',
  center: number,
  period: number,
): number[] {
  const lo = center - period;
  const hi = center + period;
  const scale = Math.max(Math.abs(lo), Math.abs(hi), Math.abs(center), Math.abs(period), Number.MIN_VALUE);
  const boundaryTolerance = Math.max(Math.abs(period) * 1e-12, Number.EPSILON * scale * 4);
  let target = -p.d / p.a;
  const targetTolerance = Math.max(
    4 * ulp(target),
    (4 * (ulp(p.d) + Math.abs(target) * ulp(p.a))) / Math.abs(p.a),
  );
  if (target > 1 && target <= 1 + targetTolerance) target = 1;
  else if (target < -1 && target >= -1 - targetTolerance) target = -1;
  else if (target < -1 || target > 1) return [];
  const principal = func === 'sin' ? Math.asin(target) : Math.acos(target);
  const families = func === 'sin' ? [principal, Math.PI - principal] : [principal, -principal];
  const roots = families.flatMap((theta) =>
    Array.from({ length: 7 }, (_, index) => index - 3)
      .map((k) => (theta + 2 * Math.PI * k - p.c) / p.b)
      .filter((root) => root >= lo - boundaryTolerance && root <= hi + boundaryTolerance),
  );
  roots.sort((left, right) => left - right);
  const deduped: number[] = [];
  for (const r of roots) {
    const previous = deduped[deduped.length - 1];
    const rootScale = Math.max(Math.abs(r), Math.abs(previous ?? 0), Math.abs(period), Number.MIN_VALUE);
    const tolerance = Math.max(Math.abs(period) * 1e-12, Number.EPSILON * rootScale * 4);
    if (!deduped.length || Math.abs(r - previous) > tolerance) {
      deduped.push(r);
    }
  }
  return deduped;
}

export function trigFeatures(p: TrigParams, func: 'sin' | 'cos'): TrigFeatures {
  const error = validateTrigParams(p);
  if (error) throw new RangeError(error);
  const a = p.a;
  const b = p.b;
  const amplitude = Math.abs(a);
  const period = (2 * Math.PI) / Math.abs(b);
  const phaseShift = -p.c / b;
  const windowResolution = Math.max(
    ulp(phaseShift),
    ulp(phaseShift - period),
    ulp(phaseShift + period),
  );
  if (period <= windowResolution) {
    throw new RangeError('Chu kỳ nhỏ hơn độ phân giải tại cửa sổ phân tích.');
  }
  const midline = p.d;
  const positiveMaximum = func === 'sin' ? Math.PI / 2 : 0;
  const thetaMax = a > 0 ? positiveMaximum : positiveMaximum + Math.PI;
  const thetaMin = a > 0 ? positiveMaximum + Math.PI : positiveMaximum;
  const xMax = (thetaMax - p.c) / b;
  const xMin = (thetaMin - p.c) / b;
  const roots = analyticalRoots(p, func, phaseShift, period);
  return {
    amplitude,
    period,
    phaseShift,
    midline,
    maxValue: amplitude + midline,
    minValue: midline - amplitude,
    xMax,
    xMin,
    roots,
  };
}

export function formatTrig(
  p: TrigParams,
  func: 'sin' | 'cos',
  sourceVariable = 'x',
  dependentVariable = 'y',
): string {
  const amp =
    p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  const inner = `${formatNum(p.b)}${sourceVariable}${p.c >= 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  let s = `${dependentVariable} = ${amp}\\${func}(${inner})`;
  if (p.d !== 0) s += `${p.d > 0 ? '+' : '-'}${formatNum(Math.abs(p.d))}`;
  return s;
}
