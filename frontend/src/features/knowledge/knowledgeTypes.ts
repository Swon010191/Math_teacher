export interface KnowledgeRequest {
  expression: string;
  include_original: boolean;
  include_vietnamese: boolean;
}

export interface KnowledgeCitation {
  id: string;
  source_id: string;
  title: string;
  url: string;
  contributors_url: string;
  license_name: string;
  license_url: string;
  revision: string;
  retrieved_at: string;
}

export interface KnowledgeItem {
  id: string;
  source_id: string;
  title: string;
  original_text: string | null;
  vietnamese_text: string | null;
  original_language: string;
  translation_status: string;
  citation_id: string;
  cache_status: string;
}

export interface KnowledgeCacheProvenance {
  policy: string;
  statuses: string[];
  external_attempted: boolean;
}

export interface KnowledgeResponse {
  schema_version: string;
  topic: string;
  items: KnowledgeItem[];
  citations: KnowledgeCitation[];
  cache: KnowledgeCacheProvenance;
  warning: string;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const hasStrings = (value: Record<string, unknown>, keys: string[]) =>
  keys.every((key) => typeof value[key] === 'string');

function isCitation(value: unknown): value is KnowledgeCitation {
  if (!isRecord(value) || !hasStrings(value, [
    'id', 'source_id', 'title', 'url', 'contributors_url', 'license_name',
    'license_url', 'revision', 'retrieved_at',
  ])) return false;
  return ['url', 'contributors_url', 'license_url'].every((key) => {
    try {
      const protocol = new URL(value[key] as string).protocol;
      return protocol === 'https:' || protocol === 'http:';
    } catch {
      return false;
    }
  });
}

function isItem(value: unknown): value is KnowledgeItem {
  return isRecord(value)
    && hasStrings(value, [
      'id', 'source_id', 'title', 'original_language', 'translation_status',
      'citation_id', 'cache_status',
    ])
    && (typeof value.original_text === 'string' || value.original_text === null)
    && (typeof value.vietnamese_text === 'string' || value.vietnamese_text === null);
}

export function isKnowledgeResponse(value: unknown): value is KnowledgeResponse {
  if (!isRecord(value) || !hasStrings(value, ['schema_version', 'topic', 'warning'])) return false;
  if (value.schema_version !== '1.0' || !Array.isArray(value.items) || !value.items.every(isItem)) return false;
  if (!Array.isArray(value.citations) || !value.citations.every(isCitation) || !isRecord(value.cache)) return false;
  return typeof value.cache.policy === 'string'
    && Array.isArray(value.cache.statuses)
    && value.cache.statuses.every((status) => typeof status === 'string')
    && typeof value.cache.external_attempted === 'boolean';
}
