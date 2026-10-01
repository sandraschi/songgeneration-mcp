import { create } from "zustand";
import { listProviders, type ProviderModels } from "@/lib/provider";

export type LlmStatus = "loading" | "ready" | "error";

interface LlmState {
  providers: ProviderModels;
  selectedProvider: string;
  selectedModel: string;
  status: LlmStatus;
  refresh: () => Promise<void>;
  select: (provider: string, model: string) => void;
}

function pickModel(
  providers: ProviderModels,
  provider: string,
  saved: string,
): string {
  const models =
    providers[provider === "ollama" ? "ollama" : "lm_studio"] || [];
  return saved && models.some((m) => m.name === saved)
    ? saved
    : models[0]?.name || "";
}

/** Fleet standard store/llm.ts: local LLM provider state, shared across pages. */
export const useLlmStore = create<LlmState>((set) => ({
  providers: { ollama: [], lm_studio: [] },
  selectedProvider:
    typeof localStorage !== "undefined"
      ? localStorage.getItem("llm_provider") || "ollama"
      : "ollama",
  selectedModel: "",
  status: "loading",
  refresh: async () => {
    try {
      const d = await listProviders();
      const savedP = localStorage.getItem("llm_provider") || "ollama";
      const savedM = localStorage.getItem("llm_model") || "";
      set({
        providers: d,
        selectedProvider: savedP,
        selectedModel: pickModel(d, savedP, savedM),
        status: "ready",
      });
    } catch {
      // Backend unreachable: honest empty state, never fake models.
      set({
        providers: { ollama: [], lm_studio: [] },
        selectedModel: "",
        status: "error",
      });
    }
  },
  select: (provider, model) => {
    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("llm_model", model);
    set({ selectedProvider: provider, selectedModel: model });
  },
}));
