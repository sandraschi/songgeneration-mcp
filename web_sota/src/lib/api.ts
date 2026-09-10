// Fleet pattern: Vite dev proxy handles /api -> 10885, so relative URL is preferred.
// VITE_API_BASE can override for Tauri/production (e.g. http://127.0.0.1:10885).
const _envBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim() ?? "";
export const API_BASE = _envBase.replace(/\/$/, "") || "";
const _url = (path: string) => `${API_BASE}${path}`;
/** Relative URLs -- Vite dev server proxies `/api` and `/mcp` to uvicorn (see vite.config.ts). */

export async function fetchHealth(): Promise<{
  ok: boolean;
  service: string;
  version: string;
  mcp_path: string;
}> {
  const r = await fetch(_url("/api/health"));
  if (!r.ok) throw new Error(`health ${r.status}`);
  return r.json();
}

export type ApiLogLine = {
  ts: string;
  level: string;
  logger: string;
  message: string;
};

export async function fetchLogs(limit = 300): Promise<{ lines: ApiLogLine[]; count: number }> {
  const r = await fetch(_url(`/api/logs?limit=${encodeURIComponent(String(limit))}`));
  if (!r.ok) throw new Error(`logs ${r.status}`);
  return r.json();
}

export async function clearLogs(): Promise<{ cleared: number }> {
  const r = await fetch(_url("/api/logs/clear"), { method: "POST" });
  if (!r.ok) throw new Error(`clear ${r.status}`);
  return r.json();
}

export type StudioStatus = {
  vram_total?: number;
  vram_used?: number;
  active_generations?: number;
  queued_tasks?: number;
  server_running?: boolean;
  model_loaded?: string | null;
  error?: string;
};

export async function fetchStudioStatus(): Promise<StudioStatus> {
  const r = await fetch(_url("/api/studio/status"));
  if (!r.ok) throw new Error(`studio status ${r.status}`);
  return r.json();
}

export type GenerateBody = {
  lyrics: string;
  genre?: string;
  mood?: string;
  tempo?: number;
  voice?: string;
  title?: string;
  separate_stems?: boolean;
  mix_dual_tracks?: boolean;
  model_repo?: string | null;
  model_weights?: string | null;
  max_length_seconds?: number;
  torch_dtype?: string;
  style_audio_prompt_path?: string | null;
  auto_fix_english_punctuation?: boolean;
  transcode_to_mp3?: boolean;
};

export type GenerateResponse = {
  success: boolean;
  error?: string;
  generation_id?: string;
  message?: string;
  repo_id?: string;
  audio_urls?: string[];
  source_audio_urls?: string[];
  mp3_urls?: string[];
  stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  source_stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  mp3_stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  studio_response?: Record<string, unknown>;
  punctuation_notes?: string[];
};

export async function postGenerate(body: GenerateBody): Promise<GenerateResponse> {
  const r = await fetch(_url("/api/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await r.json()) as GenerateResponse;
  if (!r.ok && !data.success) return data;
  return data;
}

export type SongEntry = {
  repo_id: string;
  created_at: string;
  generation_id?: string;
  title: string;
  genre: string;
  mood: string;
  message: string;
  audio_urls: string[];
  source_audio_urls?: string[];
  mp3_urls?: string[];
  stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  source_stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  mp3_stem_urls?: { vocal?: string[]; instrumental?: string[]; mix?: string[] };
  punctuation_notes?: string[];
};

export async function fetchSongs(): Promise<{ entries: SongEntry[] }> {
  const r = await fetch(_url("/api/songs"));
  if (!r.ok) throw new Error(`songs ${r.status}`);
  return r.json();
}

export type AppSettings = {
  plex_export_dir?: string | null;
  plex_export_dir_from_env?: boolean;
  studio_url?: string | null;
  studio_url_from_env?: boolean;
  studio_dir?: string | null;
  studio_dir_from_env?: boolean;
  virtualdj_drop_dir?: string | null;
  virtualdj_api_base?: string | null;
  virtualdj_api_base_from_env?: boolean;
  reaper_drop_dir?: string | null;
  reaper_drop_dir_from_env?: boolean;
  reaper_api_base?: string | null;
  reaper_api_base_from_env?: boolean;
  google_cloud_project?: string | null;
  google_cloud_project_from_env?: boolean;
  lyria_model?: string | null;
  lyria_model_from_env?: boolean;
  /** Never the raw token — the backend redacts it. Just whether one is set. */
  hf_token_configured?: boolean;
  hf_token_from_env?: boolean;
};

export async function fetchSettings(): Promise<AppSettings> {
  const r = await fetch(_url("/api/settings"));
  if (!r.ok) throw new Error(`settings ${r.status}`);
  return r.json();
}

export async function postSettings(body: {
  plex_export_dir?: string | null;
  studio_url?: string | null;
  studio_dir?: string | null;
  virtualdj_drop_dir?: string | null;
  virtualdj_api_base?: string | null;
  reaper_drop_dir?: string | null;
  reaper_api_base?: string | null;
  google_cloud_project?: string | null;
  lyria_model?: string | null;
  hf_token?: string | null;
}): Promise<AppSettings> {
  const r = await fetch(_url("/api/settings"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`settings ${r.status}`);
  return r.json();
}

export type StudioInfo = {
  studio_url: string;
  ui_url: string;
  reachable: boolean;
  status_error?: string;
};

export async function fetchStudioInfo(): Promise<StudioInfo> {
  const r = await fetch(_url("/api/studio/info"));
  if (!r.ok) throw new Error(`studio info ${r.status}`);
  return r.json();
}

export type LyriaStatus = {
  gcloud_installed: boolean;
  project: string | null;
  project_configured: boolean;
  adc_found: boolean;
  adc_detail: string;
  adc_project: string | null;
  lyria_model: string;
  ready: boolean;
};

export async function fetchLyriaStatus(): Promise<LyriaStatus> {
  const r = await fetch(_url("/api/lyria/status"));
  if (!r.ok) throw new Error(`lyria status ${r.status}`);
  return r.json();
}

export type HuggingFaceStatus = {
  token_configured: boolean;
  token_valid: boolean;
  detail: string;
  ready: boolean;
};

export async function fetchHuggingFaceStatus(): Promise<HuggingFaceStatus> {
  const r = await fetch(_url("/api/huggingface/status"));
  if (!r.ok) throw new Error(`huggingface status ${r.status}`);
  return r.json();
}

export type PlexExportResponse = {
  success: boolean;
  error?: string;
  copied?: string[];
  copied_count?: number;
  dest_dir?: string;
  errors?: string[];
};

export async function postExportPlex(body: { repo_id?: string; export_all?: boolean }): Promise<PlexExportResponse> {
  const r = await fetch(_url("/api/export/plex"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return (await r.json()) as PlexExportResponse;
}

export type VirtualDjExportResponse = {
  success: boolean;
  error?: string;
  path?: string;
  deck?: number;
  virtualdj_base?: string;
};

export async function postExportVirtualDj(body: {
  repo_id: string;
  deck?: number;
  auto_play?: boolean;
  sync_to_master?: boolean;
  cue_at_start?: boolean;
}): Promise<VirtualDjExportResponse> {
  const r = await fetch(_url("/api/export/virtualdj"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return (await r.json()) as VirtualDjExportResponse;
}

export type VirtualDjStatus = {
  ok: boolean;
  virtualdj_base: string;
  error?: string;
  response?: Record<string, unknown>;
};

export async function fetchVirtualDjStatus(): Promise<VirtualDjStatus> {
  const r = await fetch(_url("/api/export/virtualdj/status"));
  if (!r.ok) throw new Error(`virtualdj status ${r.status}`);
  return r.json();
}

export type ReaperExportResponse = {
  success: boolean;
  error?: string;
  path?: string;
  reaper_base?: string;
};

export async function postExportReaper(body: {
  repo_id: string;
  auto_import?: boolean;
}): Promise<ReaperExportResponse> {
  const r = await fetch(_url("/api/export/reaper"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return (await r.json()) as ReaperExportResponse;
}

export type QuickGenerateResponse = {
  success: boolean;
  file: string;
  backend: string;
  model: string;
  error?: string;
  generation_id?: string;
  message?: string;
  hint?: string;
  backend_errors?: Record<string, string>;
};

export async function postQuickGenerate(prompt: string, duration: number): Promise<QuickGenerateResponse> {
  let r: Response;
  try {
    r = await fetch(_url("/api/v1/generate"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt, duration}),
    });
  } catch (e) {
    return {
      success: false, file: "", backend: "none", model: "",
      error: e instanceof Error ? `backend unreachable: ${e.message}` : "backend unreachable",
    };
  }
  const text = await r.text();
  let data: QuickGenerateResponse;
  try {
    data = JSON.parse(text) as QuickGenerateResponse;
  } catch {
    return {
      success: false, file: "", backend: "none", model: "",
      error: `backend HTTP ${r.status}: ${(text || r.statusText).slice(0, 200)}`,
    };
  }
  return data;
}

export async function fetchBackends(): Promise<{available: string[]; active: string}> {
  const r = await fetch(_url("/api/health"));
  if (!r.ok) return {available: [], active: "none"};
  return r.json();
}
