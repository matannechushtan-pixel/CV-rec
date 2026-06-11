"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Users, FileText, Send, Briefcase, Download } from "lucide-react";

interface AdminStats {
  total_users: number;
  total_cvs: number;
  total_applications: number;
  total_jobs_posted: number;
}

const statCards = [
  { key: "total_users" as const, label: "Total Users", icon: Users },
  { key: "total_cvs" as const, label: "Total CVs", icon: FileText },
  { key: "total_applications" as const, label: "Total Applications", icon: Send },
  { key: "total_jobs_posted" as const, label: "Total Jobs Posted", icon: Briefcase },
];

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await api.get<AdminStats>("/admin/stats");
        setStats(data);
      } catch {
        setError("Failed to load stats.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleExport() {
    setExporting(true);
    try {
      const res = await api.get("/admin/users/export", { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "users_export.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to export users.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Admin</h1>
      <p className="mt-2 text-sm text-slate-400">Platform-wide stats and data exports.</p>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {loading ? (
        <p className="mt-8 text-sm text-slate-400">Loading…</p>
      ) : (
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <div key={card.key} className="glass-card p-5">
                <div className="mb-3 inline-flex rounded-xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 p-2.5">
                  <Icon className="h-5 w-5 text-blue-400" />
                </div>
                <p className="text-2xl font-bold text-white">{stats?.[card.key] ?? 0}</p>
                <p className="text-sm text-slate-400">{card.label}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="glass-card mt-8 p-6">
        <h2 className="text-lg font-semibold text-white">Export Users</h2>
        <p className="mt-1 text-sm text-slate-400">
          Download a spreadsheet with separate sheets for job seekers and employers.
        </p>
        <button type="button" onClick={handleExport} disabled={exporting} className="btn-primary mt-4">
          <Download className="h-4 w-4" />
          {exporting ? "Exporting…" : "Export Users to Excel"}
        </button>
      </div>
    </div>
  );
}
