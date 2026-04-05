import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { fetchHealth } from "@/lib/api";

export function Status() {
    const [json, setJson] = useState<Record<string, unknown> | null>(null);
    const [err, setErr] = useState<string | null>(null);

    const load = useCallback(async () => {
        setErr(null);
        try {
            const h = await fetchHealth();
            setJson(h as unknown as Record<string, unknown>);
        } catch (e) {
            setJson(null);
            setErr(e instanceof Error ? e.message : "unreachable");
        }
    }, []);

    useEffect(() => {
        void load();
        const id = window.setInterval(() => void load(), 5000);
        return () => window.clearInterval(id);
    }, [load]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">System Status</h2>
                    <p className="text-slate-400">Data from <code className="text-slate-500">GET /api/health</code> only (this process).</p>
                </div>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                        {err ? (
                            <>
                                <AlertCircle className="h-5 w-5 text-red-400" />
                                Backend unreachable
                            </>
                        ) : (
                            <>
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                Health
                            </>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {err ? (
                        <p className="text-sm text-red-300">{err}</p>
                    ) : json ? (
                        <pre className="overflow-x-auto rounded-md border border-slate-800 bg-slate-900/50 p-4 font-mono text-xs text-slate-300">
                            {JSON.stringify(json, null, 2)}
                        </pre>
                    ) : (
                        <p className="text-slate-500">Loading…</p>
                    )}
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Not included</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-slate-400">
                    OS-level CPU, RAM, and latency are <strong className="text-slate-300">not</strong> collected here. Use Task Manager,
                    your host monitor, or extend the server with real probes if you need them.
                </CardContent>
            </Card>
        </div>
    );
}
