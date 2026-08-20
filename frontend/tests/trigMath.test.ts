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
  });

  it('b rất nhỏ được chống 0 (clamp xuống 0.01)', () => {
    const f = trigFeatures({ a: 1, b: 0, c: 0, d: 0 }, 'sin');
    expect(f.period).toBeCloseTo((2 * Math.PI) / 0.01, 4);
  });
});

describe('formatTrig', () => {
  it('định dạng sin/cos', () => {
    expect(formatTrig({ a: 2, b: 3, c: 1, d: 4 }, 'sin')).toContain('\\sin');
    expect(formatTrig({ a: 2, b: 3, c: 1, d: 4 }, 'cos')).toContain('\\cos');
  });
});