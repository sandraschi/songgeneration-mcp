import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchSettings, postSettings } from "@/lib/api";
import { AlertCircle, CheckCircle2 } from "lucide-react";

function LLMSettings() {
    const [providers, setProviders] = useState<Record<string, {name:string}[]>>({});
    const [selectedProvider, setSelectedProvider] = useState("ollama");
    const [selectedModel, setSelectedModel] = useState("");
    const [status, setStatus] = useState<"loading"|"ready"|"error">("loading");
    useEffect(() => {
        fetch("/api/llm/providers").then(r => r.json()).then(d => {
            setProviders(d);
            const savedP = localStorage.getItem("llm_provider") || "ollama";
            const savedM = localStorage.getItem("llm_model") || "";
            setSelectedProvider(savedP);
            const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
            setSelectedModel(savedM && models.some((m:{name:string}) => m.name === savedM) ? savedM : (models[0]?.name || ""));
            setStatus(models.length > 0 ? "ready" : "error");
        }).catch(() => {
            setProviders({ ollama: [{name:"llama3.2:3b"}] });
            setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
            setStatus("ready");
        });
    }, []);
    const save = (p:string, m:string) => { localStorage.setItem("llm_provider", p); localStorage.setItem("llm_model", m); };
    const models = providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
    return (
        <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
                <CardTitle className="text-white">Local LLM</CardTitle>
                <CardDescription className="text-slate-400">Select provider and model for AI features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
                <select className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
                    value={selectedProvider} onChange={(e) => { setSelectedProvider(e.target.value); save(e.target.value, ""); }}>
                    <option value="ollama">Ollama</option>
                    <option value="lm_studio">LM Studio</option>
                </select>
                <select className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
                    value={selectedModel} onChange={(e) => { setSelectedModel(e.target.value); save(selectedProvider, e.target.value); }}>
                    {models.map((m) => <option key={m.name} value={m.name}>{m.name}</option>)}
                </select>
            </CardContent>
        </Card>
    );
}

export function Settings() {
    const [plexDir, setPlexDir] = useState("");
    const [virtualDjDir, setVirtualDjDir] = useState("");
    const [virtualDjApiBase, setVirtualDjApiBase] = useState("");
    const [virtualDjApiFromEnv, setVirtualDjApiFromEnv] = useState(false);
    const [reaperDir, setReaperDir] = useState("");
    const [reaperApiBase, setReaperApiBase] = useState("");
    const [reaperApiFromEnv, setReaperApiFromEnv] = useState(false);
    const [studioUrl, setStudioUrl] = useState("");
    const [studioDir, setStudioDir] = useState("");
    const [fromEnv, setFromEnv] = useState(false);
    const [studioFromEnv, setStudioFromEnv] = useState(false);
    const [studioDirFromEnv, setStudioDirFromEnv] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState<string | null>(null);
    const [err, setErr] = useState<string | null>(null);

    const load = useCallback(async () => {
        setErr(null);
        setLoading(true);
        try {
            const s = await fetchSettings();
            setPlexDir(s.plex_export_dir ?? "");
            setVirtualDjDir(s.virtualdj_drop_dir ?? "");
            setVirtualDjApiBase(s.virtualdj_api_base ?? "http://127.0.0.1:10877");
            setVirtualDjApiFromEnv(!!s.virtualdj_api_base_from_env);
            setReaperDir(s.reaper_drop_dir ?? "");
            setReaperApiBase(s.reaper_api_base ?? "http://127.0.0.1:10797");
            setReaperApiFromEnv(!!s.reaper_api_base_from_env);
            setFromEnv(!!s.plex_export_dir_from_env);
            setStudioUrl(s.studio_url ?? "");
            setStudioFromEnv(!!s.studio_url_from_env);
            setStudioDir(s.studio_dir ?? "");
            setStudioDirFromEnv(!!s.studio_dir_from_env);
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Failed to load settings");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
    }, [load]);

    const savePlex = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({ plex_export_dir: plexDir.trim() || null });
            setMsg("Saved.");
            await load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    const saveVirtualDj = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({
                virtualdj_drop_dir: virtualDjDir.trim() || null,
                virtualdj_api_base: virtualDjApiBase.trim() || null,
            });
            setMsg("Saved.");
            await load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    const saveReaper = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({
                reaper_drop_dir: reaperDir.trim() || null,
                reaper_api_base: reaperApiBase.trim() || null,
            });
            setMsg("Saved.");
            await load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    const saveStudio = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({
                studio_url: studioUrl.trim() || null,
                studio_dir: studioDir.trim() || null,
            });
            setMsg("Saved.");
            await load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Configuration</h2>
                <p className="text-slate-400">Paths and integrations for this machine</p>
            </div>

            {err ? (
                <div className="flex items-center gap-2 rounded-md border border-red-900/40 bg-red-950/20 px-3 py-2 text-sm text-red-200">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {err}
                </div>
            ) : null}
            {msg ? (
                <div className="flex items-center gap-2 rounded-md border border-emerald-900/40 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-200">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    {msg}
                </div>
            ) : null}

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Plex export</CardTitle>
                    <CardDescription className="text-slate-400">
                        Folder that maps to a Plex music library (or a subfolder you scan). Exports go to{" "}
                        <code className="text-slate-500">…/SongGeneration-MCP/</code> inside this path. Override with env{" "}
                        <code className="text-slate-500">SONGGEN_PLEX_EXPORT_DIR</code> (read-only in UI when set).
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {loading ? (
                        <p className="text-sm text-slate-500">Loading…</p>
                    ) : (
                        <>
                            <div className="grid gap-2">
                                <Label className="text-slate-300">Plex music library directory</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="e.g. D:\Media\Music\Plex or /volume1/music"
                                    value={plexDir}
                                    onChange={(e) => setPlexDir(e.target.value)}
                                    disabled={fromEnv}
                                />
                            </div>
                            {fromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">SONGGEN_PLEX_EXPORT_DIR</code> from the environment; clear it to edit here.
                                </p>
                            ) : null}
                            <Button
                                type="button"
                                variant="outline"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={saving || fromEnv}
                                onClick={() => void savePlex()}
                            >
                                {saving ? "Saving…" : "Save Plex path"}
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">VirtualDJ drop folder</CardTitle>
                    <CardDescription className="text-slate-400">
                        Path where tracks are copied before loading deck workflows. Use a local folder watched by VirtualDJ.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <Label className="text-slate-300">VirtualDJ drop directory</Label>
                        <Input
                            className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                            placeholder="e.g. D:\\Music\\VirtualDJ\\Drops"
                            value={virtualDjDir}
                            onChange={(e) => setVirtualDjDir(e.target.value)}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label className="text-slate-300">VirtualDJ API base</Label>
                        <Input
                            className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                            placeholder="http://127.0.0.1:10877"
                            value={virtualDjApiBase}
                            onChange={(e) => setVirtualDjApiBase(e.target.value)}
                            disabled={virtualDjApiFromEnv}
                        />
                    </div>
                    {virtualDjApiFromEnv ? (
                        <p className="text-xs text-amber-200/90">
                            Using <code className="text-slate-500">SONGGEN_VIRTUALDJ_API_BASE</code> from environment.
                        </p>
                    ) : null}
                    <Button
                        type="button"
                        variant="outline"
                        className="border-slate-800 text-slate-200 hover:bg-slate-800"
                        disabled={saving}
                        onClick={() => void saveVirtualDj()}
                    >
                        {saving ? "Saving…" : "Save VirtualDJ path"}
                    </Button>
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">SongGeneration-Studio</CardTitle>
                    <CardDescription className="text-slate-400">
                        Base URL for Studio API/UI link integration. Default is{" "}
                        <code className="text-slate-500">http://localhost:10930</code>.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {loading ? (
                        <p className="text-sm text-slate-500">Loading…</p>
                    ) : (
                        <>
                            <div className="grid gap-2">
                                <Label className="text-slate-300">Studio base URL</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="http://localhost:10930"
                                    value={studioUrl}
                                    onChange={(e) => setStudioUrl(e.target.value)}
                                    disabled={studioFromEnv}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label className="text-slate-300">Studio local directory</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="D:\\Dev\\repos\\external\\SongGeneration-Studio"
                                    value={studioDir}
                                    onChange={(e) => setStudioDir(e.target.value)}
                                    disabled={studioDirFromEnv}
                                />
                            </div>
                            {studioFromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">SONGGENERATION_STUDIO_URL</code> from the environment.
                                </p>
                            ) : null}
                            {studioDirFromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">SONGGEN_STUDIO_DIR</code> from the environment.
                                </p>
                            ) : null}
                            <Button
                                type="button"
                                variant="outline"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={saving || (studioFromEnv && studioDirFromEnv)}
                                onClick={() => void saveStudio()}
                            >
                                {saving ? "Saving…" : "Save Studio settings"}
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Reaper export</CardTitle>
                    <CardDescription className="text-slate-400">
                        Folder and API base used by song export to Reaper integration tests and workflows.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <Label className="text-slate-300">Reaper drop directory</Label>
                        <Input
                            className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                            placeholder="e.g. D:\\Audio\\Reaper\\Imports"
                            value={reaperDir}
                            onChange={(e) => setReaperDir(e.target.value)}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label className="text-slate-300">Reaper API base</Label>
                        <Input
                            className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                            placeholder="http://127.0.0.1:10797"
                            value={reaperApiBase}
                            onChange={(e) => setReaperApiBase(e.target.value)}
                            disabled={reaperApiFromEnv}
                        />
                    </div>
                    {reaperApiFromEnv ? (
                        <p className="text-xs text-amber-200/90">
                            Using <code className="text-slate-500">SONGGEN_REAPER_API_BASE</code> from environment.
                        </p>
                    ) : null}
                    <Button
                        type="button"
                        variant="outline"
                        className="border-slate-800 text-slate-200 hover:bg-slate-800"
                        disabled={saving}
                        onClick={() => void saveReaper()}
                    >
                        {saving ? "Saving…" : "Save Reaper settings"}
                    </Button>
                </CardContent>
            </Card>

            <LLMSettings />

            <Card className="border-slate-800 bg-slate-950/50 opacity-80">
                <CardHeader>
                    <CardTitle className="text-white">API bridge</CardTitle>
                    <CardDescription className="text-slate-400">This dashboard talks to the same origin as the page (Vite proxy in dev).</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-slate-500">No extra host field required when using <code className="text-slate-600">web_sota/start.ps1</code>.</p>
                </CardContent>
            </Card>
        </div>
    );
}
