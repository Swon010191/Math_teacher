import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { KnowledgeActivity } from '../src/features/knowledge/KnowledgeActivity';
import type { KnowledgeResponse } from '../src/features/knowledge/knowledgeTypes';

const mocks = vi.hoisted(() => ({
  getRelatedKnowledge: vi.fn(),
  loadKnowledgeCache: vi.fn(),
  saveKnowledgeCache: vi.fn(),
}));

vi.mock('../src/api/client', () => ({ getRelatedKnowledge: mocks.getRelatedKnowledge }));
vi.mock('../src/features/knowledge/knowledgeCache', () => ({
  loadKnowledgeCache: mocks.loadKnowledgeCache,
  saveKnowledgeCache: mocks.saveKnowledgeCache,
}));

function knowledge(title: string, options?: { english?: boolean; translated?: boolean }): KnowledgeResponse {
  const english = options?.english ?? false;
  const translated = options?.translated ?? false;
  return {
    schema_version: '1.0',
    topic: 'linear_function',
    items: [{
      id: `item-${title}`,
      source_id: english ? 'mediawiki:en.wikipedia.org' : 'builtin:curated-vi',
      title,
      original_text: english ? 'Original English text' : 'Nội dung gốc',
      vietnamese_text: english ? (translated ? 'Nội dung dịch máy' : null) : 'Nội dung gốc',
      original_language: english ? 'en' : 'vi',
      translation_status: english ? (translated ? 'machine_translated' : 'unavailable') : 'original',
      citation_id: `citation-${title}`,
      cache_status: 'network',
    }],
    citations: [{
      id: `citation-${title}`,
      source_id: 'mediawiki:en.wikipedia.org',
      title,
      url: 'https://en.wikipedia.org/wiki/Linear_function',
      contributors_url: 'https://en.wikipedia.org/w/index.php?title=Linear_function&action=history',
      license_name: 'CC BY-SA 4.0',
      license_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
      revision: '123',
      retrieved_at: '2026-08-21T00:00:00Z',
    }],
    cache: { policy: 'bounded-memory-ttl-stale-if-error', statuses: ['network'], external_attempted: true },
    warning: 'Hãy đối chiếu nguồn trích dẫn.',
  };
}

describe('KnowledgeActivity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.saveKnowledgeCache.mockResolvedValue(undefined);
  });

  it('offers valid cached content first, then replaces and persists it with current data', async () => {
    let resolveRequest!: (value: KnowledgeResponse) => void;
    const request = new Promise<KnowledgeResponse>((resolve) => { resolveRequest = resolve; });
    mocks.loadKnowledgeCache.mockResolvedValue(knowledge('Bản đã lưu'));
    mocks.getRelatedKnowledge.mockReturnValue(request);

    render(<KnowledgeActivity expression="2*x+1" activityType="linear_function" />);

    expect(await screen.findByText('Bản đã lưu')).toBeInTheDocument();
    expect(screen.getByText('Bộ nhớ thiết bị')).toBeInTheDocument();
    resolveRequest(knowledge('Bản hiện tại', { english: true, translated: true }));

    expect(await screen.findByText('Bản hiện tại')).toBeInTheDocument();
    expect(screen.getByText('Nội dung dịch máy')).toBeInTheDocument();
    expect(screen.getByText('Dịch máy (machine translation)')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Nguồn đầy đủ/ })).toHaveAttribute('href', 'https://en.wikipedia.org/wiki/Linear_function');
    await waitFor(() => expect(mocks.saveKnowledgeCache).toHaveBeenCalledWith(
      'linear_function', '2*x+1', expect.objectContaining({ topic: 'linear_function' }),
    ));
  });

  it('keeps cache on request errors and falls back to original when translation is unavailable', async () => {
    mocks.loadKnowledgeCache.mockResolvedValue(knowledge('English source', { english: true }));
    mocks.getRelatedKnowledge.mockRejectedValue(new Error('offline'));

    render(<KnowledgeActivity expression="x+1" activityType="linear_function" />);

    expect(await screen.findByText('Original English text')).toBeInTheDocument();
    expect(screen.getByText(/translation unavailable/)).toBeInTheDocument();
    expect(await screen.findByText(/Đang hiển thị bản đã lưu/)).toBeInTheDocument();
    expect(screen.getByText('Hãy đối chiếu nguồn trích dẫn.')).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: 'Original' }));
    expect(screen.getByText('Original English text')).toBeInTheDocument();
  });
});
