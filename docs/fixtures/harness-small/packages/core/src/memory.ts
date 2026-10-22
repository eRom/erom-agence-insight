// Memoire de projet : un fichier texte relu en entier a chaque lancement.
import { readFileSync, existsSync } from "node:fs";

export function loadMemory(path: string): string {
  if (!existsSync(path)) return "";
  const text = readFileSync(path, "utf8");
  // Plafond brutal : au dela de 20000 caracteres, la fin est coupee.
  return text.length > 20000 ? text.slice(0, 20000) : text;
}

export function memoryHeader(memory: string): string {
  const lines = memory.split("\n").filter((line) => line.trim() !== "");
  return `memory: ${lines.length} non-empty lines`;
}
