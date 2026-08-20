/** Client gọi backend Math Engine (FastAPI). */

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

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
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
    vertex?: [number, number] | null;
    roots?: number[] | null;
    axis?: string | null;
    y_intercept?: number | null;
    discriminant?: number | null;
    direction?: 'up' | 'down' | null;
  };
  widgets: { type: string; parameters?: string[] }[];
  steps: { visible: string[] }[];
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