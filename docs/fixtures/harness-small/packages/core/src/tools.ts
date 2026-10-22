// Registre d'outils : un outil est une fonction texte vers texte.
import type { Tool } from "./loop";

export const builtinTools: Record<string, Tool> = {
  // Rend l'entree telle quelle, utile pour tester la boucle sans effet de bord.
  echo: async (input) => input,
  // Rend la longueur de l'entree en caracteres.
  length: async (input) => String(input.length),
  // Rend l'entree en majuscules.
  upper: async (input) => input.toUpperCase(),
};

export function mergeTools(...sets: Record<string, Tool>[]): Record<string, Tool> {
  // En cas de collision de noms, le dernier registre gagne.
  return Object.assign({}, ...sets);
}

export function describeTools(tools: Record<string, Tool>): string {
  return Object.keys(tools)
    .sort()
    .map((name) => `- ${name}`)
    .join("\n");
}
