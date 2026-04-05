import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Book, Layers, Scale, Terminal, Boxes } from "lucide-react";

export function Help() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Help</h2>
        <p className="text-slate-400">
          Short overview below; use tabs for <strong className="text-slate-200">deep</strong> setup, SG2, and comparisons.
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Book className="h-5 w-5 text-emerald-400" />
            <CardTitle className="text-lg text-white">Quick start</CardTitle>
          </div>
          <CardDescription className="text-slate-400">
            Run <code className="text-slate-300">web_sota/start.ps1</code> — Vite on <strong>10884</strong>, MCP HTTP on{" "}
            <strong>10885</strong>. Point SongGeneration-Studio at your GPU; this UI does not replace Studio inference.
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="sg2" className="w-full">
        <TabsList className="flex h-auto w-full flex-wrap gap-1 bg-slate-900/80 p-1 ring-1 ring-slate-800">
          <TabsTrigger
            value="sg2"
            className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
          >
            <Layers className="mr-1 h-4 w-4" />
            SG2 & LeVo 2
          </TabsTrigger>
          <TabsTrigger
            value="compare"
            className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
          >
            <Scale className="mr-1 h-4 w-4" />
            vs Lyria 3 Pro
          </TabsTrigger>
          <TabsTrigger
            value="env"
            className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
          >
            <Terminal className="mr-1 h-4 w-4" />
            Environment
          </TabsTrigger>
          <TabsTrigger
            value="mcp"
            className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
          >
            <Boxes className="mr-1 h-4 w-4" />
            MCP resources
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sg2" className="mt-4 space-y-4 text-sm text-slate-300">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">Structural tags</CardTitle>
              <CardDescription className="text-slate-400">Length-sensitive markers inside lyrics (SongGeneration v2).</CardDescription>
            </CardHeader>
            <CardContent className="max-w-none space-y-3">
              <ul className="list-disc space-y-1 pl-5 text-slate-300">
                <li>
                  <code className="text-emerald-300">[intro-short]</code>, <code className="text-emerald-300">[intro-medium]</code>
                </li>
                <li>
                  <code className="text-emerald-300">[inst-short]</code>, <code className="text-emerald-300">[inst-medium]</code>
                </li>
                <li>
                  <code className="text-emerald-300">[outro-short]</code>, <code className="text-emerald-300">[outro-medium]</code>
                </li>
              </ul>
              <p>
                <strong className="text-white">English rule:</strong> lines should end with <code className="text-slate-200">.</code> before the
                section separator <code className="text-slate-200">;</code>. Example:{" "}
                <code className="text-xs text-slate-400">
                  [verse] The strings arise in the hall. ; [chorus]
                </code>
              </p>
              <p className="text-slate-500">
                Defaults: repo <code className="text-slate-400">tencent/SongGeneration</code>, weights{" "}
                <code className="text-slate-400">v2-large</code>, max length <strong>270s</strong>, dtype{" "}
                <code className="text-slate-400">bfloat16</code>, dual tracks <code className="text-slate-400">vocal.wav</code> /{" "}
                <code className="text-slate-400">inst.wav</code>.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compare" className="mt-4 space-y-4 text-sm text-slate-300">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">SG2 (local) vs Gemini Lyria 3 Pro (cloud)</CardTitle>
              <CardDescription className="text-slate-400">Creative fit—not a benchmark. Verify Google pricing in-app.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="overflow-x-auto rounded-md border border-slate-800">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-900/80 text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Topic</th>
                      <th className="px-3 py-2">LeVo 2 / SG2</th>
                      <th className="px-3 py-2">Lyria 3 Pro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    <tr>
                      <td className="px-3 py-2 font-medium text-slate-200">Deployment</td>
                      <td className="px-3 py-2">Self-hosted Studio + GPU</td>
                      <td className="px-3 py-2">Gemini / Google AI cloud</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-slate-200">Cost</td>
                      <td className="px-3 py-2">Hardware + power</td>
                      <td className="px-3 py-2">Often ~$0.08/song in typical credit tiers (verify)</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-slate-200">Strengths</td>
                      <td className="px-3 py-2">Classical, rubato, stems on disk</td>
                      <td className="px-3 py-2">Speed, Gemini integration, low $/track</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-500">
                Full write-up in repo: <code className="text-slate-400">docs/LYRIA_VS_SG2.md</code>. Many workflows use both.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="env" className="mt-4 space-y-4 text-sm text-slate-300">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">Common variables</CardTitle>
              <CardDescription className="text-slate-400">Studio + MCP (see also Local LLM page).</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 font-mono text-xs text-slate-400">
                <li>
                  <span className="text-emerald-300">SONGGENERATION_STUDIO_URL</span> — Studio API base
                </li>
                <li>
                  <span className="text-emerald-300">SONGGEN_MODEL_REPO</span> / <span className="text-emerald-300">SONGGEN_MODEL_WEIGHTS</span>
                </li>
                <li>
                  <span className="text-emerald-300">SONGGEN_MAX_LENGTH_SECONDS</span>,{" "}
                  <span className="text-emerald-300">SONGGEN_TORCH_DTYPE</span>,{" "}
                  <span className="text-emerald-300">SONGGEN_GENERATE_TIMEOUT_S</span>
                </li>
                <li>
                  <span className="text-emerald-300">MCP_PORT</span> / <span className="text-emerald-300">MCP_TRANSPORT</span> — MCP CLI (see
                  transport module)
                </li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mcp" className="mt-4 space-y-4 text-sm text-slate-300">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">Resources & tools</CardTitle>
              <CardDescription className="text-slate-400">Exposed by the MCP server (for capable clients).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p>
                <strong className="text-white">Tools:</strong> <code className="text-slate-400">generate_song</code>,{" "}
                <code className="text-slate-400">list_models</code>, <code className="text-slate-400">get_status</code>,{" "}
                <code className="text-slate-400">cancel_generation</code>, <code className="text-slate-400">unload_models</code>,{" "}
                <code className="text-slate-400">diagnostics</code>, <code className="text-slate-400">help</code> (try{" "}
                <code className="text-slate-400">topic=&quot;lyria&quot;</code>).
              </p>
              <p>
                <strong className="text-white">Resources:</strong> <code className="text-slate-400">api://song-request-schema</code>,{" "}
                <code className="text-slate-400">sg2://structural-tags</code>,{" "}
                <code className="text-slate-400">docs://lyria-vs-sg2</code>,{" "}
                <code className="text-slate-400">system://gpu-status</code>
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
