/** Tính toán thuần cho activity hàm phân thức bậc nhất/bậc nhất y = (ax + b)/(cx + d). */

import { formatNum } from './quadraticMath';

export interface RationalParams {
  a: number;
  b: number;
  c: number;
  d: number;
}

export interface RationalFeatures {
  poles: number[];
  horizontal: number | null;
  root: number | null;
  yIntercept: number | null;
  domain: string;
}

export function rationalFeatures(p: RationalParams): RationalFeatures {
  const c = p.c === 0 && p.d === 0 ? 0.0001 : p.c;
  const poles = c !== 0 ? [-p.d / c] : [];
  const horizontal = c !== 0 ? p.a / c : null;
  const root = p.a !== 0 ? -p.b / p.a : null;
  const yIntercept = p.d !== 0 ? p.b / p.d : null;
  const domain = poles.length > 0 ? `x ≠ ${formatNum(poles[0])}` : 'R';
  return { poles, horizontal, root, yIntercept, domain };
}

function formatLinear(coef: number, constant: number): string {
  const parts: string[] = [];
  if (coef !== 0) {
    parts.push(coef === 1 ? 'x' : coef === -1 ? '-x' : `${formatNum(coef)}x`);
  }
  if (constant !== 0 || parts.length === 0) {
    parts.push(`${constant > 0 && parts.length > 0 ? '+' : ''}${formatNum(constant)}`);
  }
  return parts.join(' ');
}

export function formatRational(p: RationalParams): string {
  return `y = \\frac{${formatLinear(p.a, p.b)}}{${formatLinear(p.c, p.d)}}`;
}