"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV, Roadmap } from "@/lib/types";
import { RoadmapTimeline } from "@/components/roadmap/RoadmapTimeline";
import { ProfileEnrichment } from "@/components/roadmap/ProfileEnrichment";
import { UpskillPlan } from "@/components/roadmap/UpskillPlan";
import { Sparkles, Brain } from "lucide-react";

interface CareerPathSuggestion {
  role: string;
  reasons: string[];
  votes: number;
  models: string[];
}

interface BrainstormCareerPathsResult {
  per_model: Record<string, { role: string; reason?: string }[]>;
  merged: CareerPathSuggestion[];
}

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCvId, setActiveCvId] = useState<string | null>(null);
  const [brainstorming, setBrainstorming] = useState(false);
  const [brainstormError, setBrainstormError] = useState<string | null>(null);
  const [careerPaths, setCareerPaths] = useState<BrainstormCareerPathsResult | null>(null);

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

  async function loadActiveCv() {
    try {
      const { data } = await api.get<CV[]>("/cv/");
      const active = data.find((cv) => cv.is_base && cv.structured_data) ?? data.find((cv) => cv.structured_data);
      setActiveCvId(active?.id ?? null);
    } catch {
      setActiveCvId(null);
    }
  }

  useEffect(() => {
    load();
    loadActiveCv();
  }, []);

  async function handleBrainstormCareerPaths() {
    if (!activeCvId) return;
    setBrainstorming(true);
    setBrainstormError(null);
    try {
      const { data } = await api.post<BrainstormCareerPathsResult>(
        `/cv/${activeCvId}/brainstorm-career-paths`
      );
      setCareerPaths(data);
    } catch {
      setBrainstormError("Failed to brainstorm career paths. Please try again.");
    } finally {
      setBrainstorming(false);
    }
  }

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
        <div className="flex flex-wrap gap-2">
          {activeCvId && (
            <button
              onClick={handleBrainstormCareerPaths}
              disabled={brainstorming}
              className="btn-secondary"
            >
              <Brain className="h-4 w-4" />
              {brainstorming ? "Brainstorming…" : "Brainstorm career paths"}
            </button>
          )}
          <button onClick={handleGenerate} disabled={generating} className="btn-primary">
            <Sparkles className="h-4 w-4" />
            {generating ? "Generating…" : roadmap ? "Regenerate" : "Generate"}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {brainstormError && <p className="text-sm text-red-400">{brainstormError}</p>}

      {careerPaths && (
        <div className="glass-card space-y-3 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Career path suggestions (Gemini + Claude + GPT)
          </h2>
          {careerPaths.merged.length === 0 ? (
            <p className="text-sm text-slate-400">No suggestions returned.</p>
          ) : (
            <ul className="space-y-2">
              {careerPaths.merged.map((s, i) => (
                <li
                  key={i}
                  className="flex flex-wrap items-start justify-between gap-2 rounded-xl border border-white/10 bg-white/5 p-3"
                >
                  <div>
                    <p className="font-semibold text-white">{s.role}</p>
                    {s.reasons[0] && <p className="mt-1 text-sm text-slate-400">{s.reasons[0]}</p>}
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                      s.votes >= 3
                        ? "bg-green-500/15 text-green-300"
                        : s.votes === 2
                        ? "bg-blue-500/15 text-blue-300"
                        : "bg-white/10 text-slate-400"
                    }`}
                  >
                    {s.votes}/3 models recommended
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

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
