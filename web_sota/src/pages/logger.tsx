import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Trash2, Download, RefreshCw } from "lucide-react";
import { clearLogs, fetchLogs, type ApiLogLine } from "@/lib/api";

export type LogLevel = "info" | "warn" | "error";

function mapLevel(s: string): LogLevel {
  const x = s.toLowerCase();
  if (x === "error" || x === "critical") return "error";
  if (x === "warning" || x === "warn") return "warn";
  return "info";
}

export function Logger() {
  const [lines, setLines] = useState<ApiLogLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | LogLevel>("all");
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await fetchLogs(800);
      setLines(data.lines);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load logs");
      setLines([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 4000);
    return () => window.clearInterval(id);
  }, [load]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const filtered = useMemo(() => {
    if (filter === "all") return lines;
    return lines.filter((l) => mapLevel(l.level) === filter);
  }, [lines, filter]);

  const onClear = async () => {
    try {
      await clearLogs();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clear failed");
    }
  };

  const download = () => {
    const t = lines.map((l) => `${l.ts} [${l.level}] ${l.logger} ${l.message}`).join("\n");
    const blob = new Blob([t], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `songgeneration-mcp-log-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const levelStyle = (level: string) => {
    const m = mapLevel(level);
    if (m === "error") return "text-red-400";
    if (m === "warn") return "text-amber-400";
    return "text-slate-300";
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Logger</h2>
          <p className="text-slate-400">
            Python <code className="text-slate-500">logging</code> ring buffer from the MCP HTTP process (
            <code className="text-slate-500">GET /api/logs</code>
            ). Start backend with <code className="text-slate-500">web_sota/start.ps1</code>.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as "all" | LogLevel)}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
          >
            <option value="all">All levels</option>
            <option value="info">info</option>
            <option value="warn">warn</option>
            <option value="error">error</option>
          </select>
          <Button variant="outline" size="sm" className="border-slate-700" onClick={() => void load()} disabled={loading}>
            <RefreshCw className={`mr-1 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" className="border-slate-700" onClick={download} disabled={!lines.length}>
            <Download className="mr-1 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" className="border-slate-700 text-red-300" onClick={() => void onClear()}>
            <Trash2 className="mr-1 h-4 w-4" />
            Clear buffer
          </Button>
        </div>
      </div>

      {error ? (
        <p className="rounded-md border border-red-900/50 bg-red-950/30 px-3 py-2 text-sm text-red-300">{error}</p>
      ) : null}

      <Card className="flex min-h-0 flex-1 flex-col border-slate-800 bg-slate-950/50">
        <CardHeader className="flex flex-row items-center justify-between py-3">
          <CardTitle className="text-base text-white">Process log</CardTitle>
          <Badge variant="outline" className="border-slate-600 font-mono text-slate-500">
            {filtered.length} lines
          </Badge>
        </CardHeader>
        <CardContent className="min-h-0 flex-1 px-2 pb-4">
          <ScrollArea className="h-[min(60vh,520px)] w-full rounded-md border border-slate-800 bg-slate-900/40 p-3 font-mono text-xs">
            <div className="space-y-1 pr-4">
              {loading && !lines.length ? (
                <p className="text-slate-500">Loading…</p>
              ) : !filtered.length ? (
                <p className="text-slate-500">No log lines yet (or buffer empty).</p>
              ) : (
                filtered.map((l, i) => (
                  <p key={`${l.ts}-${i}`} className={levelStyle(l.level)}>
                    <span className="text-slate-500">{l.ts}</span>{" "}
                    <span className="text-slate-600">[{l.level}]</span>{" "}
                    <span className="text-slate-500">{l.logger}</span> {l.message}
                  </p>
                ))
              )}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
