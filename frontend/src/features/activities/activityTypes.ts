/** Activity Model - định dạng mở (schemaVersion 1.0). */

import type { CopilotSuggestion } from '../copilot/copilotTypes';

export interface SolveAnswer {
  exact: string;
  latex: string;
  approximate?: number | null;
  condition?: string | null;
}

export interface SolveStep {
  expression: string;
  explanation: string;
  latex?: string | null;
  metadata?: {
    kind: string;
    rule?: string | null;
    values?: Record<string, string>;
  } | null;
}

export interface SolveCase {
  condition: string;
  status: string;
  answers: SolveAnswer[];
}

export interface MathSolveResponse {
  original_equation: string;
  canonical_equation: string;
  variables: string[];
  solve_for: string;
  degree: number;
  classification: string;
  status: string;
  answers: SolveAnswer[];
  cases: SolveCase[];
  steps: SolveStep[];
  verified: boolean;
}

export interface ActivitySource {
  latex: string;
  confidence: number;
  confirmed: boolean;
}

export interface ActivityMath {
  expression: string;
  source_variable?: string;
  dependent_variable?: string | null;
  a?: number | null;
  b?: number | null;
  c?: number | null;
  d?: number | null;
  func?: 'sin' | 'cos' | null;
  base?: number | null;
  root?: number | null;
  vertex?: [number, number] | null;
  roots?: number[] | null;
  axis?: string | null;
  y_intercept?: number | null;
  discriminant?: number | null;
  direction?: 'up' | 'down' | null;
  amplitude?: number | null;
  period?: number | null;
  phase_shift?: number | null;
  midline?: number | null;
  max_value?: number | null;
  min_value?: number | null;
  asymptotes?: string[] | null;
  holes?: number[] | null;
  domain?: string | null;
}

export interface ActivityWidget {
  type: string;
  parameters?: string[];
}

export interface ActivityStep {
  visible: string[];
}

export interface ActivityModel {
  schemaVersion: string;
  type: string;
  source: ActivitySource;
  math: ActivityMath;
  widgets: ActivityWidget[];
  steps: ActivityStep[];
  solution?: MathSolveResponse | null;
  copilot?: CopilotSuggestion;
}
