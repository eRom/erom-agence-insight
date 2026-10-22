// Budget de tours et de caracteres, verifie a chaque tour de la boucle.
export type Budget = { maxTurns: number; maxChars: number };

export const defaultBudget: Budget = { maxTurns: 12, maxChars: 50000 };

export function isExhausted(budget: Budget, turns: number, chars: number): boolean {
  return turns >= budget.maxTurns || chars >= budget.maxChars;
}

export function remaining(budget: Budget, turns: number, chars: number): string {
  return `${budget.maxTurns - turns} turns, ${budget.maxChars - chars} chars left`;
}
