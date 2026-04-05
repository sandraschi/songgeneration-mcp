import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, BookOpen, Cpu, Link2 } from "lucide-react";
import { fetchStudioInfo } from "@/lib/api";

const ENV_ROWS: { key: string; hint: string }[] = [
  { key: "SONGGENERATION_STUDIO_URL", hint: "SongGeneration-Studio API base (default http://localhost:10930)." },
  { key: "SONGGEN_MODEL_REPO", hint: "Hugging Face repo, e.g. tencent/SongGeneration." },
  { key: "SONGGEN_MODEL_WEIGHTS", hint: "Variant id, e.g. v2-large." },
  { key: "SONGGEN_MAX_LENGTH_SECONDS", hint: "Cap generation length (default 270)." },
  { key: "SONGGEN_TORCH_DTYPE", hint: "e.g. bfloat16 for VRAM efficiency." },
  { key: "SONGGEN_GENERATE_TIMEOUT_S", hint: "HTTP timeout for /api/generate (long runs)." },
];

export function LocalLlm() {
  const [studioUiUrl, setStudioUiUrl] = useState<string>("");
  const [studioReachable, setStudioReachable] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    void fetchStudioInfo()
      .then((info) => {
        if (!mounted) return;
        setStudioUiUrl(info.ui_url);
        setStudioReachable(info.reachable);
      })
      .catch(() => {
        if (!mounted) return;
        setStudioUiUrl("");
        setStudioReachable(null);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Local LLM & inference</h2>
        <p className="text-slate-400">
          Song generation runs on <strong className="text-slate-200">your GPU</strong> via SongGeneration-Studio and
          open-weight checkpoints—not a hosted lyric-only API.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          {studioReachable === null ? (
            <span className="text-slate-500">Studio reachability unknown</span>
          ) : studioReachable ? (
            <span className="text-emerald-300">Studio reachable</span>
          ) : (
            <span className="text-amber-300">Studio unreachable</span>
          )}
          {studioUiUrl ? (
            <a
              href={studioUiUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-violet-300 hover:text-violet-200"
            >
              <Link2 className="h-3.5 w-3.5" />
              Open Studio UI
            </a>
          ) : null}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-emerald-400" />
              <CardTitle className="text-white">What runs locally</CardTitle>
            </div>
            <CardDescription className="text-slate-400">
              LeVo 2 / SG2 weights (e.g. <code className="text-emerald-300">v2-large</code>) and the music codec
              produce dual tracks (<code className="text-slate-300">vocal.wav</code>,{" "}
              <code className="text-slate-300">inst.wav</code>) at 48 kHz.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-300">
            <p>
              This dashboard talks to the MCP HTTP server on <Badge variant="outline" className="border-slate-600 text-slate-200">10885</Badge>{" "}
              (<code className="text-xs text-slate-400">/mcp</code>). Heavy inference is still in{" "}
              <strong>Studio</strong> on the port you configure—typically separate from the MCP port.
            </p>
            <p className="text-slate-400">
              Optional <strong className="text-slate-300">Ollama</strong> / OpenAI-compatible endpoints are for{" "}
              <em>agent sampling</em> or future features—not required for core song export.
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-violet-400" />
              <CardTitle className="text-white">Why local matters</CardTitle>
            </div>
            <CardDescription className="text-slate-400">
              Privacy, repertoire control, and classical/rubato-friendly iteration without per-song cloud metering.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-300 space-y-2">
            <p>
              Pair this with cloud tools (e.g. Gemini Lyria) when you want cheap demos—use SG2 when you need{" "}
              <strong>section-tagged</strong> structure and stems on disk.
            </p>
            <p className="text-slate-500 text-xs">
              See <span className="text-slate-400">Help → Compare</span> for a concise Lyria vs SG2 note.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Studio & MCP environment</CardTitle>
          <CardDescription className="text-slate-400">
            Set these where you launch the MCP server or Studio (see repo <code className="text-slate-300">docs/</code>).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border border-slate-800">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400">
                <tr>
                  <th className="px-3 py-2 font-medium">Variable</th>
                  <th className="px-3 py-2 font-medium">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {ENV_ROWS.map((row) => (
                  <tr key={row.key} className="hover:bg-slate-900/40">
                    <td className="px-3 py-2 font-mono text-xs text-emerald-300">{row.key}</td>
                    <td className="px-3 py-2 text-slate-400">{row.hint}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-blue-400" />
            <CardTitle className="text-white">Documentation</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3 text-sm">
          <a
            href="https://github.com/sandraschi/songgeneration-mcp"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-slate-200 hover:border-blue-500/50 hover:text-white"
          >
            <Link2 className="h-4 w-4" />
            GitHub README
          </a>
          <span className="self-center text-slate-500">Repo: docs/PRD.md, docs/LYRIA_VS_SG2.md</span>
        </CardContent>
      </Card>
    </div>
  );
}
