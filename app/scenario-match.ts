/** Offline demos only replay a single, explicitly supported entity or exact sample question. */
export function matchScenario<T extends { claim: string; question: string }>(input: string, scenarios: T[]): T | undefined {
  const text = input.trim();
  const entities = [...new Set(text.toUpperCase().match(/(?<![A-Z0-9_])(?:CLM-[A-Z0-9-]*|U\d+[A-Z0-9-]*|INC-[A-Z0-9-]*)(?![A-Z0-9_])/g) ?? [])];
  if (entities.length) return entities.length === 1 ? scenarios.find((scenario) => scenario.claim === entities[0]) : undefined;
  return scenarios.find((scenario) => scenario.question === text);
}
