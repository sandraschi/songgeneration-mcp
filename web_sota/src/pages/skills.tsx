import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSkills, type RepoSkill } from "@/lib/api";

export function Skills() {
  const [skills, setSkills] = useState<RepoSkill[]>([]);
  const [preprompt, setPreprompt] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchSkills()
      .then((d) => {
        setSkills(d.skills ?? []);
        setPreprompt(d.preprompt_chars ?? 0);
      })
      .catch((e: unknown) =>
        setErr(e instanceof Error ? e.message : "Failed to load skills"),
      );
  }, []);

  return (
    <div className="space-y-6" data-testid="skills">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Skills</h2>
        <p className="mt-1 text-sm text-slate-400">
          Repo skills the Chat page prepends to every conversation ({preprompt}{" "}
          chars). Served by{" "}
          <code className="text-slate-500">GET /api/skills</code>.
        </p>
      </div>
      {err ? <p className="text-sm text-red-300">{err}</p> : null}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">
            Available ({skills.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {skills.length === 0 ? (
            <p className="text-sm text-slate-500">No skills found.</p>
          ) : (
            <ul className="space-y-2">
              {skills.map((s) => (
                <li
                  key={s.name}
                  className="rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2"
                >
                  <p className="text-sm font-medium text-slate-100">{s.name}</p>
                  <p className="text-xs text-slate-500">
                    {s.path} · {s.chars} chars
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
