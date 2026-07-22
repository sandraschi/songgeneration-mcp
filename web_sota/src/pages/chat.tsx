import { Bot, Download, Loader2, Send, Sparkles, Trash2, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const STORAGE_KEY = "songgeneration-mcp-chat-history";

const PERSONALITIES: Record<string, string> = {
  "Music Producer": "You are an experienced music producer specializing in AI-assisted music generation. Help users craft prompts for song generation, arrange tracks, and refine outputs. Be creative and technically knowledgeable about music theory.",
  "Lyricist": "You are a skilled lyricist and songwriter. Help users write compelling lyrics, structure songs, and match words to melodies. Focus on rhyme schemes, meter, and emotional impact.",
  "Quick Summarizer": "You are a concise assistant. Answer in 1-3 sentences. Be direct and to the point.",
  "Custom": "",
};

const EXAMPLE_PROMPTS = [
  { group: "Songs", items: ["Generate a synthwave track with 80s vibes", "Create a lo-fi hip hop beat with piano melody", "Produce an ambient soundscape for meditation"] },
  { group: "Style", items: ["Describe a track in the style of orchestral film score", "Generate lyrics for a pop chorus about summer", "Create a jazz-influenced instrumental piece"] },
  { group: "Production", items: ["Suggest mastering chain for electronic music", "Structure an EDM track with build-ups and drops", "Balance mix levels for vocals and instruments"] },
];

function saveMessages(msgs: Message[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs)); } catch {}
}

function loadMessages(): Message[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return [];
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = loadMessages();
    if (saved.length > 0) return saved;
    return [{
      role: "assistant",
      content: "I'm your Song Generation MCP assistant. I can help you generate music, write lyrics, and refine your creative vision. What kind of song would you like to create?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }];
  });
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [personality, setPersonality] = useState("Music Producer");
  const [showExamples, setShowExamples] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;
    setShowExamples(false);

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const updated = [...messages, userMsg];
    setMessages(updated);
    saveMessages(updated);
    setInputValue("");
    setIsLoading(true);

    try {
      const history = updated.map((m) => ({ role: m.role, content: m.content }));
      const systemPrompt = PERSONALITIES[personality] || "";
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, system_prompt: systemPrompt, context: { history } }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const reply = data.reply || data.response || "No response from model.";

      const assistantMsg: Message = {
        role: "assistant",
        content: reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      const withReply = [...updated, assistantMsg];
      setMessages(withReply);
      saveMessages(withReply);
    } catch {
      const errMsg: Message = {
        role: "assistant",
        content: "Request failed. Check that the backend is running and an LLM provider (Ollama/LM Studio) is configured.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      const withError = [...updated, errMsg];
      setMessages(withError);
      saveMessages(withError);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [messages, isLoading, personality, inputValue]);

  const handleClear = () => {
    const fresh: Message[] = [{
      role: "assistant",
      content: "Conversation cleared. Ready to make new music.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }];
    setMessages(fresh);
    saveMessages(fresh);
  };

  const handleExport = () => {
    const text = messages.map((m) => `[${m.timestamp}] ${m.role === "user" ? "You" : "Assistant"}: ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `songgeneration-mcp-chat-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col space-y-4 animate-in fade-in duration-500 h-full" data-testid="chat-page">
      <div className="flex items-center justify-between shrink-0" data-testid="chat-controls">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-pink-400" />
            <h2 className="text-2xl font-bold tracking-tight text-white">Chat</h2>
          </div>
          <span className="text-xs text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded font-mono">skill:music-producer</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" data-testid="backend-dot" />
          <button type="button" onClick={handleExport} data-testid="chat-export"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 transition-colors">
            <Download className="h-3.5 w-3.5" /> Export
          </button>
          <button type="button" onClick={handleClear} data-testid="chat-clear"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 transition-colors">
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap shrink-0" data-testid="personality-select">
        <span className="text-xs text-slate-500">Personality:</span>
        {Object.keys(PERSONALITIES).map((p) => (
          <button key={p} type="button" onClick={() => setPersonality(p)}
            className={`px-2.5 py-1 rounded text-[10px] font-medium transition-all ${
              personality === p
                ? "bg-pink-500/20 text-pink-400 border border-pink-500/30"
                : "bg-slate-800/30 text-slate-400 border border-slate-700/40 hover:bg-slate-700/50"
            }`}>
            {p}
          </button>
        ))}
      </div>

      <div className="flex-1 flex flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-950/20">
        <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className="flex gap-3 animate-in slide-in-from-bottom-2 duration-300">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${
                msg.role === "user" ? "bg-slate-800 border-slate-700/50" : "bg-pink-500/10 border-pink-500/20"
              }`}>
                {msg.role === "user" ? <User className="h-4 w-4 text-slate-400" /> : <Bot className="h-4 w-4 text-pink-400" />}
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${msg.role === "user" ? "text-white" : "text-pink-400"}`}>
                    {msg.role === "user" ? "You" : personality}
                  </span>
                  <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
                </div>
                <div className={`text-sm p-3 rounded-lg border inline-block max-w-[85%] whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-slate-800/30 border-slate-700/30 text-slate-100"
                    : "bg-pink-500/5 border-pink-500/10 text-slate-100"
                }`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 animate-pulse">
              <div className="h-8 w-8 rounded-full bg-pink-500/10 flex items-center justify-center border border-pink-500/20 shrink-0">
                <Loader2 className="h-4 w-4 text-pink-400 animate-spin" />
              </div>
              <div className="bg-pink-500/5 border border-pink-500/10 p-3 rounded-lg h-10 w-48">
                <div className="h-2 w-full bg-pink-500/20 rounded animate-pulse" />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="p-4 border-t border-slate-700/30 bg-slate-800/10 shrink-0">
          {!showExamples && (
            <div className="mb-2 flex items-center gap-1.5 flex-wrap" data-testid="example-prompts">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group} className="flex items-center gap-1">
                  <span className="text-[10px] text-slate-500 mr-1">{group.group}:</span>
                  {group.items.map((p) => (
                    <button key={p} type="button" onClick={() => { setInputValue(p); inputRef.current?.focus(); }}
                      className="px-2 py-0.5 rounded text-[10px] bg-slate-800/30 text-slate-400 hover:bg-slate-700/50 transition-colors border border-slate-700/30">
                      {p}
                    </button>
                  ))}
                </div>
              ))}
              <button type="button" onClick={() => setShowExamples(true)}
                className="px-2 py-0.5 rounded text-[10px] text-pink-400 hover:text-pink-300 transition-colors">
                Show all
              </button>
            </div>
          )}
          {showExamples && (
            <div className="mb-2 flex flex-wrap gap-1.5" data-testid="example-prompts">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group} className="flex flex-wrap items-center gap-1">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">{group.group}:</span>
                  {group.items.map((p) => (
                    <button key={p} type="button" onClick={() => { setInputValue(p); setShowExamples(false); inputRef.current?.focus(); }}
                      className="px-2 py-0.5 rounded text-[10px] bg-slate-800/30 text-slate-400 hover:bg-slate-700/50 transition-colors border border-slate-700/30">
                      {p}
                    </button>
                  ))}
                </div>
              ))}
              <button type="button" onClick={() => setShowExamples(false)}
                className="px-2 py-0.5 rounded text-[10px] text-pink-400 hover:text-pink-300 transition-colors">
                Less
              </button>
            </div>
          )}
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-3">
            <input ref={inputRef}
              className="flex-1 bg-black/20 border border-slate-700/50 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-pink-500/50 placeholder:text-slate-600/50 transition-all"
              placeholder="Ask about music generation..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
              data-testid="chat-input"
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()} data-testid="chat-send"
              className="p-2.5 rounded-lg bg-pink-500 hover:bg-pink-600 text-white shadow-lg shadow-pink-500/20 shrink-0 disabled:opacity-50 transition-all">
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
