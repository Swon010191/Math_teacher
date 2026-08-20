import { describe, expect, it } from 'vitest';

import { formatLog, logFeatures } from '../src/features/activities/logMath';

describe('logFeatures', () => {
  it('tính giao điểm cho 2*log10(x) - 1', () => {
    const f = logFeatures({ a: 2, b: 10, c: -1 });
    expect(f.base).toBe(10);
    expect(f.domain).toBe('x > 0');
    expect(f.xIntercept).toBeCloseTo(Math.pow(10, 0.5), 6);
  });

  it('a = 0 được chống 0', () => {
    const f = logFeatures({ a: 0, b: 10, c: 1 });
    expect(f.xIntercept).toBeCloseTo(Math.pow(10, -10000), 0);
  });
});

describe('formatLog', () => {
  it('định dạng logarit', () => {
    expect(formatLog({ a: 2, b: 10, c: -1 })).toContain('\\log_{10}(x)');
  });
});