"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import type { ApplicationStats, CV } from "@/lib/types";
import {
  FileText,
  Briefcase,
  ClipboardList,
  Map,
  MessageSquare,
  ArrowRight,
} from "lucide-react";

const sections = [
  {
    label: "My CVs",
    href: "/dashboard/cv",
    desc: "Upload, manage, and tailor CV versions to specific roles",
    icon: FileText,
  },
  {
    label: "Job Feed",
    href: "/dashboard/jobs",
    desc: "Browse job listings matched to your profile",
    icon: Briefcase,
  },
  {
    label: "Applications",
    href: "/dashboard/applications",
    desc: "Track every application from applied to offer",
    icon: ClipboardList,
  },
  {
    label: "Career Roadmap",
    href: "/dashboard/roadmap",
    desc: "A personalised, week-by-week plan to your target role",
    icon: Map,
  },
  {
    label: "Interview Prep",
    href: "/dashboard/interview-prep",
    desc: "Practice behavioural and technical questions",
    icon: MessageSquare,
  },
];

export default function DashboardPage() {
  const [cvCount, setCvCount] = useState<number | null>(null);
  const [stats, setStats] = useState<ApplicationStats | null>(null);

  useEffect(() => {
    api
      .get<CV[]>("/cv/")
      .then(({ data }) => setCvCount(data.length))
      .catch(() => {});
    api
      .get<ApplicationStats>("/applications/stats")
      .then(({ data }) => setStats(data))
      .catch(() => {});
  }, []);

  const totalApplications = stats
    ? stats.applied + stats.viewed + stats.interview + stats.rejected + stats.offer
    : null;

  const statCards = [
    { label: "CVs created", value: cvCount },
    { label: "Applications", value: totalApplications },
    { label: "Interviews", value: stats?.interview ?? null },
    { label: "Offers", value: stats?.offer ?? null },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Dashboard</h1>
      <p className="mb-8 mt-2 text-sm text-slate-400">
        Welcome back. What would you like to do today?
      </p>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {statCards.map((s) => (
          <div key={s.label} className="glass-card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">{s.label}</p>
            <p className="mt-1 text-2xl font-bold text-white">{s.value ?? "–"}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((s) => {
          const Icon = s.icon;
          return (
            <Link
              key={s.href}
              href={s.href}
              className="glass-card glass-card-hover group block p-5"
            >
              <div className="mb-3 inline-flex rounded-xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 p-2.5">
                <Icon className="h-5 w-5 text-blue-400" />
              </div>
              <p className="mb-1 flex items-center gap-1.5 font-semibold text-white">
                {s.label}
                <ArrowRight className="h-3.5 w-3.5 -translate-x-1 text-slate-500 opacity-0 transition-all duration-200 group-hover:translate-x-0 group-hover:opacity-100" />
              </p>
              <p className="text-sm text-slate-400">{s.desc}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
