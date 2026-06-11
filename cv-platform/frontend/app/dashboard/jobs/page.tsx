"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV, JobListing, SmartSearchResult, FitEvaluation } from "@/lib/types";
import { JobFeed } from "@/components/jobs/JobFeed";
import { Modal } from "@/components/ui/Modal";
import { Search, Sparkles, Download } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [cvs, setCvs] = useState<CV[]>([]);

  const [smartResults, setSmartResults] = useState<SmartSearchResult[] | null>(null);
  const [smartLoading, setSmartLoading] = useState(false);
  const [smartError, setSmartError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"all" | "for-you">("all");
  const [recommended, setRecommended] = useState<JobListing[] | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);

  const [tailorJob, setTailorJob] = useState<JobListing | null>(null);
  const [tailoredText, setTailoredText] = useState<string | null>(null);
  const [tailorWorking, setTailorWorking] = useState(false);
  const [tailorError, setTailorError] = useState<string | null>(null);

  const [fitResult, setFitResult] = useState<FitEvaluation | null>(null);
  const [fitLoading, setFitLoading] = useState(false);

  async function loadJobs(params?: { title?: string; location?: string }) {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<JobListing[]>("/jobs/", { params });
      setJobs(data);
    } catch {
      setError("Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
    api
      .get<CV[]>("/cv/")
      .then(({ data }) => setCvs(data))
      .catch(() => {});
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadJobs({ title: title || undefined, location: location || undefined });
  }

  async function handleSmartSearch() {
    setSmartLoading(true);
    setSmartError(null);
    try {
      const { data } = await api.post<SmartSearchResult[]>("/jobs/smart-search", {
        title: title || undefined,
        location: location || undefined,
      });
      setSmartResults(data);
    } catch {
      setSmartError("Smart search failed. Make sure you've uploaded a CV.");
    } finally {
      setSmartLoading(false);
    }
  }

  function activeCv(): CV | undefined {
    return cvs.find((c) => c.is_base) ?? cvs[0];
  }

  async function loadRecommended() {
    const cv = activeCv();
    if (!cv) {
      setRecError("Upload a CV first from the My CVs page.");
      return;
    }
    setRecLoading(true);
    setRecError(null);
    try {
      const { data } = await api.post<JobListing[]>("/jobs/recommended", { cv_id: cv.id });
      setRecommended(data.map((j) => ({ ...j, match_percentage: j.match_score })));
    } catch {
      setRecError("Failed to load recommendations.");
    } finally {
      setRecLoading(false);
    }
  }

  function selectTab(tab: "all" | "for-you") {
    setActiveTab(tab);
    if (tab === "for-you" && recommended === null && !recLoading) {
      loadRecommended();
    }
  }

  async function handleApply(job: JobListing) {
    try {
      await api.post("/applications/", {
        job_listing_id: job.id,
        cv_id: activeCv()?.id,
      });
    } catch {
      // best-effort tracking; the external apply link still opens regardless
    }
  }

  function openTailor(job: JobListing) {
    setTailorJob(job);
    setTailoredText(null);
    setTailorError(null);
    setFitResult(null);

    const cv = activeCv();
    if (cv) {
      setFitLoading(true);
      api
        .post<FitEvaluation>(`/cv/${cv.id}/evaluate-fit`, {
          job_description: job.description ?? job.title ?? "",
        })
        .then(({ data }) => setFitResult(data))
        .catch(() => {})
        .finally(() => setFitLoading(false));
    }
  }

  async function handleTailor() {
    if (!tailorJob) return;
    const cv = activeCv();
    if (!cv) {
      setTailorError("Upload a CV first from the My CVs page.");
      return;
    }
    setTailorWorking(true);
    setTailorError(null);
    try {
      const { data } = await api.post<{ tailored_text: string }>(`/cv/${cv.id}/tailor`, {
        job_description: tailorJob.description ?? tailorJob.title ?? "",
      });
      setTailoredText(data.tailored_text);
    } catch {
      setTailorError("Failed to tailor CV.");
    } finally {
      setTailorWorking(false);
    }
  }

  function downloadTailored() {
    if (!tailoredText || !tailorJob) return;
    const blob = new Blob([tailoredText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cv-tailored-${(tailorJob.title ?? "job").toLowerCase().replace(/\s+/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Job Feed</h1>
        <p className="mt-2 text-sm text-slate-400">Live job listings matched to your profile.</p>
      </div>

      <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Job title (e.g. Backend Engineer)"
          className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
        />
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Location"
          className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
        />
        <button type="submit" className="btn-secondary">
          <Search className="h-4 w-4" />
          Search
        </button>
        <button
          type="button"
          onClick={handleSmartSearch}
          disabled={smartLoading}
          className="btn-primary"
        >
          <Sparkles className="h-4 w-4" />
          {smartLoading ? "Searching…" : "Smart Search"}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {smartError && <p className="text-sm text-red-400">{smartError}</p>}

      {smartResults && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Smart matches</h2>
          {smartResults.length === 0 ? (
            <p className="text-sm text-slate-400">
              No ranked matches found right now. Try a broader title or location.
            </p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {smartResults.map((r) => (
                <div key={r.job.id} className="glass-card space-y-3 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-white">{r.job.title}</h3>
                      <p className="text-sm text-slate-400">
                        {r.job.company} · {r.job.location}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-full bg-green-500/15 px-2.5 py-1 text-xs font-bold text-green-400">
                      {r.match_percentage}% match
                    </span>
                  </div>
                  {r.strong_matches.length > 0 && (
                    <ul className="space-y-1">
                      {r.strong_matches.slice(0, 3).map((m) => (
                        <li key={m} className="text-sm text-green-400">
                          ✓ {m}
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {r.job.apply_url && (
                      <a
                        href={r.job.apply_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => handleApply(r.job)}
                        className="btn-primary !px-3 !py-1.5 text-xs"
                      >
                        Apply
                      </a>
                    )}
                    {r.tailored_cv_snippet && (
                      <button
                        onClick={() => {
                          setTailorJob(r.job);
                          setTailoredText(r.tailored_cv_snippet);
                          setTailorError(null);
                        }}
                        className="btn-secondary !px-3 !py-1.5 text-xs"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        View tailored CV
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        <div className="inline-flex rounded-xl border border-white/10 bg-white/5 p-1">
          <button
            type="button"
            onClick={() => selectTab("all")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "all" ? "bg-blue-500/20 text-blue-300" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All listings
          </button>
          <button
            type="button"
            onClick={() => selectTab("for-you")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "for-you" ? "bg-blue-500/20 text-blue-300" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            For You
          </button>
        </div>

        {activeTab === "all" ? (
          loading ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : (
            <JobFeed jobs={jobs} onTailor={openTailor} onApply={handleApply} />
          )
        ) : recError ? (
          <p className="text-sm text-red-400">{recError}</p>
        ) : recLoading || recommended === null ? (
          <p className="text-sm text-slate-400">Finding jobs that match your CV…</p>
        ) : (
          <JobFeed jobs={recommended} onTailor={openTailor} onApply={handleApply} />
        )}
      </div>

      {tailorJob && (
        <Modal title={`Tailor CV for "${tailorJob.title ?? "this job"}"`} onClose={() => setTailorJob(null)}>
          <div className="space-y-4">
            {fitLoading && <p className="text-sm text-slate-400">Checking fit…</p>}
            {fitResult && (
              <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 p-4">
                <div
                  className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-4 text-lg font-bold ${
                    fitResult.score >= 70
                      ? "border-green-500 text-green-400"
                      : fitResult.score >= 40
                        ? "border-amber-500 text-amber-400"
                        : "border-red-500 text-red-400"
                  }`}
                >
                  {fitResult.score}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold capitalize text-white">
                    {fitResult.recommendation === "apply"
                      ? "Good fit – worth applying"
                      : fitResult.recommendation === "stretch"
                        ? "Stretch role"
                        : "Likely a poor fit"}
                  </p>
                  <ul className="mt-1 space-y-0.5">
                    {fitResult.reasons.map((r, i) => (
                      <li key={i} className="text-xs text-slate-400">
                        • {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {tailorError && <p className="text-sm text-red-400">{tailorError}</p>}
            {!tailoredText && (
              <button onClick={handleTailor} disabled={tailorWorking} className="btn-primary">
                {tailorWorking ? "Working…" : "Generate tailored CV"}
              </button>
            )}
            {tailoredText && (
              <div className="space-y-3">
                <div className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200">
                  {tailoredText}
                </div>
                <button onClick={downloadTailored} className="btn-secondary">
                  <Download className="h-3.5 w-3.5" />
                  Download as .txt
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
