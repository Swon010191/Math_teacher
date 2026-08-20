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
}

export function logFeatures(p: LogParams): LogFeatures {
  const base = safeBase(p.b);
  const a = p.a === 0 ? 0.0001 : p.a;
  return {
    base,
    domain: 'x > 0',
    xIntercept: Math.pow(base, -p.c / a),
  };
}

export function formatLog(p: LogParams): string {
  const a = p.a === 0 ? '0' : p.a === 1 ? '' : p.a === -1 ? '-' : formatNum(p.a);
  let s = `y = ${a}\\log_{${formatNum(p.b)}}(x)`;
  if (p.c !== 0) s += `${p.c > 0 ? '+' : '-'}${formatNum(Math.abs(p.c))}`;
  return s;
}