// Test du plafond de tours, le seul garde-fou de la boucle.
import { runLoop, type Model } from "../packages/core/src/loop";

const forever: Model = async () => ({ text: "again", calls: [{ name: "echo", input: "x" }] });

const out = await runLoop(forever, { echo: async (i) => i }, "task");
if (out !== "turn limit reached") throw new Error(`unexpected result: ${out}`);
console.log("ok");
