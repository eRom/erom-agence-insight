// Banc e2e du mode auto : lance un cas de cases.json dans un vrai `claude -p` et juge le resultat.
// Usage : bun docs/evals/mode-auto/run-auto.ts <caseId>
//         bun docs/evals/mode-auto/run-auto.ts --reparse <caseId>  (rejuge out/<caseId>.jsonl sans lancer claude)
//         bun docs/evals/mode-auto/run-auto.ts --selfcheck         (controle hors ligne de la fraicheur du rapport)
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

// Un rapport n'est produit par ce run que s'il a ete ecrit apres le marqueur de debut.
function isFreshReport(reportPath: string, markerMtimeMs: number): boolean {
  return fs.statSync(reportPath).mtimeMs >= markerMtimeMs;
}

// Controle hors ligne : un rapport anterieur au marqueur est rejete, un rapport posterieur est accepte.
function selfCheck(): void {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "erom-insight-selfcheck-"));
  const marker = path.join(dir, "marker");
  const stale = path.join(dir, "stale.md");
  const fresh = path.join(dir, "fresh.md");
  for (const f of [marker, stale, fresh]) fs.writeFileSync(f, "");
  const t = Date.now() / 1000;
  fs.utimesSync(stale, t - 120, t - 120);
  fs.utimesSync(marker, t - 60, t - 60);
  fs.utimesSync(fresh, t, t);
  const markerMs = fs.statSync(marker).mtimeMs;
  const ok = !isFreshReport(stale, markerMs) && isFreshReport(fresh, markerMs);
  console.log(JSON.stringify({ selfCheck: "report freshness", staleRejected: !isFreshReport(stale, markerMs), freshAccepted: isFreshReport(fresh, markerMs), ok }, null, 2));
  process.exit(ok ? 0 : 1);
}

async function runFind(args: string[]): Promise<string[]> {
  const proc = Bun.spawn(["find", ...args], { stdout: "pipe", stderr: "ignore" });
  const text = await new Response(proc.stdout).text();
  await proc.exited;
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}

async function main() {
  if (process.argv[2] === "--selfcheck") selfCheck();
  // Date du run, figee une fois avant tout lancement.
  const date = localDate();
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
  let markerMtimeMs: number | null = null;

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
    markerMtimeMs = fs.statSync(marker).mtimeMs;

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

    // stderr est vide en parallele du flux stdout, sinon un tube plein peut bloquer claude.
    const stderrPromise = new Response(proc.stderr).text();

    // Ecriture du flux brut au fil de l'eau.
    const decoder = new TextDecoder();
    for await (const chunk of proc.stdout) {
      const text = decoder.decode(chunk, { stream: true });
      raw += text;
      fs.appendFileSync(jsonlPath, text);
    }
    const stderrText = await stderrPromise;
    exitCode = await proc.exited;
    clearTimeout(killTimer);
    // stderr va dans son propre fichier, jamais sur la sortie du script (le .txt tee reste du JSON pur).
    fs.writeFileSync(path.join(outDir, `${testCase.id}.stderr.log`), stderrText);

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
  let resultIsError = false;
  const forbiddenTools: string[] = [];
  let skillBaseDir: string | null = null;
  let pluginSource: string | null = null;
  let pluginLoaded = false;
  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let msg: any;
    try { msg = JSON.parse(line); } catch { continue; }
    if (msg.type === "result" && typeof msg.result === "string") {
      finalResult = msg.result;
      resultIsError = msg.is_error === true;
    }
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
  const failures: string[] = [];
  const notes: string[] = [];
  const why = failures;
  const exp = testCase.expect;
  if (exp.kind === "REPORT") {
    if (reportPath === null) why.push("last line is not [REPORT] <path>");
    else {
      if (exp.reportPattern) {
        const re = new RegExp("^" + exp.reportPattern.split("{date}").join(date) + "$");
        if (!re.test(reportPath)) why.push(`report path does not match ${re}`);
      }
      if (!reportExists) why.push("report file does not exist");
      else if (markerMtimeMs !== null && !isFreshReport(reportPath, markerMtimeMs)) why.push("report not written by this run");
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
  if (finalResult === null) why.push("no final result message in stream");
  // Un code de sortie non nul ou un resultat is_error echoue le cas, sauf pour `interactive` qui garde sa propre regle.
  const exitFailed = (exitCode !== null && exitCode !== 0) || resultIsError;
  const exitNote = `claude exit code ${exitCode ?? "unknown"}${resultIsError ? ", result is_error" : ""}`;
  if (exitFailed && exp.kind !== "NONE") failures.push(exitNote);
  else if (exitCode !== null || exitFailed) notes.push(exitNote);
  // Une relecture ne peut pas verifier memoryWrites ni la fraicheur du rapport : elle ne passe jamais.
  if (reparse) failures.push("reparse: memoryWrites and report freshness not checked, no claude run");

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
    pass: failures.length === 0,
    why: [...(failures.length === 0 ? ["ok"] : failures), ...notes].join("; "),
  };
  console.log(JSON.stringify(result, null, 2));
}

await main();
