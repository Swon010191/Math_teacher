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
  if (b <= 0 || b === 1) throw new RangeError('Cơ số b phải dương và khác 1.');
  return b;
}

export function validateExpParams(p: ExpParams): string | null {
  if (p.a === 0) return 'Tham số không hợp lệ: a phải khác 0.';
  if (p.b <= 0 || p.b === 1) return 'Tham số không hợp lệ: b phải dương và khác 1.';
  return null;
}

export function expFeatures(p: ExpParams): ExpFeatures {
  const error = validateExpParams(p);
  if (error) throw new RangeError(error);
  const base = safeBase(p.b);
  const yIntercept = p.a + p.c;
  let xIntercept: number | null = null;
  if (p.a !== 0 && p.c !== 0 && -p.c / p.a > 0) {
    xIntercept = Math.log(-p.c / p.a) / Math.log(base);
  }
  return {
    base,
    direction: p.a * Math.log(base) > 0 ? 'up' : 'down',
    yIntercept,
    xIntercept,
    horizontalAsymptote: p.c,
  };
}

export function formatExp(p: ExpParams, sourceVariable = 'x', dependentVariable = 'y'): string {
  const a = p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  let s = `${dependentVariable} = ${a}${formatNum(p.b)}^${sourceVariable}`;
  if (p.c !== 0) s += `${p.c > 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  return s;
}
