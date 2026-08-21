import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { KnowledgeResponse } from '../src/features/knowledge/knowledgeTypes';

const storage = vi.hoisted(() => new Map<IDBValidKey, unknown>());

vi.mock('idb-keyval', () => ({
  get: vi.fn(async (key: IDBValidKey) => storage.get(key)),
  set: vi.fn(async (key: IDBValidKey, value: unknown) => { storage.set(key, value); }),
  del: vi.fn(async (key: IDBValidKey) => { storage.delete(key); }),
  keys: vi.fn(async () => [...storage.keys()]),
}));

import {
  knowledgeCacheKey,
  loadKnowledgeCache,
  saveKnowledgeCache,
} from '../src/features/knowledge/knowledgeCache';

const response: KnowledgeResponse = {
  schema_version: '1.0',
  topic: 'linear_function',
  items: [{
    id: 'builtin', source_id: 'builtin:curated-vi', title: 'Hàm số bậc nhất',
    original_text: 'Nội dung', vietnamese_text: 'Nội dung', original_language: 'vi',
    translation_status: 'original', citation_id: 'citation', cache_status: 'builtin',
  }],
  citations: [{
    id: 'citation', source_id: 'builtin:curated-vi', title: 'Hàm số bậc nhất',
    url: 'https://example.test/source', contributors_url: 'https://example.test/authors',
    license_name: 'MIT', license_url: 'https://example.test/license', revision: '1',
    retrieved_at: '2026-08-21T00:00:00Z',
  }],
  cache: { policy: 'test', statuses: ['builtin'], external_attempted: false },
  warning: 'Nội dung tham khảo.',
};

describe('knowledgeCache', () => {
  beforeEach(() => {
    storage.clear();
    vi.restoreAllMocks();
  });

  it('không lưu biểu thức thô trong key và đọc lại response hợp lệ', async () => {
    const expression = '2*x + private_parameter';
    const key = knowledgeCacheKey('linear_function', expression);
    expect(key).not.toContain(expression);
    expect(key).not.toContain('private_parameter');

    await saveKnowledgeCache('linear_function', expression, response);
    await expect(loadKnowledgeCache('linear_function', expression)).resolves.toEqual(response);
  });

  it('xóa cache quá hạn và giới hạn tối đa 40 chủ đề', async () => {
    const now = vi.spyOn(Date, 'now');
    now.mockReturnValue(1_000);
    await saveKnowledgeCache('linear_function', 'expired', response);
    now.mockReturnValue(8 * 24 * 60 * 60 * 1000);
    await expect(loadKnowledgeCache('linear_function', 'expired')).resolves.toBeNull();

    for (let index = 0; index < 45; index += 1) {
      now.mockReturnValue(10_000 + index);
      await saveKnowledgeCache('linear_function', `x + ${index}`, response);
    }
    expect(storage.size).toBe(40);
  });
});
