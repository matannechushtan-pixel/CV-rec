"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { Application, ApplicationStats } from "@/lib/types";
import { Modal } from "@/components/ui/Modal";

const COLUMNS: { key: Application["status"]; label: string }[] = [
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];

function daysAgo(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days <= 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);

  const [activeApp, setActiveApp] = useState<Application | null>(null);
  const [notesDraft, setNotesDraft] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<Application[]>("/applications/");
      setApplications(data);
    } catch {
      setError("Failed to load applications.");
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    try {
      const { data } = await api.get<ApplicationStats>("/applications/stats");
      setStats(data);
    } catch {
      // best-effort
    }
  }

  useEffect(() => {
    load();
    loadStats();
  }, []);

  function columnApps(status: Application["status"]) {
    if (status === "applied") {
      return applications.filter((a) => a.status === "applied" || a.status === "viewed");
    }
    return applications.filter((a) => a.status === status);
  }

  async function handleDrop(status: Application["status"]) {
    if (!dragId) return;
    const id = dragId;
    setDragId(null);
    const app = applications.find((a) => a.id === id);
    if (!app || app.status === status) return;

    setApplications((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
    try {
      await api.patch(`/applications/${id}`, { status });
      loadStats();
    } catch {
      load();
    }
  }

  function openApp(app: Application) {
    setActiveApp(app);
    setNotesDraft(app.notes ?? "");
  }

  async function saveNotes() {
    if (!activeApp) return;
    setSavingNotes(true);
    try {
      await api.patch(`/applications/${activeApp.id}`, { notes: notesDraft });
      setApplications((prev) =>
        prev.map((a) => (a.id === activeApp.id ? { ...a, notes: notesDraft } : a))
      );
      setActiveApp(null);
    } catch {
      // best-effort
    } finally {
      setSavingNotes(false);
    }
  }

  const totalApps = stats
    ? stats.applied + stats.viewed + stats.interview + stats.rejected + stats.offer
    : 0;
  const interviewRate = totalApps > 0 && stats ? Math.round((stats.interview / totalApps) * 100) : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Applications</h1>
        <p className="mt-2 text-sm text-slate-400">
          Track your applications through the pipeline. Drag cards between columns to update status.
        </p>
      </div>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="glass-card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Total applied</p>
            <p className="mt-1 text-2xl font-bold text-white">{totalApps}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Interviews</p>
            <p className="mt-1 text-2xl font-bold text-white">{stats.interview}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Offers</p>
            <p className="mt-1 text-2xl font-bold text-white">{stats.offer}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Interview rate</p>
            <p className="mt-1 text-2xl font-bold text-white">{interviewRate}%</p>
          </div>
        </div>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : applications.length === 0 ? (
        <p className="text-sm text-slate-400">
          No applications yet. Apply to jobs from the Job Feed to see them here.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {COLUMNS.map((col) => (
            <div
              key={col.key}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(col.key)}
              className="glass-card flex min-h-[200px] flex-col gap-3 p-4"
            >
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                {col.label}{" "}
                <span className="text-slate-600">({columnApps(col.key).length})</span>
              </h2>
              <div className="flex flex-col gap-2">
                {columnApps(col.key).map((app) => (
                  <div
                    key={app.id}
                    draggable
                    onDragStart={() => setDragId(app.id)}
                    onClick={() => openApp(app)}
                    className="cursor-grab rounded-xl border border-white/10 bg-white/5 p-3 transition-colors hover:border-white/20 active:cursor-grabbing"
                  >
                    <p className="text-sm font-medium text-white">
                      {app.job?.title ?? "Untitled role"}
                    </p>
                    <p className="text-xs text-slate-400">
                      {app.job?.company} {app.job?.company && app.job?.location && "·"}{" "}
                      {app.job?.location}
                    </p>
                    {app.match_score != null && (
                      <p className="mt-1 text-xs text-blue-400">
                        {Math.round(app.match_score)}% match
                      </p>
                    )}
                    <p className="mt-1 text-xs text-slate-500">
                      Applied {new Date(app.applied_at).toLocaleDateString()} · {daysAgo(app.applied_at)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeApp && (
        <Modal title={activeApp.job?.title ?? "Application"} onClose={() => setActiveApp(null)}>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-400">
                {activeApp.job?.company} {activeApp.job?.company && activeApp.job?.location && "·"}{" "}
                {activeApp.job?.location}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Applied {new Date(activeApp.applied_at).toLocaleDateString()} · {daysAgo(activeApp.applied_at)}
              </p>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
                Notes
              </label>
              <textarea
                value={notesDraft}
                onChange={(e) => setNotesDraft(e.target.value)}
                rows={6}
                placeholder="Add notes about this application…"
                className="w-full resize-y rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
            <button onClick={saveNotes} disabled={savingNotes} className="btn-primary">
              {savingNotes ? "Saving…" : "Save notes"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
