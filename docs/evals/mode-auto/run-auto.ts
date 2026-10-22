// Banc e2e du mode auto : lance un cas de cases.json dans un vrai `claude -p` et juge le resultat.
// Usage : bun docs/evals/mode-auto/run-auto.ts <caseId>
//         bun docs/evals/mode-auto/run-auto.ts --reparse <caseId>  (rejuge out/<caseId>.jsonl sans lancer claude)
//         bun docs/evals/mode-auto/run-auto.ts --selfcheck         (controle hors ligne de la fraicheur du rapport)
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

type Expect = { kind: "REPORT" | "ABORT" | "NONE"; reportPattern?: string; frontmatter?: string };
type Case = { id: string; prompt: string; expect: Expect; minAgentSpawns?: number };

const PLUGIN_DIR = "/Users/recarnot/dev/erom-agence-insight/plugin";
const PLUGIN_PREFIX = PLUGIN_DIR + "/";
const WORKER_CWD = "/Users/Shared/erom-agence-backlog-worker";
const CLAUDE_HOME = "/Users/recarnot/.claude";
const REPO_MEMORY = "/Users/recarnot/dev/erom-agence-insight/_memory_";
// Autres lieux de memoire durable surveilles : playbook et CLAUDE.md globaux, puis memoire du cwd du worker.
const GLOBAL_MEMORY_FILES = [`${CLAUDE_HOME}/erom-playbook.md`, `${CLAUDE_HOME}/CLAUDE.md`];
const WORKER_MEMORY_PATHS = [`${WORKER_CWD}/_memory_`, `${WORKER_CWD}/.claude`, `${WORKER_CWD}/CLAUDE.md`];
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

type StreamInfo = {
  finalResult: string | null;
  resultIsError: boolean;
  resultEvents: number;
  agentSpawns: number;
  forbiddenTools: string[];
  pluginEntryCounts: number[];
  skillBaseDir: string | null;
  pluginSource: string | null;
};

// Lecture du flux stream-json. Le dernier message `result` fait foi, quelle que soit sa forme :
// sans champ `result` de type string, finalResult reste null et le cas echoue.
function parseStream(raw: string, skillName: string | null): StreamInfo {
  const info: StreamInfo = {
    finalResult: null, resultIsError: false, resultEvents: 0, agentSpawns: 0,
    forbiddenTools: [], pluginEntryCounts: [], skillBaseDir: null, pluginSource: null,
  };
  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let msg: any;
    try { msg = JSON.parse(line); } catch { continue; }
    if (msg.type === "result") {
      info.resultEvents++;
      info.finalResult = typeof msg.result === "string" ? msg.result : null;
      info.resultIsError = msg.is_error === true;
    }
    // Le message init liste les plugins charges : c'est lui qui dit d'ou vient le plugin erom-insight.
    if (msg.type === "system" && msg.subtype === "init" && Array.isArray(msg.plugins)) {
      const entries = msg.plugins.filter((p: any) => p?.name === "erom-insight");
      info.pluginEntryCounts.push(entries.length);
      if (entries.length === 1) {
        const entry = entries[0];
        info.pluginSource = typeof entry.source === "string" ? entry.source : null;
        if (skillName && typeof entry.path === "string") info.skillBaseDir = `${entry.path}/skills/${skillName}`;
      }
    }
    const content = msg.message?.content;
    if (Array.isArray(content)) {
      for (const block of content) {
        if (block?.type !== "tool_use") continue;
        if (FORBIDDEN.has(block.name)) info.forbiddenTools.push(block.name);
        if (block.name === "Agent" || block.name === "Task") info.agentSpawns++;
      }
    }
  }
  return info;
}

// Derniere ligne non vide du resultat, ou null si le dernier `result` n'a pas de texte.
function lastNonEmptyLine(result: string | null): string | null {
  if (result === null) return null;
  return result.split("\n").map((l) => l.trimEnd()).filter((l) => l.trim() !== "").pop() ?? "";
}

// Controle hors ligne : fraicheur du rapport, puis lecture du flux (dernier result, plugin unique).
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
  const freshnessOk = !isFreshReport(stale, markerMs) && isFreshReport(fresh, markerMs);
  // Flux synthetique : deux `result`, le dernier sans texte, et deux entrees erom-insight dans init.
  const synthetic = [
    JSON.stringify({ type: "system", subtype: "init", plugins: [{ name: "erom-insight", path: "/a" }, { name: "erom-insight", path: "/b" }] }),
    JSON.stringify({ type: "assistant", message: { content: [{ type: "tool_use", name: "Agent" }] } }),
    JSON.stringify({ type: "result", result: "[REPORT] /x.md" }),
    JSON.stringify({ type: "result", subtype: "error_max_turns" }),
  ].join("\n");
  const s = parseStream(synthetic, "harness");
  const streamOk = s.resultEvents === 2 && s.finalResult === null && lastNonEmptyLine(s.finalResult) === null
    && s.agentSpawns === 1 && s.pluginEntryCounts[0] === 2 && s.skillBaseDir === null;
  const ok = freshnessOk && streamOk;
  console.log(JSON.stringify({ selfCheck: "report freshness and stream parsing", freshnessOk, streamOk, ok }, null, 2));
  process.exit(ok ? 0 : 1);
}

// `find` absolu (jamais l'alias de la session). Un chemin absent est ignore ; toute autre erreur est rendue, jamais avalee.
async function runFind(args: string[], errors: string[]): Promise<string[]> {
  const root = args[0];
  if (!fs.existsSync(root)) return [];
  const proc = Bun.spawn(["/usr/bin/find", ...args], { stdout: "pipe", stderr: "pipe" });
  const [text, errText] = await Promise.all([new Response(proc.stdout).text(), new Response(proc.stderr).text()]);
  const code = await proc.exited;
  if (code !== 0) errors.push(`find ${root} exited ${code}: ${errText.trim().split("\n")[0] ?? ""}`);
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
  const findErrors: string[] = [];
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
      ...(await runFind([CLAUDE_HOME, "-path", "*memory*", "-type", "f", "-newer", marker], findErrors)),
      ...(await runFind([REPO_MEMORY, "-newer", marker], findErrors)),
    ];
    for (const f of GLOBAL_MEMORY_FILES) memoryWrites.push(...(await runFind([f, "-type", "f", "-newer", marker], findErrors)));
    for (const d of WORKER_MEMORY_PATHS) memoryWrites.push(...(await runFind([d, "-type", "f", "-newer", marker], findErrors)));
    // Un meme fichier peut remonter par deux recherches : on ne le liste qu'une fois.
    memoryWrites = [...new Set(memoryWrites)];
  }

  // Nom de la skill visee par le prompt : /erom-insight:<skill>.
  const skillName = testCase.prompt.match(/\/erom-insight:([\w-]+)/)?.[1] ?? null;

  // Lecture du flux.
  const stream = parseStream(raw, skillName);
  const { finalResult, resultIsError, forbiddenTools, skillBaseDir, pluginSource } = stream;
  const lastLine = lastNonEmptyLine(finalResult);

  const reportMatch = lastLine === null ? null : lastLine.match(/^\[REPORT\] (.+)$/);
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
    if (lastLine === null || !/^\[ABORT\] .+/.test(lastLine)) why.push("last line is not [ABORT] <cause>");
  } else {
    if (lastLine === null || lastLine === "") why.push("empty last line");
    else if (/^\[(REPORT|ABORT)\]/.test(lastLine)) why.push("interactive case ended with an auto-mode prefix");
  }
  if (exp.kind !== "NONE") {
    if (forbiddenTools.length > 0) why.push(`forbidden tools used: ${forbiddenTools.join(", ")}`);
    if (memoryWrites && memoryWrites.length > 0) why.push("memoryWrites not empty (to be judged by hand)");
  }
  // Une erreur de find (hors chemin absent) rend memoryWrites incomplet : le cas echoue, y compris `interactive`.
  for (const e of findErrors) why.push(`memoryWrites scan failed: ${e}`);
  const pluginCounts = stream.pluginEntryCounts;
  if (pluginCounts.length === 0) why.push("erom-insight not loaded");
  else if (pluginCounts.some((n) => n !== 1)) why.push(`init.plugins must list erom-insight exactly once, got ${pluginCounts.join("/")}`);
  else if (skillBaseDir === null) why.push("skill name not found in the prompt");
  else if (!skillBaseDir.startsWith(PLUGIN_PREFIX)) why.push(`skillBaseDir outside the repo plugin: ${skillBaseDir}`);
  if (finalResult === null) why.push("no final result message with a text result in stream");
  // Informatif : un cas qui attend un swarm signale l'absence de spawn sans l'echouer.
  if (testCase.minAgentSpawns !== undefined && stream.agentSpawns < testCase.minAgentSpawns) {
    notes.push(`CONCERN agentSpawns ${stream.agentSpawns} < ${testCase.minAgentSpawns}: no swarm was launched`);
  }
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
    agentSpawns: stream.agentSpawns,
    resultEvents: stream.resultEvents,
    memoryWrites,
    skillBaseDir,
    pluginSource,
    stagedFixtures,
    pass: failures.length === 0,
    why: [...(failures.length === 0 ? ["ok"] : failures), ...notes].join("; "),
  };
  console.log(JSON.stringify(result, null, 2));
  // Code de sortie : 0 si le cas passe, 1 sinon.
  process.exit(result.pass ? 0 : 1);
}

await main();
