import katex from 'katex';

import type { ActivityModel, SolveAnswer, SolveStep } from './activityTypes';

const STEP_LABELS: Record<string, string> = {
  original_equation: 'Đề bài',
  standard_form: 'Đưa về dạng chuẩn',
  coefficient_identification: 'Xác định hệ số',
  isolate_variable_term: 'Cô lập hạng tử chứa ẩn',
  divide_coefficient: 'Chia hai vế',
  discriminant: 'Tính biệt thức',
  case_analysis: 'Xét trường hợp',
  quadratic_formula: 'Áp dụng công thức nghiệm',
  exact_answers: 'Kết luận nghiệm',
  verification: 'Kiểm tra nghiệm',
};

function MathText({ value }: { value: string }) {
  let html: string;
  try {
    html = katex.renderToString(value, { throwOnError: false });
  } catch {
    return <code>{value}</code>;
  }
  return <span className="solution-math" dangerouslySetInnerHTML={{ __html: html }} />;
}

function Answers({ answers, solveFor }: { answers: SolveAnswer[]; solveFor: string }) {
  if (answers.length === 0) return <p className="solution-empty">Không có nghiệm được liệt kê.</p>;
  return (
    <ul className="solution-answers">
      {answers.map((answer, index) => (
        <li key={`${answer.exact}-${index}`}>
          <MathText value={`${solveFor} = ${answer.latex || answer.exact}`} />
          {answer.approximate != null && <span> ≈ {answer.approximate}</span>}
          {answer.condition && <span className="solution-condition">Điều kiện: {answer.condition}</span>}
        </li>
      ))}
    </ul>
  );
}

function statusLabel(status: string): string {
  return {
    solved: 'Đã giải',
    conditional: 'Phụ thuộc điều kiện',
    no_solution: 'Vô nghiệm',
    infinite_solutions: 'Vô số nghiệm',
  }[status] ?? status;
}

function StepItem({ step, index }: { step: SolveStep; index: number }) {
  const kind = step.metadata?.kind;
  const label = kind ? STEP_LABELS[kind] : undefined;
  return (
    <li className={kind ? `solution-step kind-${kind}` : 'solution-step'}>
      <div className="solution-step-heading">
        <span className="solution-step-number">Bước {index + 1}</span>
        {label && <strong>{label}</strong>}
        {kind === 'verification' && <span className="solution-step-verified">Đã đối chiếu</span>}
      </div>
      <div className="solution-step-formula"><MathText value={step.latex || step.expression} /></div>
      <p>{step.explanation}</p>
    </li>
  );
}

export function SolutionActivity({
  activity,
  collapsible = false,
  embedded = false,
}: {
  activity: ActivityModel;
  collapsible?: boolean;
  embedded?: boolean;
}) {
  const solution = activity.solution;
  if (!solution) return null;

  const content = (
    <div className="solution-body">
      <div className="solution-equation">
        <MathText value={solution.canonical_equation} />
      </div>
      <p className="solution-status">
        Trạng thái: <strong>{statusLabel(solution.status)}</strong>
        <span className={solution.verified ? 'verified' : 'unverified'}>
          <span aria-hidden="true">{solution.verified ? '✓ ' : '⚠ '}</span>
          {solution.verified ? 'Đã kiểm chứng' : 'Chưa kiểm chứng'}
        </span>
      </p>
      <Answers answers={solution.answers} solveFor={solution.solve_for} />
      {solution.cases.map((item, index) => (
        <section className="solution-case" key={`${item.condition}-${index}`}>
          <h4>Trường hợp: {item.condition}</h4>
          <p>{statusLabel(item.status)}</p>
          <Answers answers={item.answers} solveFor={solution.solve_for} />
        </section>
      ))}
      {solution.steps.length > 0 && (
        <ol className="solution-steps">
          {solution.steps.map((step, index) => (
            <StepItem key={`${step.expression}-${index}`} step={step} index={index} />
          ))}
        </ol>
      )}
    </div>
  );

  if (embedded) return <div className="solution-activity embedded" data-testid="solution-activity">{content}</div>;

  return (
    <details
      className="solution-activity"
      data-testid="solution-activity"
      open={!collapsible}
    >
      <summary>Đáp án &amp; lời giải</summary>
      {content}
    </details>
  );
}
