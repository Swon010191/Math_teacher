import { describe, expect, it } from 'vitest';

import { formatNum, formatQuadratic, quadraticFeatures } from '../src/features/activities/quadraticMath';

describe('quadraticFeatures', () => {
  it('tính đỉnh, nghiệm, trục đối xứng của y = x^2 - 4x + 3', () => {
    const f = quadraticFeatures({ a: 1, b: -4, c: 3 });
    expect(f.h).toBe(2);
    expect(f.k).toBe(-1);
    expect(f.discriminant).toBe(4);
    expect(f.roots).toEqual([1, 3]);
  });

  it('bề lõm xuống khi a âm', () => {
    const f = quadraticFeatures({ a: -1, b: 6, c: -5 });
    expect(f.h).toBe(3);
    expect(f.k).toBe(4);
    expect(f.roots).toEqual([1, 5]);
  });

  it('vô nghiệm thực khi delta âm', () => {
    const f = quadraticFeatures({ a: 1, b: 0, c: 1 });
    expect(f.roots).toEqual([]);
  });

  it('nghiệm kép khi delta bằng 0', () => {
    const f = quadraticFeatures({ a: 1, b: -2, c: 1 });
    expect(f.roots).toEqual([1]);
  });

  it('không chia cho 0 khi a = 0', () => {
    const f = quadraticFeatures({ a: 0, b: 2, c: 1 });
    expect(Number.isFinite(f.h)).toBe(true);
    expect(f.a).toBeCloseTo(0.0001);
  });
});

describe('formatQuadratic', () => {
  it('định dạng dấu đúng', () => {
    expect(formatQuadratic({ a: 1, b: -4, c: 3 })).toBe('y = x^2 -4x +3');
    expect(formatQuadratic({ a: -2, b: 3, c: -1 })).toBe('y = -2x^2 +3x -1');
    expect(formatQuadratic({ a: 1, b: 0, c: 0 })).toBe('y = x^2');
  });
});

describe('formatNum', () => {
  it('bỏ số 0 thừa', () => {
    expect(formatNum(2)).toBe('2');
    expect(formatNum(2.5)).toBe('2.5');
  });
});