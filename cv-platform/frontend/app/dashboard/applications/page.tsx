"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { Application } from "@/lib/types";

const COLUMNS: { key: Application["status"]; label: string }[] = [
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);

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

  useEffect(() => {
    load();
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
    } catch {
      load();
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Applications</h1>
        <p className="mt-2 text-sm text-slate-400">
          Track your applications through the pipeline. Drag cards between columns to update status.
        </p>
      </div>

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
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
