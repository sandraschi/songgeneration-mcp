import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Loader2, Music2, RefreshCw, Cpu } from "lucide-react";
import {
    fetchStudioStatus,
    fetchStudioInfo,
    postGenerate,
    fetchSongs,
    type GenerateResponse,
    type StudioStatus,
    type SongEntry,
    type GenerateBody,
} from "@/lib/api";

const defaultLyrics = `[verse]
Line one here.
; [chorus]
Hook line two.`;

export function Generate() {
    const [lyrics, setLyrics] = useState(defaultLyrics);
    const [title, setTitle] = useState("");
    const [genre, setGenre] = useState("Pop");
    const [mood, setMood] = useState("uplifting");
    const [tempo, setTempo] = useState(120);
    const [voice, setVoice] = useState("female");
    const [separateStems, setSeparateStems] = useState(true);
    const [mixDualTracks, setMixDualTracks] = useState(false);
    const [modelRepo, setModelRepo] = useState("tencent/SongGeneration");
    const [modelWeights, setModelWeights] = useState("v2-large");
    const [maxLengthSeconds, setMaxLengthSeconds] = useState(270);
    const [torchDtype, setTorchDtype] = useState("bfloat16");
    const [styleAudioPath, setStyleAudioPath] = useState("");
    const [autoFixPunct, setAutoFixPunct] = useState(true);
    const [transcodeMp3, setTranscodeMp3] = useState(false);

    const [studio, setStudio] = useState<StudioStatus | null>(null);
    const [studioErr, setStudioErr] = useState<string | null>(null);
    const [studioUiUrl, setStudioUiUrl] = useState<string>("");
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState<GenerateResponse | null>(null);
    const [submitErr, setSubmitErr] = useState<string | null>(null);

    const [songs, setSongs] = useState<SongEntry[]>([]);
    const [songsErr, setSongsErr] = useState<string | null>(null);

    const pollStudio = useCallback(async () => {
        setStudioErr(null);
        try {
            const s = await fetchStudioStatus();
            setStudio(s);
        } catch (e) {
            setStudio(null);
            setStudioErr(e instanceof Error ? e.message : "Studio status failed");
        }
    }, []);

    const loadStudioInfo = useCallback(async () => {
        try {
            const info = await fetchStudioInfo();
            setStudioUiUrl(info.ui_url);
        } catch {
            setStudioUiUrl("");
        }
    }, []);

    const loadSongs = useCallback(async () => {
        setSongsErr(null);
        try {
            const data = await fetchSongs();
            setSongs(data.entries);
        } catch (e) {
            setSongs([]);
            setSongsErr(e instanceof Error ? e.message : "Repository list failed");
        }
    }, []);

    useEffect(() => {
        void pollStudio();
        void loadStudioInfo();
        void loadSongs();
        const id = window.setInterval(() => void pollStudio(), 4000);
        return () => window.clearInterval(id);
    }, [pollStudio, loadStudioInfo, loadSongs]);

    const onSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setSubmitErr(null);
        setResult(null);
        const trimmed = lyrics.trim();
        if (!trimmed) {
            setSubmitErr("Lyrics are required.");
            return;
        }
        setSubmitting(true);
        try {
            const body: GenerateBody = {
                lyrics: trimmed,
                genre,
                mood,
                tempo: Number.isFinite(tempo) ? tempo : 120,
                voice,
                separate_stems: separateStems,
                mix_dual_tracks: mixDualTracks,
                model_repo: modelRepo || undefined,
                model_weights: modelWeights || undefined,
                max_length_seconds: maxLengthSeconds,
                torch_dtype: torchDtype,
                auto_fix_english_punctuation: autoFixPunct,
                transcode_to_mp3: transcodeMp3,
            };
            if (title.trim()) body.title = title.trim();
            if (styleAudioPath.trim()) body.style_audio_prompt_path = styleAudioPath.trim();

            const res = await postGenerate(body);
            setResult(res);
            if (!res.success) {
                setSubmitErr(res.error ?? "Generation failed");
            } else {
                await loadSongs();
            }
        } catch (err) {
            setSubmitErr(err instanceof Error ? err.message : "Request failed");
        } finally {
            setSubmitting(false);
        }
    };

    const stemRoles = [
        { key: "vocal", label: "Vocal stem" },
        { key: "instrumental", label: "Instrumental stem" },
        { key: "mix", label: "Mix/master" },
    ] as const;

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Generate</h2>
                <p className="text-slate-400">
                    Submit a job to SongGeneration-Studio via <code className="text-slate-500">POST /api/generate</code>. Playback URLs
                    appear only when the Studio JSON includes http(s) links the server can scrape.
                </p>
                {studioUiUrl ? (
                    <p className="mt-2 text-sm text-slate-500">
                        Need Studio controls?{" "}
                        <a
                            className="text-violet-300 hover:text-violet-200"
                            href={studioUiUrl}
                            target="_blank"
                            rel="noreferrer"
                        >
                            Open Studio UI
                        </a>
                    </p>
                ) : null}
            </div>

            <div className="grid gap-6 xl:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50 xl:col-span-2">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Music2 className="h-5 w-5 text-violet-400" />
                            Parameters
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Lyrics drive SG2 sections; semicolons trigger phrase boundaries when punctuation fix is on.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={onSubmit} className="space-y-4">
                            <div className="grid gap-2">
                                <Label className="text-slate-300">Lyrics</Label>
                                <textarea
                                    className="min-h-[160px] w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500"
                                    value={lyrics}
                                    onChange={(e) => setLyrics(e.target.value)}
                                    spellCheck={false}
                                />
                            </div>
                            <div className="grid gap-4 sm:grid-cols-2">
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Title (optional)</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        placeholder="e.g. Demo track"
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Genre</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={genre}
                                        onChange={(e) => setGenre(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Mood / emotion</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={mood}
                                        onChange={(e) => setMood(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Tempo (BPM)</Label>
                                    <Input
                                        type="number"
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={tempo}
                                        onChange={(e) => setTempo(Number(e.target.value))}
                                        min={40}
                                        max={240}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Voice</Label>
                                    <select
                                        className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm text-slate-100"
                                        value={voice}
                                        onChange={(e) => setVoice(e.target.value)}
                                    >
                                        <option value="female">female</option>
                                        <option value="male">male</option>
                                    </select>
                                </div>
                                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
                                    <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                                        <input
                                            type="checkbox"
                                            className="rounded border-slate-600"
                                            checked={separateStems}
                                            onChange={(e) => setSeparateStems(e.target.checked)}
                                        />
                                        Separate stems (dual tracks)
                                    </label>
                                    <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                                        <input
                                            type="checkbox"
                                            className="rounded border-slate-600"
                                            checked={mixDualTracks}
                                            onChange={(e) => setMixDualTracks(e.target.checked)}
                                        />
                                        Mix down mono
                                    </label>
                                    <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                                        <input
                                            type="checkbox"
                                            className="rounded border-slate-600"
                                            checked={autoFixPunct}
                                            onChange={(e) => setAutoFixPunct(e.target.checked)}
                                        />
                                        Auto-fix English punctuation
                                    </label>
                                    <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                                        <input
                                            type="checkbox"
                                            className="rounded border-slate-600"
                                            checked={transcodeMp3}
                                            onChange={(e) => setTranscodeMp3(e.target.checked)}
                                        />
                                        Transcode to MP3 (requires ffmpeg)
                                    </label>
                                </div>
                            </div>

                            <div className="grid gap-4 sm:grid-cols-2">
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">SG2 model repo</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={modelRepo}
                                        onChange={(e) => setModelRepo(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Weights</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={modelWeights}
                                        onChange={(e) => setModelWeights(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Max length (seconds)</Label>
                                    <Input
                                        type="number"
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={maxLengthSeconds}
                                        onChange={(e) => setMaxLengthSeconds(Number(e.target.value))}
                                        min={30}
                                        max={600}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label className="text-slate-300">Torch dtype</Label>
                                    <select
                                        className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 text-sm text-slate-100"
                                        value={torchDtype}
                                        onChange={(e) => setTorchDtype(e.target.value)}
                                    >
                                        <option value="bfloat16">bfloat16</option>
                                        <option value="float16">float16</option>
                                        <option value="float32">float32</option>
                                    </select>
                                </div>
                                <div className="grid gap-2 sm:col-span-2">
                                    <Label className="text-slate-300">Style audio path (optional, local)</Label>
                                    <Input
                                        className="bg-slate-900 border-slate-800 text-slate-100"
                                        value={styleAudioPath}
                                        onChange={(e) => setStyleAudioPath(e.target.value)}
                                        placeholder="Path on Studio machine for style RAG"
                                    />
                                </div>
                            </div>

                            {submitErr ? (
                                <p className="text-sm text-red-400">{submitErr}</p>
                            ) : null}

                            <Button
                                type="submit"
                                disabled={submitting}
                                className="bg-violet-600 text-white hover:bg-violet-500"
                            >
                                {submitting ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Submitting…
                                    </>
                                ) : (
                                    "Start generation"
                                )}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-200">
                                <Cpu className="h-4 w-4 text-emerald-400" />
                                Studio progress
                            </CardTitle>
                            <Button type="button" variant="ghost" size="sm" onClick={() => void pollStudio()}>
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                            {studioErr ? <p className="text-amber-400">{studioErr}</p> : null}
                            {studio ? (
                                <>
                                    <div className="flex justify-between text-slate-400">
                                        <span>Active generations</span>
                                        <span className="font-mono text-white">{studio.active_generations ?? "—"}</span>
                                    </div>
                                    <div className="flex justify-between text-slate-400">
                                        <span>Queued</span>
                                        <span className="font-mono text-white">{studio.queued_tasks ?? "—"}</span>
                                    </div>
                                    <div className="flex justify-between text-slate-400">
                                        <span>VRAM used / total</span>
                                        <span className="font-mono text-white">
                                            {(studio.vram_used ?? 0).toFixed(1)} / {(studio.vram_total ?? 0).toFixed(1)} GB
                                        </span>
                                    </div>
                                    <div className="flex justify-between text-slate-400">
                                        <span>Model</span>
                                        <span className="text-right text-slate-200">{studio.model_loaded ?? "—"}</span>
                                    </div>
                                    {studio.error ? (
                                        <p className="text-xs text-red-400">Studio unreachable: {studio.error}</p>
                                    ) : null}
                                </>
                            ) : (
                                <p className="text-slate-500">No status yet.</p>
                            )}
                            <p className="text-xs text-slate-500">
                                Polls <code className="text-slate-600">GET /api/studio/status</code> (GPU + queue from Studio).
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <CardTitle className="text-white">Last response</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {!result && !submitErr ? (
                                <p className="text-sm text-slate-500">Submit the form to see the API payload.</p>
                            ) : null}
                            {result?.success ? (
                                <>
                                    <p className="text-sm text-slate-300">{result.message}</p>
                                    {result.generation_id ? (
                                        <Badge variant="outline" className="border-slate-700 text-slate-300">
                                            ID: {result.generation_id}
                                        </Badge>
                                    ) : null}
                                    {result.repo_id ? (
                                        <p className="text-xs text-slate-500">
                                            Saved to repository as <code className="text-slate-400">{result.repo_id}</code>
                                        </p>
                                    ) : null}
                                    {result.punctuation_notes && result.punctuation_notes.length > 0 ? (
                                        <ul className="list-inside list-disc text-xs text-slate-400">
                                            {result.punctuation_notes.map((n, i) => (
                                                <li key={i}>{n}</li>
                                            ))}
                                        </ul>
                                    ) : null}
                                    {result.audio_urls && result.audio_urls.length > 0 ? (
                                        <div className="space-y-2">
                                            <p className="text-sm text-slate-400">Playback (source URLs)</p>
                                            {result.audio_urls.map((u) => (
                                                <audio key={u} controls className="w-full" src={u} preload="none" />
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-xs text-slate-500">
                                            No playable URLs in this response — check Studio output or open the Studio UI.
                                        </p>
                                    )}
                                    {result.mp3_urls && result.mp3_urls.length > 0 ? (
                                        <div className="space-y-2">
                                            <p className="text-sm text-slate-400">Playback (MP3)</p>
                                            {result.mp3_urls.map((u) => (
                                                <audio key={u} controls className="w-full" src={u} preload="none" />
                                            ))}
                                        </div>
                                    ) : null}
                                    {result.stem_urls ? (
                                        <div className="space-y-2 rounded-md border border-slate-800 bg-slate-900/40 p-3">
                                            <p className="text-sm text-slate-300">Stem detection (source)</p>
                                            <div className="grid gap-2 sm:grid-cols-3">
                                                {stemRoles.map((role) => {
                                                    const urls = result.stem_urls?.[role.key] ?? [];
                                                    return (
                                                        <div key={role.key} className="rounded border border-slate-800 p-2">
                                                            <p className="text-xs text-slate-500">{role.label}</p>
                                                            {urls.length > 0 ? (
                                                                <Badge className="mt-1 bg-emerald-900/40 text-emerald-200">
                                                                    ready ({urls.length})
                                                                </Badge>
                                                            ) : (
                                                                <Badge variant="outline" className="mt-1 border-slate-700 text-slate-400">
                                                                    missing
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ) : null}
                                    {result.mp3_stem_urls ? (
                                        <div className="space-y-2 rounded-md border border-slate-800 bg-slate-900/40 p-3">
                                            <p className="text-sm text-slate-300">Stem detection (MP3)</p>
                                            <div className="grid gap-2 sm:grid-cols-3">
                                                {stemRoles.map((role) => {
                                                    const urls = result.mp3_stem_urls?.[role.key] ?? [];
                                                    return (
                                                        <div key={role.key} className="rounded border border-slate-800 p-2">
                                                            <p className="text-xs text-slate-500">{role.label}</p>
                                                            {urls.length > 0 ? (
                                                                <Badge className="mt-1 bg-violet-900/40 text-violet-200">
                                                                    ready ({urls.length})
                                                                </Badge>
                                                            ) : (
                                                                <Badge variant="outline" className="mt-1 border-slate-700 text-slate-400">
                                                                    missing
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ) : null}
                                </>
                            ) : null}
                            {result && !result.success ? (
                                <p className="text-sm text-red-400">{result.error ?? "Unknown error"}</p>
                            ) : null}
                        </CardContent>
                    </Card>
                </div>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                    <div>
                        <CardTitle className="text-white">Song repository</CardTitle>
                        <CardDescription className="text-slate-400">
                            Local JSON store at <code className="text-slate-500">~/.songgeneration-mcp/repository.json</code> or{" "}
                            <code className="text-slate-500">SONGGEN_REPO_PATH</code>.
                        </CardDescription>
                    </div>
                    <Button type="button" variant="outline" size="sm" onClick={() => void loadSongs()} className="border-slate-800">
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refresh
                    </Button>
                </CardHeader>
                <CardContent>
                    {songsErr ? <p className="text-sm text-amber-400">{songsErr}</p> : null}
                    {songs.length === 0 ? (
                        <p className="text-sm text-slate-500">No saved generations yet.</p>
                    ) : (
                        <div className="space-y-4">
                            {songs.map((s) => (
                                <div
                                    key={s.repo_id}
                                    className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
                                >
                                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                                        <div>
                                            <p className="font-medium text-white">{s.title}</p>
                                            <p className="text-xs text-slate-500">
                                                {s.created_at} · {s.genre} · {s.mood}
                                            </p>
                                        </div>
                                        <Badge variant="secondary" className="font-mono text-xs">
                                            {s.repo_id.slice(0, 8)}…
                                        </Badge>
                                    </div>
                                    <p className="mt-2 text-sm text-slate-400">{s.message}</p>
                                    {s.audio_urls.length > 0 ? (
                                        <div className="mt-3 space-y-2">
                                            {s.audio_urls.map((u) => (
                                                <audio key={u} controls className="w-full max-w-xl" src={u} preload="none" />
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="mt-2 text-xs text-slate-500">No URLs extracted from Studio JSON.</p>
                                    )}
                                    {s.mp3_urls && s.mp3_urls.length > 0 ? (
                                        <div className="mt-3 space-y-2">
                                            <p className="text-xs text-slate-500">Compressed MP3</p>
                                            {s.mp3_urls.map((u) => (
                                                <audio key={u} controls className="w-full max-w-xl" src={u} preload="none" />
                                            ))}
                                        </div>
                                    ) : null}
                                    {s.stem_urls ? (
                                        <div className="mt-3 grid gap-2 sm:grid-cols-3">
                                            {stemRoles.map((role) => {
                                                const stemCount = s.stem_urls?.[role.key]?.length ?? 0;
                                                const mp3Count = s.mp3_stem_urls?.[role.key]?.length ?? 0;
                                                return (
                                                    <div key={role.key} className="rounded border border-slate-800 px-2 py-1.5">
                                                        <p className="text-xs text-slate-500">{role.label}</p>
                                                        <p className="text-xs text-slate-400">
                                                            src: {stemCount} · mp3: {mp3Count}
                                                        </p>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ) : null}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
