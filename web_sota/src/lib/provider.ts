import { API_BASE } from "@/lib/api";

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ProviderModels {
  ollama: { name: string }[];
  lm_studio: { name: string }[];
}

/** LLM provider probe + chat calls (fleet standard lib/provider.ts). */
export async function listProviders(): Promise<ProviderModels> {
  const r = await fetch(`${API_BASE}/api/llm/providers`);
  if (!r.ok) throw new Error(`providers ${r.status}`);
  return r.json();
}

/** Send a chat turn, skill-first server side. Returns the reply text. */
export async function sendChat(
  message: string,
  systemPrompt: string,
  history: ChatMessage[],
): Promise<string> {
  const response = await fetch("/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      system_prompt: systemPrompt,
      context: { history },
    }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  return data.reply || data.response || "No response from model.";
}
