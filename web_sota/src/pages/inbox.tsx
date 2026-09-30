import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSongs, type SongEntry } from "@/lib/api";

const PAGE_SIZE = 10;

export function Inbox() {
  const [entries, setEntries] = useState<SongEntry[]>([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchSongs()
      .then((d) => setEntries(d.entries ?? []))
      .catch((e: unknown) =>
        setErr(e instanceof Error ? e.message : "Failed to load inbox"),
      );
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter((e) =>
      [
        String(e.title ?? ""),
        String(e.genre ?? ""),
        String(e.mood ?? ""),
        String(e.repo_id ?? ""),
      ]
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [entries, query]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pages - 1);
  const visible = filtered.slice(
    safePage * PAGE_SIZE,
    safePage * PAGE_SIZE + PAGE_SIZE,
  );

  return (
    <div className="space-y-6" data-testid="inbox">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Inbox</h2>
        <p className="mt-1 text-sm text-slate-400">
          Every generation in the song repository. Search, page through, open in
          Listen.
        </p>
      </div>
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setPage(0);
        }}
        placeholder="Search title, genre, mood..."
        className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
        data-testid="inbox-search"
      />
      {err ? <p className="text-sm text-red-300">{err}</p> : null}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">
            Generations ({filtered.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {visible.length === 0 ? (
            <p className="text-sm text-slate-500">
              Empty. Generate something first.
            </p>
          ) : (
            <ul className="space-y-2">
              {visible.map((e) => (
                <li
                  key={String(e.repo_id ?? e.title)}
                  className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-100">
                      {String(e.title || "Untitled")}
                    </p>
                    <p className="text-xs text-slate-500">
                      {String(e.genre || "-")} · {String(e.mood || "-")}
                    </p>
                  </div>
                  <Link
                    to="/listen"
                    className="text-sm text-violet-400 hover:underline"
                  >
                    Open
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4 flex items-center gap-3 text-sm text-slate-400">
            <button
              type="button"
              disabled={safePage === 0}
              onClick={() => setPage(safePage - 1)}
              className="rounded border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Prev
            </button>
            <span data-testid="inbox-page">
              Page {safePage + 1} of {pages}
            </span>
            <button
              type="button"
              disabled={safePage >= pages - 1}
              onClick={() => setPage(safePage + 1)}
              className="rounded border border-slate-700 px-2 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
