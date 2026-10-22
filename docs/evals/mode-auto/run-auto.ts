// Banc e2e du mode auto : lance un cas de cases.json dans un vrai `claude -p` et juge le resultat.
// Usage : bun docs/evals/mode-auto/run-auto.ts <caseId>
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

// Parcourt recursivement un objet JSON et rend toutes les chaines rencontrees.
function collectStrings(value: unknown, acc: string[]): void {
  if (typeof value === "string") acc.push(value);
  else if (Array.isArray(value)) for (const v of value) collectStrings(v, acc);
  else if (value && typeof value === "object") for (const v of Object.values(value)) collectStrings(v, acc);
}

async function runFind(args: string[]): Promise<string[]> {
  const proc = Bun.spawn(["find", ...args], { stdout: "pipe", stderr: "ignore" });
  const text = await new Response(proc.stdout).text();
  await proc.exited;
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}

async function main() {
  const caseId = process.argv[2];
  const cases: Case[] = JSON.parse(fs.readFileSync(path.join(here, "cases.json"), "utf8"));
  const testCase = cases.find((c) => c.id === caseId);
  if (!testCase) {
    console.error(`Unknown case "${caseId}". Known: ${cases.map((c) => c.id).join(", ")}`);
    process.exit(2);
  }

  // Copie des fixtures hors de tout depot git, pour que la cible locale ne porte pas le remote du depot de travail.
  const tmpDir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "erom-insight-auto-")));
  const stagedFixtures = path.join(tmpDir, "fixtures");
  fs.cpSync(fixturesSrc, stagedFixtures, { recursive: true });

  const date = localDate();
  const prompt = testCase.prompt.split("{fixtures}").join(stagedFixtures);

  // Marqueur d'horodatage, cree juste avant le lancement.
  const marker = path.join(tmpDir, "marker");
  fs.writeFileSync(marker, "");

  fs.mkdirSync(outDir, { recursive: true });
  const jsonlPath = path.join(outDir, `${testCase.id}.jsonl`);
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
  let raw = "";
  const decoder = new TextDecoder();
  for await (const chunk of proc.stdout) {
    const text = decoder.decode(chunk, { stream: true });
    raw += text;
    fs.appendFileSync(jsonlPath, text);
  }
  const stderrText = await new Response(proc.stderr).text();
  const exitCode = await proc.exited;
  clearTimeout(killTimer);
  if (stderrText.trim()) console.error(`[claude stderr]\n${stderrText.trim()}`);

  // Lecture du flux.
  let finalResult: string | null = null;
  const forbiddenTools: string[] = [];
  let skillBaseDir: string | null = null;
  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let msg: any;
    try { msg = JSON.parse(line); } catch { continue; }
    if (msg.type === "result" && typeof msg.result === "string") finalResult = msg.result;
    const content = msg.message?.content;
    if (Array.isArray(content)) {
      for (const block of content) {
        if (block?.type === "tool_use" && FORBIDDEN.has(block.name)) forbiddenTools.push(block.name);
      }
    }
    if (skillBaseDir === null) {
      const strings: string[] = [];
      collectStrings(msg.message ?? msg, strings);
      for (const s of strings) {
        const m = s.match(/Base directory for this skill: ([^\n]+)/);
        if (m) { skillBaseDir = m[1].trim(); break; }
      }
    }
  }
  const lastLine = (finalResult ?? "").split("\n").map((l) => l.trimEnd()).filter((l) => l.trim() !== "").pop() ?? "";

  // Ecritures de memoire depuis le marqueur : listees pour jugement manuel, jamais ignorees.
  const memoryWrites = [
    ...(await runFind([CLAUDE_HOME, "-path", "*memory*", "-type", "f", "-newer", marker])),
    ...(await runFind([REPO_MEMORY, "-newer", marker])),
  ];

  const reportMatch = lastLine.match(/^\[REPORT\] (.+)$/);
  const reportPath = reportMatch ? reportMatch[1].trim() : null;
  const reportExists = reportPath !== null && fs.existsSync(reportPath);

  // Jugement.
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
    if (memoryWrites.length > 0) why.push("memoryWrites not empty (to be judged by hand)");
  }
  if (skillBaseDir === null) why.push("skillBaseDir not found in stream");
  else if (!skillBaseDir.startsWith(PLUGIN_PREFIX)) why.push(`skillBaseDir outside the repo plugin: ${skillBaseDir}`);
  if (finalResult === null) why.push(`no final result message in stream (claude exit code ${exitCode})`);

  const result = {
    caseId: testCase.id,
    lastLine,
    reportPath,
    reportExists,
    forbiddenTools,
    memoryWrites,
    skillBaseDir,
    stagedFixtures,
    pass: why.length === 0,
    why: why.length === 0 ? "ok" : why.join("; "),
  };
  console.log(JSON.stringify(result, null, 2));
}

await main();
