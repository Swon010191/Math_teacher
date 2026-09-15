import { describe, expect, it } from 'vitest';

import { classifyMathInput, extractVariables } from '../src/features/math/classifyMathInput';

describe('classifyMathInput', () => {
  it.each([
    ['x+y=2', 'solve'],
    ['2u+3=9', 'solve'],
    ['z=2t+1', 'function'],
    ['2x+1=y', 'function'],
    ['2x+1=5', 'solve'],
    ['f(t)=sin(t)+pi', 'function'],
    ['t^2-4t+3', 'function'],
  ] as const)('phân loại %s thành %s', (input, intent) => {
    expect(classifyMathInput(input).intent).toBe(intent);
  });

  it('chuẩn hóa hàm viết ngược nhưng giữ đúng biến nguồn/phụ thuộc', () => {
    expect(classifyMathInput('2x+1=y')).toMatchObject({
      sourceVariable: 'x',
      dependentVariable: 'y',
      canonicalInput: 'y=2x+1',
    });
  });

  it('trích biến ASCII theo thứ tự và bỏ tên hàm/hằng số', () => {
    expect(extractVariables('sin(alpha) + beta + pi + sqrt(beta)')).toEqual(['alpha', 'beta']);
  });

  it('nhận diện biến nguồn và biến phụ thuộc của định nghĩa hàm', () => {
    expect(classifyMathInput('z=2t+1')).toMatchObject({
      sourceVariable: 't',
      dependentVariable: 'z',
      variables: ['t'],
    });
  });

  it.each([
    ['x==2', 'solve'],
    ['x>=2', 'solve'],
    ['x<=2', 'solve'],
    ['x!=2', 'solve'],
  ] as const)('toán tử so sánh %s luôn là phương trình', (input, intent) => {
    expect(classifyMathInput(input).intent).toBe(intent);
  });
});
