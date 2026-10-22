// Point d'entree : lit la tache, charge la memoire de projet, lance la boucle.
import { readFileSync } from "node:fs";
import { runLoop, type Model } from "../../core/src/loop";

const task = process.argv[2] ?? "";
const memory = readFileSync("AGENTS.md", "utf8");

// Modele factice : rend la tache et la memoire telles quelles, sans appel reseau.
const echoModel: Model = async () => ({
  text: `task: ${task} (memory: ${memory.length} chars)`,
  calls: [],
});

console.log(await runLoop(echoModel, {}, task));
