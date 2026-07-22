import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { API_BASE } from "../lib/api";
import { Music, Wand2, Loader2, Check, Sparkles } from "lucide-react";
import { postQuickGenerate } from "../lib/api";

const BACKENDS = [
  { id: "lyria", name: "Lyria 3 Pro", quality: "Best", icon: "✨" },
  { id: "stableaudio", name: "Stable Audio", quality: "Good", icon: "🎛️" },
  { id: "musicgen", name: "MusicGen", quality: "Fair", icon: "🎵" },
  { id: "studio", name: "Studio SG2", quality: "Variable", icon: "🎚️" },
];

export default function QuickGenerate() {
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(30);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{file: string; backend: string; model: string} | null>(null);
  const [error, setError] = useState("");
  const [activeBackend, setActiveBackend] = useState<string | null>(null);

  const generate = useCallback(async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await postQuickGenerate(prompt.trim(), duration);
      if (data.success) {
        setResult(data);
        setActiveBackend(data.backend);
      } else {
        setError(data.error || "Generation failed");
      }
    } catch (e: any) {
      setError(e.message || "Connection failed");
    }
    setLoading(false);
  }, [prompt, duration]);

  const loadToDeck = useCallback(async (deck: number) => {
    if (!result?.file) return;
    try {
      await fetch(`http://127.0.0.1:11116/api/v1/deck/${deck}/load`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_path: result.file }),
      });
    } catch {}
  }, [result]);

  return (
    <div className="space-y-6" data-testid="quick-generate">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            <Sparkles size={20} className="text-purple-400" />
            Quick Generate
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">Text prompt → AI music, any backend</p>
        </div>
        <div className="flex gap-2">
          {BACKENDS.map((b) => (
            <span key={b.id} className={`text-[10px] px-2 py-1 rounded-full ${
              activeBackend === b.id ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" : "bg-slate-800 text-slate-500"
            }`}>
              {b.icon} {b.name}
            </span>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && generate()}
            placeholder="128 BPM tech house drum loop with warm pads..."
            className="flex-1 px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 transition-colors"
            data-testid="prompt-input"
          />
          <button
            onClick={generate}
            disabled={loading || !prompt.trim()}
            className="px-6 py-3 rounded-xl bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            data-testid="generate-btn"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            Generate
          </button>
        </div>

        <div className="flex items-center gap-4 mt-4">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Duration:
            <input type="range" min={5} max={60} value={duration} onChange={(e) => setDuration(Number(e.target.value))}
              className="w-24 accent-purple-500" />
            <span className="font-mono text-slate-300 w-8">{duration}s</span>
          </label>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-800 bg-red-900/20 p-4">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {result && (
        <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}}
          className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Check size={16} className="text-emerald-400" />
              <div>
                <p className="text-sm text-slate-200">Generated</p>
                <p className="text-[10px] text-slate-500">via {result.backend} · {result.model}</p>
              </div>
            </div>
            <div className="flex gap-1">
              {[1, 2, 3, 4].map((d) => (
                <button key={d} onClick={() => loadToDeck(d)}
                  className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 text-xs font-mono transition-colors">
                  Load D{d}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
