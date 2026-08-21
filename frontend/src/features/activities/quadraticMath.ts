/** Tính toán thuần (không phụ thuộc UI) cho activity hàm bậc hai.
 *
 * Math Engine (SymPy) là nguồn sự thật cho lần phân tích đầu tiên;
 * module này chỉ tái tính đặc trưng khi giáo viên kéo slider (công thức
 * đã được xác nhận, chỉ thay tham số).
 */

export interface QuadraticParams {
  a: number;
  b: number;
  c: number;
}

export interface QuadraticFeatures {
  a: number;
  discriminant: number;
  h: number;
  k: number;
  roots: number[];
}

export function quadraticFeatures(p: QuadraticParams): QuadraticFeatures {
  const a = p.a === 0 ? 0.0001 : p.a;
  const discriminant = p.b * p.b - 4 * a * p.c;
  const h = -p.b / (2 * a);
  const k = -discriminant / (4 * a);
  let roots: number[] = [];
  if (discriminant > 0) {
    roots = [
      (-p.b - Math.sqrt(discriminant)) / (2 * a),
      (-p.b + Math.sqrt(discriminant)) / (2 * a),
    ].sort((x, y) => x - y);
  } else if (Math.abs(discriminant) < 1e-9) {
    roots = [h];
  }
  return { a, discriminant, h, k, roots };
}

export function formatNum(n: number): string {
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(2).replace(/\.?0+$/, '');
}

export function formatQuadratic(
  p: QuadraticParams,
  sourceVariable = 'x',
  dependentVariable = 'y',
): string {
  const { a, b, c } = p;
  const parts: string[] = [];
  if (a !== 0) {
    parts.push(a === 1 ? `${sourceVariable}^2` : a === -1 ? `-${sourceVariable}^2` : `${formatNum(a)}${sourceVariable}^2`);
  }
  if (b !== 0) {
    parts.push(`${b > 0 && parts.length > 0 ? '+' : ''}${formatNum(b)}${sourceVariable}`);
  }
  if (c !== 0 || parts.length === 0) {
    parts.push(`${c > 0 && parts.length > 0 ? '+' : ''}${formatNum(c)}`);
  }
  return `${dependentVariable} = ${parts.join(' ')}`;
}
