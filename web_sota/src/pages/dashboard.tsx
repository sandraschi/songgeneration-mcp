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
    Headphones,
    Settings,
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
            <div className="space-y-3">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">SongGeneration MCP</h2>
                    <p className="mt-1 max-w-3xl text-base leading-relaxed text-slate-300">
                        <strong className="font-semibold text-white">What this is:</strong> a browser dashboard for the{" "}
                        <span className="text-slate-200">songgeneration-mcp</span> Python server. That server speaks{" "}
                        <abbr title="Model Context Protocol" className="cursor-help border-b border-dotted border-slate-500">
                            MCP
                        </abbr>{" "}
                        to tools like Claude and exposes REST endpoints this UI calls. Music is rendered by{" "}
                        <strong className="text-slate-200">SongGeneration-Studio</strong> (GPU, usually{" "}
                        <code className="text-slate-400">localhost:10930</code>) — not by this page alone.
                    </p>
                    <p className="mt-2 max-w-3xl text-sm text-slate-500">
                        The tiles below only reflect <strong className="text-slate-400">this API process</strong> (health + in-memory
                        logs). Use <strong className="text-slate-400">Generate</strong> to send jobs to Studio, <strong className="text-slate-400">Listen</strong> for playback,{" "}
                        <strong className="text-slate-400">Settings</strong> for URLs and export paths.
                    </p>
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
                    to="/listen"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-violet-500/40 hover:text-white"
                >
                    <Headphones className="h-4 w-4 text-violet-400" />
                    Listen
                </Link>
                <Link
                    to="/settings"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 hover:border-slate-600 hover:text-white"
                >
                    <Settings className="h-4 w-4 text-slate-400" />
                    Settings
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
                        <CardTitle className="text-sm font-medium text-slate-200">API server</CardTitle>
                        <Shield
                            className={`h-4 w-4 ${healthOk ? "text-emerald-500" : healthOk === false ? "text-red-400" : "text-slate-500"}`}
                        />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {healthOk === null ? "…" : healthOk ? "OK" : "Down"}
                        </div>
                        <p className="text-xs text-slate-400">
                            {healthDetail || "songgeneration-mcp (GET /api/health)"}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Server logs (buffer)</CardTitle>
                        <Activity className="h-4 w-4 text-slate-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{logCount === null ? "…" : logCount}</div>
                        <p className="text-xs text-slate-400">Recent lines kept in memory (env SONGGEN_LOG_BUFFER_LINES)</p>
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
                        <CardTitle className="text-white">What this page does not show</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="list-inside list-disc space-y-2 text-sm text-slate-400">
                            <li>
                                <strong className="text-slate-300">GPU / Studio</strong> — reachability is surfaced on{" "}
                                <Link to="/generate" className="text-violet-400 underline-offset-2 hover:underline">
                                    Generate
                                </Link>
                                ; set the Studio URL under{" "}
                                <Link to="/settings" className="text-violet-400 underline-offset-2 hover:underline">
                                    Settings
                                </Link>
                                .
                            </li>
                            <li>
                                <strong className="text-slate-300">These log lines</strong> — only this MCP process; Studio prints to its
                                own window unless you forward logs.
                            </li>
                        </ul>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
