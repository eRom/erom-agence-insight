// Affichage du resultat : texte brut, sans couleur ni mise en forme.
export function render(result: string, verbose: boolean): string {
  if (!verbose) return result;
  return `--- result ---\n${result}\n--- end ---`;
}
