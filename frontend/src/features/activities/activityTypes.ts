/** Activity Model - định dạng mở (schemaVersion 1.0). */

import type { CopilotSuggestion } from '../copilot/copilotTypes';

export interface ActivitySource {
  latex: string;
  confidence: number;
  confirmed: boolean;
}

export interface ActivityMath {
  expression: string;
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
  copilot?: CopilotSuggestion;
}
