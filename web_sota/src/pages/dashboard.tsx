import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Activity,
    Shield,
    ScrollText,
    Brain,
    LifeBuoy,
    MessageSquare,
    AlertCircle,
    Music2,
} from "lucide-react";
import { fetchHealth, fetchLogs } from "@/lib/api";

export function Dashboard() {
    const [healthOk, setHealthOk] = useState<boolean | null>(null);
    const [healthDetail, setHealthDetail] = useState<string>("");
    const [logCount, setLogCount] = useState<number | null>(null);
    const [logPreview, setLogPreview] = useState<string[]>([]);
    const [err, setErr] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setErr(null);
        try {
            const h = await fetchHealth();
            setHealthOk(!!h.ok);
            setHealthDetail(`${h.service} ${h.version} · ${h.mcp_path}`);
        } catch {
            setHealthOk(false);
            setHealthDetail("");
            setErr("Cannot reach /api/health — start the backend (web_sota/start.ps1).");
        }
        try {
            const lg = await fetchLogs(12);
            setLogCount(lg.count);
            setLogPreview(lg.lines.slice(-6).map((l) => `${l.ts} [${l.level}] ${l.message}`));
        } catch {
            setLogCount(null);
            setLogPreview([]);
        }
    }, []);

    useEffect(() => {
        void refresh();
        const id = window.setInterval(() => void refresh(), 5000);
        return () => window.clearInterval(id);
    }, [refresh]);

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Songgeneration MCP Dashboard</h2>
                    <p className="text-slate-400">Live data from this repo’s HTTP process (no fake telemetry).</p>
                </div>
            </div>

            {err ? (
                <div className="flex items-center gap-2 rounded-md border border-amber-900/50 bg-amber-950/20 px-3 py-2 text-sm text-amber-200">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {err}
                </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
                <Link
                    to="/generate"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-violet-500/40 hover:text-white"
                >
                    <Music2 className="h-4 w-4 text-violet-400" />
                    Generate
                </Link>
                <Link
                    to="/local-llm"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-emerald-500/40 hover:text-white"
                >
                    <Brain className="h-4 w-4 text-emerald-400" />
                    Local LLM
                </Link>
                <Link
                    to="/chat"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-blue-500/40 hover:text-white"
                >
                    <MessageSquare className="h-4 w-4 text-blue-400" />
                    Chat
                </Link>
                <Link
                    to="/logger"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-amber-500/40 hover:text-white"
                >
                    <ScrollText className="h-4 w-4 text-amber-400" />
                    Logger
                </Link>
                <Link
                    to="/help"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-violet-500/40 hover:text-white"
                >
                    <LifeBuoy className="h-4 w-4 text-violet-400" />
                    Help
                </Link>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">HTTP API</CardTitle>
                        <Shield
                            className={`h-4 w-4 ${healthOk ? "text-emerald-500" : healthOk === false ? "text-red-400" : "text-slate-500"}`}
                        />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {healthOk === null ? "…" : healthOk ? "OK" : "Down"}
                        </div>
                        <p className="text-xs text-slate-400">{healthDetail || "GET /api/health"}</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Log buffer</CardTitle>
                        <Activity className="h-4 w-4 text-slate-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{logCount === null ? "…" : logCount}</div>
                        <p className="text-xs text-slate-400">Lines in process ring buffer (SONGGEN_LOG_BUFFER_LINES)</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Recent log lines</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[200px] space-y-1 overflow-y-auto rounded-md border border-slate-800 bg-slate-900/50 p-4 font-mono text-xs text-slate-400">
                            {logPreview.length === 0 ? (
                                <p className="text-slate-500">No lines yet or API unreachable.</p>
                            ) : (
                                logPreview.map((line, i) => <p key={i}>{line}</p>)
                            )}
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Scope</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-slate-400">
                            SongGeneration-Studio GPU inference is a <strong className="text-slate-300">separate</strong> process. This UI
                            reflects only the MCP HTTP server and Python <code className="text-slate-500">logging</code> buffer.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
