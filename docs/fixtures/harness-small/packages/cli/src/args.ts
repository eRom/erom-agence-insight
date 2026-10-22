// Lecture des arguments de la ligne de commande, sans bibliotheque.
export type Args = { task: string; verbose: boolean };

export function parseArgs(argv: string[]): Args {
  const flags = argv.filter((a) => a.startsWith("--"));
  const rest = argv.filter((a) => !a.startsWith("--"));
  return { task: rest.join(" "), verbose: flags.includes("--verbose") };
}

export function usage(): string {
  return "usage: agentlet [--verbose] <task>";
}
