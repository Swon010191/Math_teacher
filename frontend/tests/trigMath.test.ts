import { describe, expect, it } from 'vitest';

import { formatTrig, trigFeatures } from '../src/features/activities/trigMath';

describe('trigFeatures', () => {
  it('tính biên độ, chu kỳ, đường trung bình cho 2*sin(3x+1)+4', () => {
    const f = trigFeatures({ a: 2, b: 3, c: 1, d: 4 }, 'sin');
    expect(f.amplitude).toBe(2);
    expect(f.period).toBeCloseTo((2 * Math.PI) / 3, 6);
    expect(f.midline).toBe(4);
    expect(f.maxValue).toBe(6);
    expect(f.minValue).toBe(2);
    expect(f.roots).toEqual([]);
  });

  it('hàm cos lệch pha giữ nguyên max/min', () => {
    const f = trigFeatures({ a: -3, b: 1, c: 0, d: 0 }, 'cos');
    expect(f.maxValue).toBe(3);
    expect(f.minValue).toBe(-3);
    expect(f.xMax).toBeCloseTo(Math.PI, 10);
    expect(f.xMin).toBeCloseTo(0, 10);
  });

  it('a = 0 hoặc b = 0 là trạng thái suy biến', () => {
    expect(() => trigFeatures({ a: 1, b: 0, c: 0, d: 0 }, 'sin')).toThrow();
    expect(() => trigFeatures({ a: 0, b: 1, c: 0, d: 0 }, 'sin')).toThrow();
  });

  it('tìm nghiệm tiếp xúc bằng công thức giải tích', () => {
    const f = trigFeatures({ a: 1, b: 1, c: 0, d: 1 }, 'sin');
    expect(f.roots).toContain(-Math.PI / 2);
    expect(f.roots).toContain((3 * Math.PI) / 2);
  });

  it('không gộp nghiệm khi chu kỳ rất nhỏ', () => {
    const f = trigFeatures({ a: 1, b: 1_000_000, c: 0, d: 0 }, 'sin');
    expect(f.roots.length).toBeGreaterThanOrEqual(3);
    expect(new Set(f.roots).size).toBe(f.roots.length);
    expect(f.roots[1] - f.roots[0]).toBeLessThan(1e-5);
  });

  it('không gộp nghiệm ở tần số xấp xỉ 1e16', () => {
    const f = trigFeatures({ a: 1, b: 1e16, c: 0, d: 0 }, 'sin');
    expect(f.roots.length).toBeGreaterThanOrEqual(3);
    expect(f.roots.every((root, index) => index === 0 || root > f.roots[index - 1])).toBe(true);
  });

  it('clamp target sát biên và dedup nghiệm tiếp xúc', () => {
    const f = trigFeatures({ a: 1, b: 1, c: 0, d: -1.0000000000000002 }, 'sin');
    expect(f.roots).toHaveLength(2);
    expect(f.roots[0]).toBeLessThan(f.roots[1]);
  });

  it('từ chối period nhỏ hơn ULP tại phase', () => {
    expect(() => trigFeatures({ a: 1, b: 1e17, c: 1e17, d: 0 }, 'sin')).toThrow();
  });
});

describe('formatTrig', () => {
  it('định dạng sin/cos', () => {
    expect(formatTrig({ a: 2, b: 3, c: 1, d: 4 }, 'sin')).toContain('\\sin');
    expect(formatTrig({ a: 2, b: 3, c: 1, d: 4 }, 'cos')).toContain('\\cos');
  });
});
