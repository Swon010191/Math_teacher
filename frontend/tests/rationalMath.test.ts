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

  it('mẫu số đồng nhất bằng 0 bị từ chối', () => {
    expect(() => rationalFeatures({ a: 1, b: 1, c: 0, d: 0 })).toThrow();
  });

  it('phân biệt chính xác điểm khuyết với tiệm cận đứng', () => {
    const hole = rationalFeatures({ a: 1, b: -1, c: 1, d: -1 });
    expect(hole.poles).toEqual([1]);
    expect(hole.holes).toEqual([1]);
    expect(hole.verticalAsymptotes).toEqual([]);
    expect(hole.root).toBeNull();

    const almostCancelled = rationalFeatures({ a: 1, b: -1 + 1e-12, c: 1, d: -1 });
    expect(almostCancelled.holes).toEqual([]);
    expect(almostCancelled.verticalAsymptotes).toEqual([1]);
  });

  it('nhận diện cancellation decimal theo sai số tương đối ổn định', () => {
    const cancelled = rationalFeatures({ a: 0.3, b: 0.6, c: 0.1, d: 0.2 });
    expect(cancelled.holes).toEqual([-2]);
    expect(cancelled.verticalAsymptotes).toEqual([]);
    expect(cancelled.root).toBeNull();

    const distinct = rationalFeatures({ a: 0.3, b: 0.600000000001, c: 0.1, d: 0.2 });
    expect(distinct.holes).toEqual([]);
    expect(distinct.verticalAsymptotes).toEqual([-2]);
  });

  it('normalize hệ số trước proportional check để tránh underflow/overflow', () => {
    expect(
      rationalFeatures({ a: 1e-300, b: 2e-300, c: 2e-300, d: 4e-300 }).holes,
    ).toEqual([-2]);
    expect(
      rationalFeatures({ a: 1e-300, b: 3e-300, c: 2e-300, d: 4e-300 }).holes,
    ).toEqual([]);
    expect(
      rationalFeatures({ a: 1e300, b: 2e300, c: 2e300, d: 4e300 }).holes,
    ).toEqual([-2]);
  });
});

describe('formatRational', () => {
  it('định dạng phân thức', () => {
    expect(formatRational({ a: 2, b: 1, c: 1, d: -1 })).toBe('y = \\frac{2x +1}{x -1}');
  });
});
