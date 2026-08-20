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

function safeB(b: number): number {
  return Math.abs(b) < 1e-6 ? (b < 0 ? -0.01 : 0.01) : b;
}

function numericRoots(
  f: (x: number) => number,
  center: number,
  period: number,
): number[] {
  const lo = center - period;
  const hi = center + period;
  const roots: number[] = [];
  const step = 0.02;
  let prevT = lo;
  let prevY = f(lo);
  let t = lo + step;
  while (t <= hi + 1e-9) {
    const y = f(t);
    if (Number.isFinite(prevY) && Number.isFinite(y)) {
      if (prevY === 0) roots.push(prevT);
      else if ((prevY > 0) !== (y > 0)) roots.push((prevT + t) / 2);
    }
    prevT = t;
    prevY = y;
    t += step;
  }
  const deduped: number[] = [];
  for (const r of roots) {
    if (!deduped.length || Math.abs(r - deduped[deduped.length - 1]) > 0.05) {
      deduped.push(r);
    }
  }
  return deduped.map((r) => Math.round(r * 100) / 100);
}

export function trigFeatures(p: TrigParams, func: 'sin' | 'cos'): TrigFeatures {
  const a = p.a === 0 ? 0.0001 : p.a;
  const b = safeB(p.b);
  const amplitude = Math.abs(a);
  const period = (2 * Math.PI) / Math.abs(b);
  const phaseShift = -p.c / b;
  const midline = p.d;
  const base = func === 'sin' ? Math.PI / 2 : 0;
  const xMax = (base - p.c) / b;
  const xMin = (base + Math.PI - p.c) / b;
  const rootFn = (x: number) => a * (func === 'sin' ? Math.sin(b * x + p.c) : Math.cos(b * x + p.c)) + p.d;
  const roots = numericRoots(rootFn, phaseShift, period);
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

export function formatTrig(p: TrigParams, func: 'sin' | 'cos'): string {
  const amp =
    p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  const inner = `${formatNum(p.b)}x${p.c >= 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  let s = `y = ${amp}\\${func}(${inner})`;
  if (p.d !== 0) s += `${p.d > 0 ? '+' : '-'}${formatNum(Math.abs(p.d))}`;
  return s;
}