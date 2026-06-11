"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import { RoadmapTimeline } from "@/components/roadmap/RoadmapTimeline";
import { ProfileEnrichment } from "@/components/roadmap/ProfileEnrichment";
import { UpskillPlan } from "@/components/roadmap/UpskillPlan";
import { Sparkles } from "lucide-react";

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const { data } = await api.get<Roadmap | null>("/roadmap/");
      setRoadmap(data);
    } catch {
      setError("Failed to load roadmap.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const { data } = await api.post<Roadmap>("/roadmap/generate", {});
      setRoadmap(data);
    } catch {
      setError(
        "Failed to generate roadmap. Make sure your profile has a target role and you've uploaded a CV."
      );
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Career Roadmap
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            A personalised plan to help you reach your target role.
          </p>
        </div>
        <button onClick={handleGenerate} disabled={generating} className="btn-primary">
          <Sparkles className="h-4 w-4" />
          {generating ? "Generating…" : roadmap ? "Regenerate" : "Generate"}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <ProfileEnrichment />
      <UpskillPlan />

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : !roadmap ? (
        <p className="text-sm text-slate-400">
          No roadmap yet. Click "Generate" to create your personalised plan.
        </p>
      ) : (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <div className="flex flex-wrap items-center gap-8">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Target role</p>
                <p className="text-lg font-semibold text-white">{roadmap.target_role}</p>
              </div>
              {roadmap.gap_analysis?.current_readiness_percentage != null && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Readiness</p>
                  <p className="gradient-text text-lg font-semibold">
                    {roadmap.gap_analysis.current_readiness_percentage}%
                  </p>
                </div>
              )}
              {roadmap.estimated_timeline_weeks != null && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Est. timeline</p>
                  <p className="text-lg font-semibold text-white">
                    {roadmap.estimated_timeline_weeks} weeks
                  </p>
                </div>
              )}
            </div>
          </div>

          {!!roadmap.gap_analysis?.immediate_actions?.length && (
            <div className="glass-card p-5">
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                This week
              </h2>
              <ul className="space-y-1">
                {roadmap.gap_analysis.immediate_actions.map((a, i) => (
                  <li key={i} className="text-sm text-slate-200">
                    • {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!!roadmap.gap_analysis?.quick_wins?.length && (
            <div className="glass-card p-5">
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Quick wins
              </h2>
              <ul className="space-y-1">
                {roadmap.gap_analysis.quick_wins.map((a, i) => (
                  <li key={i} className="text-sm text-slate-200">
                    • {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!!roadmap.steps?.length && (
            <div className="glass-card p-5">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Roadmap
              </h2>
              <RoadmapTimeline steps={roadmap.steps} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
