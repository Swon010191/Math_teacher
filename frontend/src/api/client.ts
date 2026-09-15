/** Client gọi backend Math Engine (FastAPI). */

import type { CopilotSuggestion } from '../features/copilot/copilotTypes';
import type { ActivityModel, MathSolveResponse } from '../features/activities/activityTypes';
import type { KnowledgeRequest, KnowledgeResponse } from '../features/knowledge/knowledgeTypes';

export type { ActivityModel, MathSolveResponse } from '../features/activities/activityTypes';

const RAW_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';
// Chuẩn hóa base URL: bỏ khoảng trắng và dấu / cuối để tránh gọi nhầm
// (ví dụ "http://localhost:8000/" + "/api/..." thành "//api/...").
// Mặc định '' nghĩa là cùng gốc (bản đóng gói 1-port, không cần proxy Vite).
const BASE_URL = RAW_BASE_URL.trim().replace(/\/+$/, '');

async function request<T>(
  path: string,
  init?: RequestInit,
  timeoutMs = 20_000,
): Promise<T> {
  let response: Response;
  const { headers: initHeaders, signal: initSignal, ...restInit } = init ?? {};
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...restInit,
      headers: { 'Content-Type': 'application/json', ...(initHeaders as Record<string, string> | undefined) },
      signal: initSignal ?? AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    if (err instanceof DOMException && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
      throw new Error(
        'Xử lý AI quá lâu (quá thời gian chờ). Hãy thử lại hoặc kiểm tra tài nguyên máy.',
      );
    }
    throw new Error(
      'Không kết nối được máy chủ AI. Vui lòng khởi động backend: uvicorn app.main:app --port 8000',
    );
  }
  if (!response.ok) {
    let detail = `Lỗi ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* giữ nguyên thông báo mặc định */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export interface HealthInfo {
  connected: boolean;
  provider: string;
}

export interface ProviderState {
  provider: string;
  available: string[];
}

export async function checkHealth(timeoutMs = 5_000): Promise<HealthInfo> {
  try {
    const response = await fetch(`${BASE_URL}/health`, {
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) return { connected: false, provider: '' };
    const body = (await response.json()) as { recognition_provider?: string };
    return { connected: true, provider: body.recognition_provider ?? '' };
  } catch {
    return { connected: false, provider: '' };
  }
}

export async function getRecognitionProvider(): Promise<ProviderState> {
  return request<ProviderState>('/api/recognize/provider');
}

export interface ProviderStatus {
  provider: string;
  available: boolean;
  detail: string;
}

export async function getRecognitionProviderStatus(): Promise<ProviderStatus[]> {
  return request<ProviderStatus[]>('/api/recognize/providers/status');
}

export async function setRecognitionProvider(
  provider: string,
): Promise<ProviderState> {
  return request<ProviderState>('/api/recognize/provider', {
    method: 'PUT',
    body: JSON.stringify({ provider }),
  });
}

export interface QuadraticFeatures {
  a: number;
  b: number;
  c: number;
  discriminant: number;
  vertex: [number, number];
  axis: string;
  roots: number[];
  y_intercept: number;
  direction: 'up' | 'down';
  sample_points: number[][];
}

export interface RationalFeatures {
  a: number;
  b: number;
  c: number;
  d: number;
  poles: number[];
  vertical_asymptotes: string[];
  horizontal_asymptote: string | null;
  root: number | null;
  y_intercept: number | null;
  domain: string;
  sample_points: number[][];
}

export interface TrigFeatures {
  func: 'sin' | 'cos';
  a: number;
  b: number;
  c: number;
  d: number;
  amplitude: number;
  period: number;
  phase_shift: number;
  midline: number;
  max_value: number;
  min_value: number;
  roots: number[];
  sample_points: number[][];
}

export interface ExponentialFeatures {
  a: number;
  b: number;
  c: number;
  base: number;
  direction: 'up' | 'down';
  horizontal_asymptote: string;
  y_intercept: number;
  x_intercept: number | null;
  sample_points: number[][];
}

export interface LogarithmicFeatures {
  a: number;
  b: number;
  c: number;
  base: number;
  domain: string;
  vertical_asymptote: string;
  x_intercept: number;
  sample_points: number[][];
}

export interface MathAnalyzeResponse {
  expression: string;
  normalized_expression: string;
  kind:
    | 'quadratic'
    | 'linear'
    | 'rational'
    | 'trigonometric'
    | 'exponential'
    | 'logarithmic'
    | 'unknown';
  latex: string;
  canonical_expression?: string | null;
  source_variable: string;
  dependent_variable?: string | null;
  quadratic?: QuadraticFeatures;
  linear?: { a: number; b: number; root: number | null; y_intercept: number; sample_points: number[][] };
  rational?: RationalFeatures;
  trigonometric?: TrigFeatures;
  exponential?: ExponentialFeatures;
  logarithmic?: LogarithmicFeatures;
}

export interface RecognizeResult {
  latex: string;
  expression: string;
  confidence: number;
  provider: string;
  raw?: string | null;
}

export async function analyzeExpression(
  expression: string,
): Promise<MathAnalyzeResponse> {
  return request<MathAnalyzeResponse>('/api/math/analyze', {
    method: 'POST',
    body: JSON.stringify({ expression }),
  });
}

export async function createActivity(
  expression: string,
): Promise<ActivityModel> {
  return request<ActivityModel>('/api/math/activity', {
    method: 'POST',
    body: JSON.stringify({ expression }),
  });
}

export async function recognizeRegion(
  imageBase64: string | null,
  hint?: string,
  signal?: AbortSignal,
): Promise<RecognizeResult> {
  return request<RecognizeResult>(
    '/api/recognize',
    {
      method: 'POST',
      body: JSON.stringify({ image_base64: imageBase64, hint }),
      ...(signal ? { signal } : {}),
    },
    120_000,
  );
}

export async function suggestCopilot(
  activity: ActivityModel,
  gradeLevel = 'THCS',
  signal?: AbortSignal,
): Promise<CopilotSuggestion> {
  return request<CopilotSuggestion>(
    '/api/copilot/suggest',
    {
      method: 'POST',
      body: JSON.stringify({
        expression: activity.math.expression,
        activity_type: activity.type,
        math: activity.math,
        grade_level: gradeLevel,
      }),
      ...(signal ? { signal } : {}),
    },
    120_000,
  );
}

export interface CopilotProviderState {
  provider: string;
  available: string[];
}

export async function getCopilotProvider(): Promise<CopilotProviderState> {
  return request<CopilotProviderState>('/api/copilot/provider');
}

export async function setCopilotProvider(
  provider: string,
): Promise<CopilotProviderState> {
  return request<CopilotProviderState>('/api/copilot/provider', {
    method: 'PUT',
    body: JSON.stringify({ provider }),
  });
}

export async function solveEquation(
  expression: string,
  solveFor?: string,
): Promise<MathSolveResponse> {
  return request<MathSolveResponse>('/api/math/solve', {
    method: 'POST',
    body: JSON.stringify({ expression, ...(solveFor ? { solve_for: solveFor } : {}) }),
  });
}

export async function getRelatedKnowledge(
  expression: string,
  includeOriginal = true,
  includeVietnamese = true,
  signal?: AbortSignal,
): Promise<KnowledgeResponse> {
  const body: KnowledgeRequest = {
    expression,
    include_original: includeOriginal,
    include_vietnamese: includeVietnamese,
  };
  return request<KnowledgeResponse>('/api/knowledge/related', {
    method: 'POST',
    body: JSON.stringify(body),
    ...(signal ? { signal } : {}),
  });
}
