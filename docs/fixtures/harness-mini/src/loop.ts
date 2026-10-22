// Boucle d'agent minimale, fournie comme fixture : elle n'est jamais executee.

type Message = { role: "user" | "assistant" | "tool"; content: string };

type Tool = { name: string; run: (input: string) => Promise<string> };

const MAX_TURNS = 20;

// Appel de modele simule : renvoie une reponse figee.
async function callModel(messages: Message[]): Promise<{ text: string; toolName?: string; toolInput?: string }> {
  const last = messages[messages.length - 1];
  return { text: `echo: ${last.content}` };
}

export async function runAgent(task: string, tools: Tool[]): Promise<string> {
  const messages: Message[] = [{ role: "user", content: task }];
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const reply = await callModel(messages);
    if (!reply.toolName) return reply.text;
    const tool = tools.find((t) => t.name === reply.toolName);
    const output = tool ? await tool.run(reply.toolInput ?? "") : "outil inconnu";
    messages.push({ role: "assistant", content: reply.text });
    messages.push({ role: "tool", content: output });
  }
  return "limite de tours atteinte";
}
