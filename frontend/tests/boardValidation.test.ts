import { describe, expect, it } from 'vitest';

import { formatNum } from '../src/features/activities/quadraticMath';
import { objectBounds } from '../src/features/board/types';
import { isValidBoardObject, sanitizeBoard } from '../src/features/board/boardValidation';
import { isKnowledgeResponse } from '../src/features/knowledge/knowledgeTypes';

describe('boardValidation', () => {
  it('loại object bẩn khi import JSON', () => {
    expect(isValidBoardObject(null)).toBe(false);
    expect(isValidBoardObject({ id: '', type: 'stroke', points: [] })).toBe(false);
    expect(
      isValidBoardObject({ id: 's1', type: 'stroke', points: [0, NaN], color: '#000', strokeWidth: 3, x: 0, y: 0 }),
    ).toBe(false);
    expect(
      isValidBoardObject({ id: 't1', type: 'text', text: 'hi', x: 0, y: 0, fontSize: 20, color: '#000' }),
    ).toBe(true);
  });

  it('dọn activity mồ côi khi sanitize', () => {
    const clean = sanitizeBoard(
      [{ id: 'a1', type: 'activity', activityId: 'kept', x: 0, y: 0, width: 1, height: 1 }],
      { kept: { type: 'quadratic_function' }, orphan: { type: 'quadratic_function' } },
    );
    expect(clean).not.toBeNull();
    expect(Object.keys(clean!.activities)).toEqual(['kept']);
  });

  it('trả null khi cấu trúc bảng sai', () => {
    expect(sanitizeBoard('nope', {})).toBeNull();
    expect(sanitizeBoard([], null)).toBeNull();
  });

  it('bbox nét rỗng không tạo ghost object', () => {
    const bounds = objectBounds({ id: 's', type: 'stroke', points: [], color: '#000', strokeWidth: 3, x: 5, y: 7 });
    expect(bounds).toEqual({ x0: 5, y0: 7, x1: 5, y1: 7 });
  });

  it('bbox text nhiều dòng theo dòng dài nhất', () => {
    const bounds = objectBounds({ id: 't', type: 'text', text: 'ab\ncdef', x: 0, y: 0, fontSize: 10, color: '#000' });
    expect(bounds.x1).toBeCloseTo(10 * 4 * 0.6);
    expect(bounds.y1).toBeCloseTo(10 * 2 * 1.2);
  });

  it('formatNum không crash với undefined', () => {
    expect(formatNum(undefined as unknown as number)).toBe('?');
    expect(formatNum(Number.NaN)).toBe('?');
    expect(formatNum(2)).toBe('2');
  });

  it('chấp nhận citation link http hợp lệ', () => {
    const response = {
      schema_version: '1.0',
      topic: 'linear_function',
      items: [],
      citations: [{
        id: 'c1',
        source_id: 'mediawiki:en.wikipedia.org',
        title: 'T',
        url: 'http://en.wikipedia.org/wiki/X',
        contributors_url: 'http://en.wikipedia.org/wiki/X',
        license_name: 'CC',
        license_url: 'http://example.com/license',
        revision: '1',
        retrieved_at: '2026-01-01T00:00:00Z',
      }],
      cache: { policy: 'p', statuses: [], external_attempted: false },
      warning: '',
    };
    expect(isKnowledgeResponse(response)).toBe(true);
  });
});
