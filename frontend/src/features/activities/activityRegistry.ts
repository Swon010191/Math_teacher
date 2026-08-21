/** Registry activity: ánh xạ type -> widget component + nhãn tiếng Việt. */

import type { ComponentType } from 'react';

import type { ActivityModel } from './activityTypes';
import { ExponentialActivity } from './ExponentialActivity';
import { LinearActivity } from './LinearActivity';
import { LogarithmicActivity } from './LogarithmicActivity';
import { QuadraticActivity } from './QuadraticActivity';
import { RationalActivity } from './RationalActivity';
import { TrigActivity } from './TrigActivity';
import { SolutionActivity } from './SolutionActivity';

export const ACTIVITY_WIDGETS: Record<
  string,
  ComponentType<{ activity: ActivityModel }>
> = {
  quadratic_function: QuadraticActivity,
  linear_function: LinearActivity,
  rational_function: RationalActivity,
  trig_function: TrigActivity,
  exponential_function: ExponentialActivity,
  logarithmic_function: LogarithmicActivity,
  equation_solution: SolutionActivity,
};

export const ACTIVITY_KIND_LABELS: Record<string, string> = {
  quadratic: 'hàm bậc hai',
  linear: 'hàm bậc nhất',
  rational: 'hàm phân thức',
  trigonometric: 'hàm lượng giác',
  exponential: 'hàm mũ',
  logarithmic: 'hàm logarit',
};

export function activityWidgetFor(type: string) {
  return ACTIVITY_WIDGETS[type] ?? null;
}

export function activityKindLabel(kind: string): string {
  return ACTIVITY_KIND_LABELS[kind] ?? kind;
}
