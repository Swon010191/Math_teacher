import { del, get, keys, set } from 'idb-keyval';

import { isKnowledgeResponse, type KnowledgeResponse } from './knowledgeTypes';

export type KnowledgeActivityType =
  | 'linear_function'
  | 'quadratic_function'
  | 'linear_equation'
  | 'quadratic_equation';

interface KnowledgeCacheEntry {
  cachedAt: number;
  response: KnowledgeResponse;
}

const CACHE_PREFIX = 'knowledge:1.0:';
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const CACHE_MAX_ENTRIES = 40;

function expressionHash(value: string): string {
  let hash = 0xcbf29ce484222325n;
  for (const char of value.trim()) {
    hash ^= BigInt(char.codePointAt(0) ?? 0);
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, '0');
}

export function knowledgeCacheKey(activityType: KnowledgeActivityType, expression: string): string {
  return `${CACHE_PREFIX}${activityType}:${expressionHash(expression)}`;
}

export async function loadKnowledgeCache(
  activityType: KnowledgeActivityType,
  expression: string,
): Promise<KnowledgeResponse | null> {
  const key = knowledgeCacheKey(activityType, expression);
  const cached: unknown = await get(key);
  if (!isCacheEntry(cached) || Date.now() - cached.cachedAt > CACHE_TTL_MS) {
    if (cached != null) await del(key);
    return null;
  }
  return cached.response;
}

export async function saveKnowledgeCache(
  activityType: KnowledgeActivityType,
  expression: string,
  response: KnowledgeResponse,
): Promise<void> {
  if (isKnowledgeResponse(response)) {
    await set(knowledgeCacheKey(activityType, expression), {
      cachedAt: Date.now(),
      response,
    } satisfies KnowledgeCacheEntry);
    await pruneKnowledgeCache();
  }
}

function isCacheEntry(value: unknown): value is KnowledgeCacheEntry {
  if (typeof value !== 'object' || value === null) return false;
  const entry = value as Partial<KnowledgeCacheEntry>;
  return typeof entry.cachedAt === 'number' && isKnowledgeResponse(entry.response);
}

async function pruneKnowledgeCache(): Promise<void> {
  const cacheKeys = (await keys()).filter(
    (key): key is string => typeof key === 'string' && key.startsWith(CACHE_PREFIX),
  );
  if (cacheKeys.length <= CACHE_MAX_ENTRIES) return;
  const entries = await Promise.all(cacheKeys.map(async (key) => ({ key, value: await get(key) })));
  entries.sort((a, b) => {
    const aTime = isCacheEntry(a.value) ? a.value.cachedAt : 0;
    const bTime = isCacheEntry(b.value) ? b.value.cachedAt : 0;
    return aTime - bTime;
  });
  await Promise.all(entries.slice(0, entries.length - CACHE_MAX_ENTRIES).map(({ key }) => del(key)));
}
