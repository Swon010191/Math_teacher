import { describe, expect, it } from 'vitest';

import { expFeatures, formatExp, safeBase } from '../src/features/activities/expMath';

describe('safeBase', () => {
  it('từ chối base <= 0 và base = 1 thay vì thay giá trị', () => {
    expect(() => safeBase(0)).toThrow();
    expect(() => safeBase(-2)).toThrow();
    expect(() => safeBase(1)).toThrow();
    expect(safeBase(2)).toBe(2);
  });
});

describe('expFeatures', () => {
  it('tính giao điểm và tiệm cận cho 2*3^x - 1', () => {
    const f = expFeatures({ a: 2, b: 3, c: -1 });
    expect(f.base).toBe(3);
    expect(f.direction).toBe('up');
    expect(f.yIntercept).toBe(1);
    expect(f.horizontalAsymptote).toBe(-1);
    expect(f.xIntercept).not.toBeNull();
  });

  it('hàm đi xuống khi 0 < base < 1', () => {
    const f = expFeatures({ a: 1, b: 0.5, c: 0 });
    expect(f.direction).toBe('down');
    expect(f.xIntercept).toBeNull();
  });

  it('hệ số âm đảo chiều biến thiên', () => {
    expect(expFeatures({ a: -1, b: 2, c: 0 }).direction).toBe('down');
    expect(expFeatures({ a: -1, b: 0.5, c: 0 }).direction).toBe('up');
  });

  it('a = 0 là trạng thái suy biến', () => {
    expect(() => expFeatures({ a: 0, b: 2, c: 1 })).toThrow();
  });
});

describe('formatExp', () => {
  it('định dạng hàm mũ', () => {
    expect(formatExp({ a: 2, b: 3, c: -1 })).toBe('y = 23^x-1');
  });
});
