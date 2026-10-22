// Boucle d'agent minimale : un modele, des outils, un plafond de tours.
export type ToolCall = { name: string; input: string };
export type Reply = { text: string; calls: ToolCall[] };
export type Model = (history: string[]) => Promise<Reply>;
export type Tool = (input: string) => Promise<string>;

const MAX_TURNS = 12;

export async function runLoop(
  model: Model,
  tools: Record<string, Tool>,
  task: string,
): Promise<string> {
  const history: string[] = [`user: ${task}`];
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const reply = await model(history);
    history.push(`assistant: ${reply.text}`);
    if (reply.calls.length === 0) return reply.text;
    for (const call of reply.calls) {
      const tool = tools[call.name];
      const output = tool ? await tool(call.input) : `unknown tool ${call.name}`;
      history.push(`tool(${call.name}): ${output}`);
    }
  }
  return "turn limit reached";
}
