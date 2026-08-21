/** Tính toán thuần cho activity hàm logarit y = a*log(x, base) + c. */

import { formatNum } from './quadraticMath';
import { safeBase } from './expMath';

export interface LogParams {
  a: number;
  b: number;
  c: number;
}

export interface LogFeatures {
  base: number;
  domain: string;
  xIntercept: number;
  direction: 'up' | 'down';
}

export function validateLogParams(p: LogParams): string | null {
  if (p.a === 0) return 'Tham số không hợp lệ: a phải khác 0.';
  if (p.b <= 0 || p.b === 1) return 'Tham số không hợp lệ: b phải dương và khác 1.';
  return null;
}

export function logFeatures(p: LogParams): LogFeatures {
  const error = validateLogParams(p);
  if (error) throw new RangeError(error);
  const base = safeBase(p.b);
  return {
    base,
    domain: 'x > 0',
    xIntercept: Math.pow(base, -p.c / p.a),
    direction: p.a / Math.log(base) > 0 ? 'up' : 'down',
  };
}

export function formatLog(p: LogParams, sourceVariable = 'x', dependentVariable = 'y'): string {
  const a = p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  let s = `${dependentVariable} = ${a}\\log_{${formatNum(p.b)}}(${sourceVariable})`;
  if (p.c !== 0) s += `${p.c > 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  return s;
}
