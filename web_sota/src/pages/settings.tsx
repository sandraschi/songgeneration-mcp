import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    API_BASE,
    fetchSettings,
    postSettings,
    fetchLyriaStatus,
    type LyriaStatus,
    fetchHuggingFaceStatus,
    type HuggingFaceStatus,
} from "@/lib/api";
import { AlertCircle, CheckCircle2, Circle, Copy, Check, RefreshCw } from "lucide-react";

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    return (
        <button
            type="button"
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
            onClick={async () => {
                try {
                    await navigator.clipboard.writeText(text);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                } catch {
                    // clipboard unavailable — nothing to fall back to in-browser
                }
            }}
        >
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copied" : "Copy"}
        </button>
    );
}

function StepRow({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
    return (
        <div className="flex items-start gap-2 text-sm">
            {ok ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
            ) : (
                <Circle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
            )}
            <div>
                <span className={ok ? "text-slate-200" : "text-slate-300"}>{label}</span>
                {detail ? <p className="text-xs text-slate-500 mt-0.5">{detail}</p> : null}
            </div>
        </div>
    );
}

function LLMSettings() {
    const [providers, setProviders] = useState<Record<string, {name:string}[]>>({});
    const [selectedProvider, setSelectedProvider] = useState("ollama");
    const [selectedModel, setSelectedModel] = useState("");
    const [status, setStatus] = useState<"loading"|"ready"|"error">("loading");
    useEffect(() => {
        fetch(API_BASE + "/api/llm/providers").then(r => {
            if (!r.ok) throw new Error(`providers ${r.status}`);
            return r.json();
        }).then(d => {
            setProviders(d);
            const savedP = localStorage.getItem("llm_provider") || "ollama";
            const savedM = localStorage.getItem("llm_model") || "";
            setSelectedProvider(savedP);
            const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
            setSelectedModel(savedM && models.some((m:{name:string}) => m.name === savedM) ? savedM : (models[0]?.name || ""));
            setStatus("ready");
        }).catch(() => {
            // Backend unreachable: honest empty state, never fake models.
            setProviders({ ollama: [], lm_studio: [] });
            setSelectedModel("");
            setStatus("error");
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
                    {models.length === 0 ? (
                        <option value="">-- no models found --</option>
                    ) : models.map((m) => <option key={m.name} value={m.name}>{m.name}</option>)}
                </select>
                {status === "loading" ? (
                    <p className="text-xs text-slate-500">Probing local providers…</p>
                ) : status === "error" ? (
                    <p className="text-xs text-red-400">Provider unreachable — is the backend up and Ollama / LM Studio running?</p>
                ) : (
                    <p className="text-xs text-slate-500">{models.length} live model{models.length === 1 ? "" : "s"} from {selectedProvider === "ollama" ? "Ollama" : "LM Studio"}.</p>
                )}
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
    const [gcpProject, setGcpProject] = useState("");
    const [gcpProjectFromEnv, setGcpProjectFromEnv] = useState(false);
    const [lyriaStatus, setLyriaStatus] = useState<LyriaStatus | null>(null);
    const [lyriaStatusLoading, setLyriaStatusLoading] = useState(true);
    const [hfToken, setHfToken] = useState("");
    const [hfTokenConfigured, setHfTokenConfigured] = useState(false);
    const [hfTokenFromEnv, setHfTokenFromEnv] = useState(false);
    const [hfStatus, setHfStatus] = useState<HuggingFaceStatus | null>(null);
    const [hfStatusLoading, setHfStatusLoading] = useState(true);
    const [lyriaModel, setLyriaModel] = useState("");
    const [lyriaModelFromEnv, setLyriaModelFromEnv] = useState(false);
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
            setGcpProject(s.google_cloud_project ?? "");
            setGcpProjectFromEnv(!!s.google_cloud_project_from_env);
            setLyriaModel(s.lyria_model ?? "lyria-002");
            setLyriaModelFromEnv(!!s.lyria_model_from_env);
            setHfTokenConfigured(!!s.hf_token_configured);
            setHfTokenFromEnv(!!s.hf_token_from_env);
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

    const checkLyriaStatus = useCallback(async () => {
        setLyriaStatusLoading(true);
        try {
            const s = await fetchLyriaStatus();
            setLyriaStatus(s);
        } catch (e) {
            setLyriaStatus(null);
            setErr(e instanceof Error ? e.message : "Failed to check Lyria status");
        } finally {
            setLyriaStatusLoading(false);
        }
    }, []);

    useEffect(() => {
        void checkLyriaStatus();
    }, [checkLyriaStatus]);

    const checkHfStatus = useCallback(async () => {
        setHfStatusLoading(true);
        try {
            const s = await fetchHuggingFaceStatus();
            setHfStatus(s);
        } catch (e) {
            setHfStatus(null);
            setErr(e instanceof Error ? e.message : "Failed to check Hugging Face status");
        } finally {
            setHfStatusLoading(false);
        }
    }, []);

    useEffect(() => {
        void checkHfStatus();
    }, [checkHfStatus]);

    const saveHfToken = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({ hf_token: hfToken.trim() || null });
            setHfToken("");
            setMsg("Saved.");
            await load();
            await checkHfStatus();
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

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

    const saveGcpProject = async () => {
        setErr(null);
        setMsg(null);
        setSaving(true);
        try {
            await postSettings({
                google_cloud_project: gcpProject.trim() || null,
                lyria_model: lyriaModel.trim() || null,
            });
            setMsg("Saved.");
            await load();
            await checkLyriaStatus();
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

            <Card className={`border-slate-800 bg-slate-950/50 ${lyriaStatus?.ready ? "" : "border-amber-900/40"}`}>
                <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                        <CardTitle className="text-white">Lyria (Google Vertex AI) setup</CardTitle>
                        {!lyriaStatusLoading && lyriaStatus ? (
                            <span
                                className={`text-xs font-medium px-2 py-1 rounded-full ${
                                    lyriaStatus.ready
                                        ? "bg-emerald-500/10 text-emerald-400"
                                        : "bg-amber-500/10 text-amber-400"
                                }`}
                            >
                                {lyriaStatus.ready ? "Ready" : "Not ready"}
                            </span>
                        ) : null}
                    </div>
                    <CardDescription className="text-slate-400">
                        Cloud music generation used as the first Quick Generate backend. Three things have to be true
                        before it works — this checklist tells you which ones aren't, live.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                    {loading || lyriaStatusLoading ? (
                        <p className="text-sm text-slate-500">Checking…</p>
                    ) : (
                        <>
                            <div className="space-y-3 rounded-lg border border-slate-800/80 p-3">
                                <StepRow
                                    ok={!!lyriaStatus?.gcloud_installed}
                                    label="Google Cloud CLI installed"
                                    detail={
                                        lyriaStatus?.gcloud_installed
                                            ? undefined
                                            : "Not found on PATH. Install it, then re-open a terminal."
                                    }
                                />
                                {!lyriaStatus?.gcloud_installed ? (
                                    <div className="ml-6 flex items-center gap-2 rounded bg-slate-900 px-2 py-1.5">
                                        <code className="text-xs text-slate-300 flex-1">
                                            winget install -e --id Google.CloudSDK
                                        </code>
                                        <CopyButton text="winget install -e --id Google.CloudSDK" />
                                    </div>
                                ) : null}

                                <StepRow
                                    ok={!!gcpProject || gcpProjectFromEnv}
                                    label="Google Cloud project ID configured"
                                    detail={
                                        gcpProject || gcpProjectFromEnv
                                            ? undefined
                                            : "Needs an existing GCP project with Vertex AI enabled — set it below."
                                    }
                                />

                                <StepRow
                                    ok={!!lyriaStatus?.adc_found}
                                    label="Application Default Credentials valid"
                                    detail={lyriaStatus?.adc_found ? undefined : lyriaStatus?.adc_detail}
                                />
                                {!lyriaStatus?.adc_found ? (
                                    <div className="ml-6 flex items-center gap-2 rounded bg-slate-900 px-2 py-1.5">
                                        <code className="text-xs text-slate-300 flex-1">
                                            gcloud auth application-default login
                                        </code>
                                        <CopyButton text="gcloud auth application-default login" />
                                    </div>
                                ) : null}
                            </div>

                            <p className="text-xs text-slate-500">
                                The two commands above open your own terminal / browser sign-in — this dashboard can't
                                run them for you. Run them, then hit Recheck.
                            </p>

                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={lyriaStatusLoading}
                                onClick={() => void checkLyriaStatus()}
                            >
                                <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${lyriaStatusLoading ? "animate-spin" : ""}`} />
                                Recheck
                            </Button>

                            <div className="grid gap-2 pt-2 border-t border-slate-800/80">
                                <Label className="text-slate-300">Google Cloud project ID</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="e.g. my-lyria-project"
                                    value={gcpProject}
                                    onChange={(e) => setGcpProject(e.target.value)}
                                    disabled={gcpProjectFromEnv}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label className="text-slate-300">Lyria model ID</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder="lyria-002"
                                    value={lyriaModel}
                                    onChange={(e) => setLyriaModel(e.target.value)}
                                    disabled={lyriaModelFromEnv}
                                />
                            </div>
                            {lyriaModelFromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">SONGGEN_LYRIA_MODEL</code> from the environment; clear it to edit here.
                                </p>
                            ) : null}
                            {gcpProjectFromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">GOOGLE_CLOUD_PROJECT</code> from the environment; clear it to edit here.
                                </p>
                            ) : null}
                            <Button
                                type="button"
                                variant="outline"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={saving || gcpProjectFromEnv}
                                onClick={() => void saveGcpProject()}
                            >
                                {saving ? "Saving…" : "Save Lyria project"}
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>

            <Card className={`border-slate-800 bg-slate-950/50 ${hfStatus?.ready ? "" : "border-amber-900/40"}`}>
                <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                        <CardTitle className="text-white">Stable Audio (Hugging Face) setup</CardTitle>
                        {!hfStatusLoading && hfStatus ? (
                            <span
                                className={`text-xs font-medium px-2 py-1 rounded-full ${
                                    hfStatus.ready
                                        ? "bg-emerald-500/10 text-emerald-400"
                                        : "bg-amber-500/10 text-amber-400"
                                }`}
                            >
                                {hfStatus.ready ? "Ready" : "Not ready"}
                            </span>
                        ) : null}
                    </div>
                    <CardDescription className="text-slate-400">
                        MusicGen fallback needs no account — it's a public model. Stable Audio Open is{" "}
                        <em>gated</em>: it needs your own Hugging Face account to accept the model license, plus an
                        access token here so the server can download it on your behalf.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {hfStatusLoading ? (
                        <p className="text-sm text-slate-500">Checking…</p>
                    ) : (
                        <>
                            <div className="space-y-3 rounded-lg border border-slate-800/80 p-3">
                                <StepRow
                                    ok={!!hfStatus?.token_configured}
                                    label="Hugging Face token configured"
                                    detail={hfStatus?.token_configured ? undefined : "Paste a token below."}
                                />
                                <StepRow
                                    ok={!!hfStatus?.token_valid}
                                    label="License accepted for stable-audio-open-1.0"
                                    detail={hfStatus?.token_valid ? undefined : hfStatus?.detail}
                                />
                            </div>

                            {!hfStatus?.token_valid ? (
                                <ol className="text-xs text-slate-500 list-decimal list-inside space-y-1">
                                    <li>
                                        Accept the license at{" "}
                                        <a
                                            className="text-slate-300 underline"
                                            href="https://huggingface.co/stabilityai/stable-audio-open-1.0"
                                            target="_blank"
                                            rel="noreferrer"
                                        >
                                            huggingface.co/stabilityai/stable-audio-open-1.0
                                        </a>{" "}
                                        (needs your own HF login — this dashboard can't do that step for you).
                                    </li>
                                    <li>
                                        Create a read token at{" "}
                                        <a
                                            className="text-slate-300 underline"
                                            href="https://huggingface.co/settings/tokens"
                                            target="_blank"
                                            rel="noreferrer"
                                        >
                                            huggingface.co/settings/tokens
                                        </a>{" "}
                                        and paste it below.
                                    </li>
                                </ol>
                            ) : null}

                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={hfStatusLoading}
                                onClick={() => void checkHfStatus()}
                            >
                                <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${hfStatusLoading ? "animate-spin" : ""}`} />
                                Recheck
                            </Button>

                            <div className="grid gap-2 pt-2 border-t border-slate-800/80">
                                <Label className="text-slate-300">Hugging Face token</Label>
                                <Input
                                    type="password"
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500 font-mono"
                                    placeholder={hfTokenConfigured ? "•••••••••••••••••• (configured)" : "hf_…"}
                                    value={hfToken}
                                    onChange={(e) => setHfToken(e.target.value)}
                                    disabled={hfTokenFromEnv}
                                />
                            </div>
                            {hfTokenFromEnv ? (
                                <p className="text-xs text-amber-200/90">
                                    Using <code className="text-slate-500">HF_TOKEN</code> from the environment; clear it to edit here.
                                </p>
                            ) : null}
                            <Button
                                type="button"
                                variant="outline"
                                className="border-slate-800 text-slate-200 hover:bg-slate-800"
                                disabled={saving || hfTokenFromEnv || !hfToken.trim()}
                                onClick={() => void saveHfToken()}
                            >
                                {saving ? "Saving…" : "Save Hugging Face token"}
                            </Button>
                        </>
                    )}
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
