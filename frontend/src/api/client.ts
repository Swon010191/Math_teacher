/** Client gọi backend Math Engine (FastAPI). */

import type { CopilotSuggestion } from '../features/copilot/copilotTypes';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(20_000),
      ...init,
    });
  } catch {
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

export async function checkHealth(): Promise<HealthInfo> {
  try {
    const response = await fetch(`${BASE_URL}/health`);
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

export interface MathAnalyzeResponse {
  expression: string;
  normalized_expression: string;
  kind: 'quadratic' | 'linear' | 'unknown';
  latex: string;
  quadratic?: QuadraticFeatures;
}

export interface RecognizeResult {
  latex: string;
  expression: string;
  confidence: number;
  provider: string;
  raw?: string | null;
}

export interface ActivityModel {
  schemaVersion: string;
  type: string;
  source: { latex: string; confidence: number; confirmed: boolean };
  math: {
    expression: string;
    a?: number | null;
    b?: number | null;
    c?: number | null;
    root?: number | null;
    vertex?: [number, number] | null;
    roots?: number[] | null;
    axis?: string | null;
    y_intercept?: number | null;
    discriminant?: number | null;
    direction?: 'up' | 'down' | null;
  };
  widgets: { type: string; parameters?: string[] }[];
  steps: { visible: string[] }[];
  copilot?: CopilotSuggestion;
}

export async function analyzeExpression(
  expression: string,
): Promise<MathAnalyzeResponse> {
  return request<MathAnalyzeResponse>('/api/math/analyze', {
    method: 'POST',
    body: JSON.stringify({ expression }),
  });
}

export async function createQuadraticActivity(
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
): Promise<RecognizeResult> {
  return request<RecognizeResult>('/api/recognize', {
    method: 'POST',
    body: JSON.stringify({ image_base64: imageBase64, hint }),
  });
}

export async function suggestCopilot(
  activity: ActivityModel,
  gradeLevel = 'THCS',
): Promise<CopilotSuggestion> {
  return request<CopilotSuggestion>('/api/copilot/suggest', {
    method: 'POST',
    body: JSON.stringify({
      expression: activity.math.expression,
      activity_type: activity.type,
      math: activity.math,
      grade_level: gradeLevel,
    }),
  });
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