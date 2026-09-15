export type MathInputIntent = 'solve' | 'function';

export interface MathInputClassification {
  intent: MathInputIntent;
  variables: string[];
  sourceVariable: string | null;
  dependentVariable: string | null;
  isBareExpression: boolean;
  canonicalInput: string;
}

const RESERVED_NAMES = new Set([
  'abs', 'acos', 'asin', 'atan', 'ceil', 'cos', 'e', 'exp', 'floor', 'inf',
  'infinity', 'ln', 'log', 'max', 'min', 'oo', 'pi', 'sin', 'sqrt', 'tan',
]);

export function extractVariables(expression: string): string[] {
  const variables: string[] = [];
  const seen = new Set<string>();
  for (const match of expression.matchAll(/[A-Za-z][A-Za-z0-9_]*/g)) {
    const name = match[0];
    const rest = expression.slice((match.index ?? 0) + name.length);
    const isFunctionCall = /^\s*\(/.test(rest);
    if (RESERVED_NAMES.has(name.toLowerCase()) || isFunctionCall || seen.has(name)) continue;
    seen.add(name);
    variables.push(name);
  }
  return variables;
}

/** Classifies without evaluating input, so OCR and keyboard input behave identically. */
export function classifyMathInput(input: string): MathInputClassification {
  const expression = input.trim();
  // Toán tử so sánh (==, >=, <=, !=) luôn là phương trình cần giải,
  // không phải định nghĩa hàm.
  if (/(==|>=|<=|!=)/.test(expression)) {
    return {
      intent: 'solve',
      variables: extractVariables(expression),
      sourceVariable: null,
      dependentVariable: null,
      isBareExpression: false,
      canonicalInput: expression,
    };
  }
  const equality = expression.match(/^(.*?)=(.*)$/);
  if (!equality || /[<>!]\s*$/.test(equality[1]) || /^\s*=/.test(equality[2])) {
    const variables = extractVariables(expression);
    return {
      intent: 'function',
      variables,
      sourceVariable: variables[0] ?? null,
      dependentVariable: null,
      isBareExpression: true,
      canonicalInput: expression,
    };
  }

  const lhs = equality[1].trim();
  const rhs = equality[2].trim();
  const functionDefinition = lhs.match(/^([A-Za-z][A-Za-z0-9_]*)\s*\(\s*([A-Za-z][A-Za-z0-9_]*)\s*\)$/);
  const simpleDependent = lhs.match(/^([A-Za-z][A-Za-z0-9_]*)$/);
  const simpleDependentRight = rhs.match(/^([A-Za-z][A-Za-z0-9_]*)$/);
  const lhsVariables = extractVariables(lhs);
  const rhsVariables = extractVariables(rhs);

  if (functionDefinition && rhsVariables.length === 1) {
    return {
      intent: 'function',
      variables: rhsVariables,
      sourceVariable: functionDefinition[2],
      dependentVariable: functionDefinition[1],
      isBareExpression: false,
      canonicalInput: expression,
    };
  }

  if (simpleDependent && rhsVariables.length === 1 && rhsVariables[0] !== simpleDependent[1]) {
    return {
      intent: 'function',
      variables: rhsVariables,
      sourceVariable: rhsVariables[0],
      dependentVariable: simpleDependent[1],
      isBareExpression: false,
      canonicalInput: `${simpleDependent[1]}=${rhs}`,
    };
  }

  if (simpleDependentRight && lhsVariables.length === 1 && lhsVariables[0] !== simpleDependentRight[1]) {
    return {
      intent: 'function',
      variables: lhsVariables,
      sourceVariable: lhsVariables[0],
      dependentVariable: simpleDependentRight[1],
      isBareExpression: false,
      canonicalInput: `${simpleDependentRight[1]}=${lhs}`,
    };
  }

  return {
    intent: 'solve',
    variables: extractVariables(`${lhs} ${rhs}`),
    sourceVariable: null,
    dependentVariable: null,
    isBareExpression: false,
    canonicalInput: expression,
  };
}

export function normalizeMathInput(input: string, intent: MathInputIntent): string {
  const classification = classifyMathInput(input);
  return intent === 'function' ? classification.canonicalInput : input.trim();
}
