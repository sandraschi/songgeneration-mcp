import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    fetchSongs,
    fetchSettings,
    fetchVirtualDjStatus,
    postExportPlex,
    postExportVirtualDj,
    type SongEntry,
} from "@/lib/api";
import {
    Headphones,
    RefreshCw,
    SkipBack,
    SkipForward,
    Upload,
    Music2,
    Disc3,
} from "lucide-react";

type StemRole = "vocal" | "instrumental" | "mix" | "untyped";
type Playable = {
    label: string;
    src: string;
    kind: "mp3" | "source" | "remote-fallback";
    stem: StemRole;
};

function collectPlayables(entry: SongEntry): Playable[] {
    const out: Playable[] = [];
    const stemOrder = ["vocal", "instrumental", "mix"] as const;

    for (const role of stemOrder) {
        const urls = entry.mp3_stem_urls?.[role] ?? [];
        for (let i = 0; i < urls.length; i++) {
            out.push({ label: `MP3 ${role} ${i + 1}`, src: urls[i], kind: "mp3", stem: role });
        }
    }
    for (const role of stemOrder) {
        const urls = entry.stem_urls?.[role] ?? [];
        for (let i = 0; i < urls.length; i++) {
            const isLocal = urls[i].startsWith("/api/media/");
            out.push({
                label: `Source ${role} ${i + 1}`,
                src: urls[i],
                kind: isLocal ? "source" : "remote-fallback",
                stem: role,
            });
        }
    }

    if (out.length === 0) {
        const mp3 = entry.mp3_urls ?? [];
        for (let i = 0; i < mp3.length; i++) {
            out.push({ label: `MP3 ${i + 1}`, src: mp3[i], kind: "mp3", stem: "untyped" });
        }
        const remote = entry.audio_urls ?? [];
        for (let i = 0; i < remote.length; i++) {
            const isLocal = remote[i].startsWith("/api/media/");
            out.push({
                label: `Source ${i + 1}`,
                src: remote[i],
                kind: isLocal ? "source" : "remote-fallback",
                stem: "untyped",
            });
        }
    }
    return out;
}

function stemLabel(stem: StemRole): string {
    if (stem === "instrumental") return "instrumental";
    if (stem === "vocal") return "vocal";
    if (stem === "mix") return "mix";
    return "untyped";
}

export function Listen() {
    const [entries, setEntries] = useState<SongEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState<string | null>(null);
    const [plexConfigured, setPlexConfigured] = useState(false);
    const [vdjConfigured, setVdjConfigured] = useState(false);
    const [vdjOnline, setVdjOnline] = useState<boolean | null>(null);
    const [selectedDeck, setSelectedDeck] = useState(1);
    const [autoPlayDeck, setAutoPlayDeck] = useState(true);
    const [syncToMaster, setSyncToMaster] = useState(false);
    const [cueAtStart, setCueAtStart] = useState(false);

    const [selectedIdx, setSelectedIdx] = useState(0);
    const [trackIdx, setTrackIdx] = useState(0);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const load = useCallback(async () => {
        setErr(null);
        setLoading(true);
        try {
            const [songs, settings] = await Promise.all([fetchSongs(), fetchSettings()]);
            setEntries(songs.entries);
            const dir = settings.plex_export_dir;
            setPlexConfigured(!!(dir && String(dir).trim()));
            const vdir = settings.virtualdj_drop_dir;
            setVdjConfigured(!!(vdir && String(vdir).trim()));
        } catch (e) {
            setErr(e instanceof Error ? e.message : "Failed to load");
            setEntries([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        const run = async () => {
            try {
                const s = await fetchVirtualDjStatus();
                setVdjOnline(!!s.ok);
            } catch {
                setVdjOnline(false);
            }
        };
        void run();
        const id = window.setInterval(() => void run(), 5000);
        return () => window.clearInterval(id);
    }, []);

    const current = entries[selectedIdx] ?? null;
    const playables = useMemo(() => (current ? collectPlayables(current) : []), [current]);
    const currentTrack = playables[trackIdx] ?? null;

    useEffect(() => {
        setTrackIdx(0);
    }, [selectedIdx]);

    useEffect(() => {
        const a = audioRef.current;
        if (!a) return;
        if (!currentTrack) {
            a.removeAttribute("src");
            a.load();
            return;
        }
        a.src = currentTrack.src;
        void a.play().catch(() => {
            /* autoplay blocked */
        });
    }, [currentTrack]);

    const goNextTrack = () => {
        if (playables.length === 0) return;
        setTrackIdx((t) => (t + 1) % playables.length);
    };

    const goPrevTrack = () => {
        if (playables.length === 0) return;
        setTrackIdx((t) => (t - 1 + playables.length) % playables.length);
    };

    const goNextEntry = () => {
        if (entries.length === 0) return;
        setSelectedIdx((i) => (i + 1) % entries.length);
    };

    const goPrevEntry = () => {
        if (entries.length === 0) return;
        setSelectedIdx((i) => (i - 1 + entries.length) % entries.length);
    };

    const onExportOne = async () => {
        if (!current) return;
        const r = await postExportPlex({ repo_id: current.repo_id });
        if (!r.success) {
            setErr(r.error ?? "Export failed");
            return;
        }
        setErr(null);
    };

    const onExportAll = async () => {
        const r = await postExportPlex({ export_all: true });
        if (!r.success) {
            setErr(r.error ?? "Export failed");
            return;
        }
        setErr(null);
    };

    const onSendToVirtualDj = async () => {
        if (!current) return;
        const r = await postExportVirtualDj({
            repo_id: current.repo_id,
            deck: selectedDeck,
            auto_play: autoPlayDeck,
            sync_to_master: syncToMaster,
            cue_at_start: cueAtStart,
        });
        if (!r.success) {
            setErr(r.error ?? "VirtualDJ export failed");
            return;
        }
        setErr(null);
    };

    const roleCounts = {
        vocal: current?.stem_urls?.vocal?.length ?? 0,
        instrumental: current?.stem_urls?.instrumental?.length ?? 0,
        mix: current?.stem_urls?.mix?.length ?? 0,
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Listen</h2>
                    <p className="text-slate-400">
                        DJ-friendly view: stems are labeled as vocal, instrumental, and mix.
                    </p>
                </div>
                <Button type="button" variant="outline" size="sm" onClick={() => void load()} className="border-slate-800">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {err ? (
                <p className="rounded-md border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-sm text-amber-200">{err}</p>
            ) : null}

            {loading ? (
                <p className="text-slate-500">Loading…</p>
            ) : entries.length === 0 ? (
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardContent className="py-12 text-center text-slate-500">
                        <Music2 className="mx-auto mb-3 h-10 w-10 text-slate-600" />
                        Nothing in the repository yet. Generate with MP3 transcoding enabled, then return here.
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-6 lg:grid-cols-5">
                    <Card className="border-slate-800 bg-gradient-to-b from-slate-900/80 to-slate-950/80 lg:col-span-3">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-white">
                                <Headphones className="h-6 w-6 text-violet-400" />
                                Now playing
                            </CardTitle>
                            <CardDescription className="text-slate-400">
                                {current ? `${current.title} · ${current.genre}` : ""}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid gap-2 sm:grid-cols-3">
                                <Badge variant="outline" className="justify-center border-slate-700 text-slate-300">
                                    vocal: {roleCounts.vocal}
                                </Badge>
                                <Badge variant="outline" className="justify-center border-slate-700 text-slate-300">
                                    instrumental: {roleCounts.instrumental}
                                </Badge>
                                <Badge variant="outline" className="justify-center border-slate-700 text-slate-300">
                                    mix: {roleCounts.mix}
                                </Badge>
                            </div>
                            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-6 shadow-inner">
                                <p className="mb-2 text-center text-sm text-slate-500">
                                    {currentTrack ? `${currentTrack.label} (${stemLabel(currentTrack.stem)})` : "No track"}
                                    {currentTrack?.kind === "mp3" ? (
                                        <Badge className="ml-2 bg-violet-600/30 text-violet-200">mp3</Badge>
                                    ) : currentTrack?.kind === "source" ? (
                                        <Badge variant="outline" className="ml-2 border-emerald-700 text-emerald-300">
                                            local source
                                        </Badge>
                                    ) : currentTrack ? (
                                        <Badge variant="outline" className="ml-2 border-slate-600 text-slate-400">
                                            remote fallback
                                        </Badge>
                                    ) : null}
                                </p>
                                <audio
                                    ref={audioRef}
                                    controls
                                    className="w-full"
                                    preload="metadata"
                                    onEnded={() => goNextTrack()}
                                />
                                <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                                    <Button type="button" variant="outline" size="sm" className="border-slate-700" onClick={goPrevEntry}>
                                        <SkipBack className="mr-1 h-4 w-4" />
                                        Prev song
                                    </Button>
                                    <Button type="button" variant="outline" size="sm" className="border-slate-700" onClick={goPrevTrack}>
                                        Prev stem
                                    </Button>
                                    <Button type="button" variant="outline" size="sm" className="border-slate-700" onClick={goNextTrack}>
                                        Next stem
                                    </Button>
                                    <Button type="button" variant="outline" size="sm" className="border-slate-700" onClick={goNextEntry}>
                                        Next song
                                        <SkipForward className="ml-1 h-4 w-4" />
                                    </Button>
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2 border-t border-slate-800 pt-4">
                                <Button
                                    type="button"
                                    variant="secondary"
                                    disabled={!current || !(current.mp3_urls && current.mp3_urls.length) || !plexConfigured}
                                    onClick={() => void onExportOne()}
                                    title={!plexConfigured ? "Set Plex export folder in Settings" : undefined}
                                >
                                    <Upload className="mr-2 h-4 w-4" />
                                    Export this song to Plex folder
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="border-sky-700 text-sky-200 hover:bg-sky-950/40"
                                    disabled={!vdjConfigured || vdjOnline === false}
                                    onClick={() => void onSendToVirtualDj()}
                                    title={!vdjConfigured ? "Set VirtualDJ drop folder in Settings" : undefined}
                                >
                                    <Disc3 className="mr-2 h-4 w-4" />
                                    Send to VirtualDJ deck {selectedDeck}
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="border-slate-700"
                                    disabled={!plexConfigured}
                                    onClick={() => void onExportAll()}
                                >
                                    Export all MP3s
                                </Button>
                            </div>
                            {!plexConfigured ? (
                                <p className="text-xs text-slate-500">
                                    Configure <strong className="text-slate-400">Plex music library path</strong> under Settings to enable export.
                                </p>
                            ) : null}
                            {!vdjConfigured ? (
                                <p className="text-xs text-slate-500">
                                    Configure <strong className="text-slate-400">VirtualDJ drop folder</strong> in Settings to enable deck handoff.
                                </p>
                            ) : null}
                            <div className="grid gap-2 rounded-md border border-slate-800 bg-slate-900/30 p-3 sm:grid-cols-5">
                                <div className="text-xs text-slate-400">
                                    VirtualDJ API:{" "}
                                    {vdjOnline === null ? "checking…" : vdjOnline ? "online" : "offline"}
                                </div>
                                <label className="flex items-center gap-2 text-xs text-slate-300">
                                    Deck
                                    <select
                                        className="h-7 rounded border border-slate-700 bg-slate-900 px-2 text-xs"
                                        value={selectedDeck}
                                        onChange={(e) => setSelectedDeck(Number(e.target.value))}
                                    >
                                        {[1, 2, 3, 4].map((d) => (
                                            <option key={d} value={d}>
                                                {d}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                                <label className="flex items-center gap-2 text-xs text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={autoPlayDeck}
                                        onChange={(e) => setAutoPlayDeck(e.target.checked)}
                                    />
                                    Auto-play after load
                                </label>
                                <label className="flex items-center gap-2 text-xs text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={syncToMaster}
                                        onChange={(e) => setSyncToMaster(e.target.checked)}
                                    />
                                    Sync to master
                                </label>
                                <label className="flex items-center gap-2 text-xs text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={cueAtStart}
                                        onChange={(e) => setCueAtStart(e.target.checked)}
                                    />
                                    Cue at start
                                </label>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50 lg:col-span-2">
                        <CardHeader>
                            <CardTitle className="text-white">Library</CardTitle>
                            <CardDescription className="text-slate-400">{entries.length} saved generations</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="max-h-[min(70vh,520px)] space-y-1 overflow-y-auto pr-1">
                                {entries.map((e, i) => {
                                    const active = i === selectedIdx;
                                    const n = (e.mp3_urls?.length ?? 0) + (e.audio_urls?.length ?? 0);
                                    const vocal = e.stem_urls?.vocal?.length ?? 0;
                                    const inst = e.stem_urls?.instrumental?.length ?? 0;
                                    return (
                                        <button
                                            key={e.repo_id}
                                            type="button"
                                            onClick={() => setSelectedIdx(i)}
                                            className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                                                active
                                                    ? "border-violet-500/50 bg-violet-950/30 text-white"
                                                    : "border-transparent bg-slate-900/40 text-slate-300 hover:border-slate-700"
                                            }`}
                                        >
                                            <div className="font-medium">{e.title}</div>
                                            <div className="text-xs text-slate-500">
                                                {e.genre} · {n} tracks · v:{vocal} i:{inst}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
