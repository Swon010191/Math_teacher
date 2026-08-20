import { describe, expect, it } from 'vitest';

import { formatRational, rationalFeatures } from '../src/features/activities/rationalMath';

describe('rationalFeatures', () => {
  it('tính pole, tiệm cận ngang và nghiệm cho (2x+1)/(x-1)', () => {
    const f = rationalFeatures({ a: 2, b: 1, c: 1, d: -1 });
    expect(f.poles).toEqual([1]);
    expect(f.horizontal).toBe(2);
    expect(f.root).toBe(-0.5);
    expect(f.yIntercept).toBe(-1);
    expect(f.domain).toBe('x ≠ 1');
  });

  it('tử số hằng số thì không có nghiệm', () => {
    const f = rationalFeatures({ a: 0, b: 1, c: 1, d: 1 });
    expect(f.root).toBeNull();
    expect(f.horizontal).toBe(0);
  });

  it('mẫu số suy biến được chống 0', () => {
    const f = rationalFeatures({ a: 1, b: 1, c: 0, d: 0 });
    expect(f.poles.length).toBeGreaterThan(0);
  });
});

describe('formatRational', () => {
  it('định dạng phân thức', () => {
    expect(formatRational({ a: 2, b: 1, c: 1, d: -1 })).toBe('y = \\frac{2x +1}{x -1}');
  });
});