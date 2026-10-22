// Banc e2e du mode auto : lance un cas de cases.json dans un vrai `claude -p` et juge le resultat.
// Usage : bun docs/evals/mode-auto/run-auto.ts <caseId>
//         bun docs/evals/mode-auto/run-auto.ts --reparse <caseId>  (rejuge out/<caseId>.jsonl sans lancer claude)
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

type Expect = { kind: "REPORT" | "ABORT" | "NONE"; reportPattern?: string; frontmatter?: string };
type Case = { id: string; prompt: string; expect: Expect };

const PLUGIN_DIR = "/Users/recarnot/dev/erom-agence-insight/plugin";
const PLUGIN_PREFIX = PLUGIN_DIR + "/";
const WORKER_CWD = "/Users/Shared/erom-agence-backlog-worker";
const CLAUDE_HOME = "/Users/recarnot/.claude";
const REPO_MEMORY = "/Users/recarnot/dev/erom-agence-insight/_memory_";
const FORBIDDEN = new Set(["SendUserFile", "AskUserQuestion"]);
// Plafond de securite : un run peut depasser 20 minutes, jamais moins de 45.
const HARD_TIMEOUT_MS = 90 * 60 * 1000;

const here = import.meta.dir;
const fixturesSrc = path.resolve(here, "../../fixtures");
const outDir = path.join(here, "out");

function localDate(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

async function runFind(args: string[]): Promise<string[]> {
  const proc = Bun.spawn(["find", ...args], { stdout: "pipe", stderr: "ignore" });
  const text = await new Response(proc.stdout).text();
  await proc.exited;
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}

async function main() {
  const reparse = process.argv[2] === "--reparse";
  const caseId = reparse ? process.argv[3] : process.argv[2];
  const cases: Case[] = JSON.parse(fs.readFileSync(path.join(here, "cases.json"), "utf8"));
  const testCase = cases.find((c) => c.id === caseId);
  if (!testCase) {
    console.error(`Unknown case "${caseId}". Known: ${cases.map((c) => c.id).join(", ")}`);
    process.exit(2);
  }
  const jsonlPath = path.join(outDir, `${testCase.id}.jsonl`);

  let raw = "";
  let stagedFixtures: string | null = null;
  let memoryWrites: string[] | null = null;
  let exitCode: number | null = null;

  if (reparse) {
    // Relecture seule : aucun lancement de claude, memoryWrites non verifiable.
    raw = fs.readFileSync(jsonlPath, "utf8");
  } else {
    // Copie des fixtures hors de tout depot git, pour que la cible locale ne porte pas le remote du depot de travail.
    const tmpDir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "erom-insight-auto-")));
    stagedFixtures = path.join(tmpDir, "fixtures");
    fs.cpSync(fixturesSrc, stagedFixtures, { recursive: true });
    const prompt = testCase.prompt.split("{fixtures}").join(stagedFixtures);

    // Marqueur d'horodatage, cree juste avant le lancement.
    const marker = path.join(tmpDir, "marker");
    fs.writeFileSync(marker, "");

    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(jsonlPath, "");

    const proc = Bun.spawn(
      [
        "claude", "-p",
        "--plugin-dir", PLUGIN_DIR,
        "--model", "sonnet",
        "--effort", "high",
        "--permission-mode", "auto",
        "--permission-prompts", "none",
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
      ],
      { cwd: WORKER_CWD, stdin: "pipe", stdout: "pipe", stderr: "pipe" },
    );
    proc.stdin.write(prompt);
    proc.stdin.end();

    const killTimer = setTimeout(() => proc.kill(), HARD_TIMEOUT_MS);

    // Ecriture du flux brut au fil de l'eau.
    const decoder = new TextDecoder();
    for await (const chunk of proc.stdout) {
      const text = decoder.decode(chunk, { stream: true });
      raw += text;
      fs.appendFileSync(jsonlPath, text);
    }
    const stderrText = await new Response(proc.stderr).text();
    exitCode = await proc.exited;
    clearTimeout(killTimer);
    if (stderrText.trim()) console.error(`[claude stderr]\n${stderrText.trim()}`);

    // Ecritures de memoire depuis le marqueur : listees pour jugement manuel, jamais ignorees.
    memoryWrites = [
      ...(await runFind([CLAUDE_HOME, "-path", "*memory*", "-type", "f", "-newer", marker])),
      ...(await runFind([REPO_MEMORY, "-newer", marker])),
    ];
  }

  // Nom de la skill visee par le prompt : /erom-insight:<skill>.
  const skillName = testCase.prompt.match(/\/erom-insight:([\w-]+)/)?.[1] ?? null;

  // Lecture du flux.
  let finalResult: string | null = null;
  const forbiddenTools: string[] = [];
  let skillBaseDir: string | null = null;
  let pluginSource: string | null = null;
  let pluginLoaded = false;
  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let msg: any;
    try { msg = JSON.parse(line); } catch { continue; }
    if (msg.type === "result" && typeof msg.result === "string") finalResult = msg.result;
    // Le message init liste les plugins charges : c'est lui qui dit d'ou vient le plugin erom-insight.
    if (msg.type === "system" && msg.subtype === "init" && Array.isArray(msg.plugins)) {
      const entry = msg.plugins.find((p: any) => p?.name === "erom-insight");
      if (entry) {
        pluginLoaded = true;
        pluginSource = typeof entry.source === "string" ? entry.source : null;
        if (skillName && typeof entry.path === "string") skillBaseDir = `${entry.path}/skills/${skillName}`;
      }
    }
    const content = msg.message?.content;
    if (Array.isArray(content)) {
      for (const block of content) {
        if (block?.type === "tool_use" && FORBIDDEN.has(block.name)) forbiddenTools.push(block.name);
      }
    }
  }
  const lastLine = (finalResult ?? "").split("\n").map((l) => l.trimEnd()).filter((l) => l.trim() !== "").pop() ?? "";

  const reportMatch = lastLine.match(/^\[REPORT\] (.+)$/);
  const reportPath = reportMatch ? reportMatch[1].trim() : null;
  const reportExists = reportPath !== null && fs.existsSync(reportPath);

  // Jugement.
  const date = localDate();
  const why: string[] = [];
  const exp = testCase.expect;
  if (exp.kind === "REPORT") {
    if (reportPath === null) why.push("last line is not [REPORT] <path>");
    else {
      if (exp.reportPattern) {
        const re = new RegExp("^" + exp.reportPattern.split("{date}").join(date) + "$");
        if (!re.test(reportPath)) why.push(`report path does not match ${re}`);
      }
      if (!reportExists) why.push("report file does not exist");
      else if (exp.frontmatter && !fs.readFileSync(reportPath, "utf8").split("\n").some((l) => l.trim() === exp.frontmatter)) {
        why.push(`report lacks the line "${exp.frontmatter}"`);
      }
    }
  } else if (exp.kind === "ABORT") {
    if (!/^\[ABORT\] .+/.test(lastLine)) why.push("last line is not [ABORT] <cause>");
  } else {
    if (lastLine === "") why.push("empty last line");
    else if (/^\[(REPORT|ABORT)\]/.test(lastLine)) why.push("interactive case ended with an auto-mode prefix");
  }
  if (exp.kind !== "NONE") {
    if (forbiddenTools.length > 0) why.push(`forbidden tools used: ${forbiddenTools.join(", ")}`);
    if (memoryWrites && memoryWrites.length > 0) why.push("memoryWrites not empty (to be judged by hand)");
  }
  if (!pluginLoaded) why.push("erom-insight not loaded");
  else if (skillBaseDir === null) why.push("skill name not found in the prompt");
  else if (!skillBaseDir.startsWith(PLUGIN_PREFIX)) why.push(`skillBaseDir outside the repo plugin: ${skillBaseDir}`);
  if (finalResult === null) why.push(`no final result message in stream (claude exit code ${exitCode})`);
  // Une relecture ne peut pas verifier memoryWrites : elle ne passe jamais.
  if (reparse) why.push("reparse: memoryWrites not checked (null), no claude run");

  const result = {
    caseId: testCase.id,
    lastLine,
    reportPath,
    reportExists,
    forbiddenTools,
    memoryWrites,
    skillBaseDir,
    pluginSource,
    stagedFixtures,
    pass: why.length === 0,
    why: why.length === 0 ? "ok" : why.join("; "),
  };
  console.log(JSON.stringify(result, null, 2));
}

await main();
