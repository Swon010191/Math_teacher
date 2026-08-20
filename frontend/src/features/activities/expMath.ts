/** Tính toán thuần cho activity hàm mũ y = a*b^x + c. */

import { formatNum } from './quadraticMath';

export interface ExpParams {
  a: number;
  b: number;
  c: number;
}

export interface ExpFeatures {
  base: number;
  direction: 'up' | 'down';
  yIntercept: number;
  xIntercept: number | null;
  horizontalAsymptote: number;
}

export function safeBase(b: number): number {
  if (b <= 0) return 0.1;
  if (b === 1) return 1.01;
  return b;
}

export function expFeatures(p: ExpParams): ExpFeatures {
  const base = safeBase(p.b);
  const yIntercept = p.a + p.c;
  let xIntercept: number | null = null;
  if (p.a !== 0 && p.c !== 0 && -p.c / p.a > 0) {
    xIntercept = Math.log(-p.c / p.a) / Math.log(base);
  }
  return {
    base,
    direction: base > 1 ? 'up' : 'down',
    yIntercept,
    xIntercept,
    horizontalAsymptote: p.c,
  };
}

export function formatExp(p: ExpParams): string {
  const a = p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  let s = `y = ${a}${formatNum(p.b)}^x`;
  if (p.c !== 0) s += `${p.c > 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  return s;
}