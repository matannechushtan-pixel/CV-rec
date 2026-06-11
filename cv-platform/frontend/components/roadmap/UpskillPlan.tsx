"use client";

import { useState } from "react";
import api from "@/lib/api";
import { GraduationCap, ChevronDown, ChevronUp } from "lucide-react";

interface UpskillGap {
  skill: string;
  priority: "critical" | "important" | "nice_to_have";
  resource_url: string;
  estimated_weeks: number;
}

interface UpskillReport {
  current_level: string;
  target_role: string;
  gaps: UpskillGap[];
  total_estimated_weeks: number;
}

const PRIORITY_STYLES: Record<string, string> = {
  critical: "bg-red-500/15 text-red-400",
  important: "bg-amber-500/15 text-amber-400",
  nice_to_have: "bg-slate-500/15 text-slate-400",
};

export function UpskillPlan() {
  const [open, setOpen] = useState(false);
  const [report, setReport] = useState<UpskillReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (report || loading) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<UpskillReport>("/profile/upskill-report", {});
      setReport(data);
    } catch {
      setError(
        "Failed to generate upskill plan. Make sure your profile has a target role and you've uploaded a CV."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card p-5">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          if (!open) load();
        }}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            Upskill Plan
          </h2>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {open && (
        <div className="mt-4 space-y-4">
          {loading && <p className="text-sm text-slate-400">Building your upskill plan…</p>}
          {error && <p className="text-sm text-red-400">{error}</p>}

          {report && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-8">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Current level</p>
                  <p className="text-lg font-semibold text-white capitalize">
                    {report.current_level}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Target role</p>
                  <p className="text-lg font-semibold text-white">{report.target_role}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Total time</p>
                  <p className="gradient-text text-lg font-semibold">
                    {report.total_estimated_weeks} weeks
                  </p>
                </div>
              </div>

              <ul className="space-y-2">
                {report.gaps.map((gap, i) => (
                  <li
                    key={i}
                    className="flex flex-col gap-2 rounded-xl border border-white/10 bg-white/5 p-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">{gap.skill}</span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            PRIORITY_STYLES[gap.priority] ?? PRIORITY_STYLES.nice_to_have
                          }`}
                        >
                          {gap.priority.replace("_", " ")}
                        </span>
                      </div>
                      <a
                        href={gap.resource_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:underline"
                      >
                        {gap.resource_url}
                      </a>
                    </div>
                    <span className="shrink-0 text-xs text-slate-400">
                      ~{gap.estimated_weeks} weeks
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
