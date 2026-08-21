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
  holes: number[];
  verticalAsymptotes: number[];
  horizontal: number | null;
  root: number | null;
  yIntercept: number | null;
  domain: string;
}

export function validateRationalParams(p: RationalParams): string | null {
  return p.c === 0 && p.d === 0
    ? 'Tham số không hợp lệ: mẫu số không thể đồng nhất bằng 0.'
    : null;
}

export function rationalFeatures(p: RationalParams): RationalFeatures {
  const error = validateRationalParams(p);
  if (error) throw new RangeError(error);
  const poles = p.c !== 0 ? [-p.d / p.c] : [];
  const coefficientScale = Math.max(
    Math.abs(p.a),
    Math.abs(p.b),
    Math.abs(p.c),
    Math.abs(p.d),
  );
  const normalizedA = p.a / coefficientScale;
  const normalizedB = p.b / coefficientScale;
  const normalizedC = p.c / coefficientScale;
  const normalizedD = p.d / coefficientScale;
  const left = normalizedA * normalizedD;
  const right = normalizedB * normalizedC;
  const cancellationTolerance =
    Number.EPSILON * 16 * Math.max(Math.abs(left), Math.abs(right), Number.MIN_VALUE);
  const cancelled = p.c !== 0 && Math.abs(left - right) <= cancellationTolerance;
  const holes = cancelled ? poles : [];
  const verticalAsymptotes = cancelled ? [] : poles;
  const horizontal = p.c !== 0 ? p.a / p.c : null;
  const rootCandidate = p.a !== 0 ? -p.b / p.a : null;
  const root = cancelled ? null : rootCandidate;
  const yIntercept = p.d !== 0 ? p.b / p.d : null;
  const domain = poles.length > 0 ? `x ≠ ${formatNum(poles[0])}` : 'R';
  return { poles, holes, verticalAsymptotes, horizontal, root, yIntercept, domain };
}

function formatLinear(coef: number, constant: number, variable: string): string {
  const parts: string[] = [];
  if (coef !== 0) {
    parts.push(coef === 1 ? variable : coef === -1 ? `-${variable}` : `${formatNum(coef)}${variable}`);
  }
  if (constant !== 0 || parts.length === 0) {
    parts.push(`${constant > 0 && parts.length > 0 ? '+' : ''}${formatNum(constant)}`);
  }
  return parts.join(' ');
}

export function formatRational(p: RationalParams, sourceVariable = 'x', dependentVariable = 'y'): string {
  return `${dependentVariable} = \\frac{${formatLinear(p.a, p.b, sourceVariable)}}{${formatLinear(p.c, p.d, sourceVariable)}}`;
}
