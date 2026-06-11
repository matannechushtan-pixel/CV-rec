"use client";

import Link from "next/link";
import { Briefcase, Users, ArrowRight } from "lucide-react";

const sections = [
  {
    label: "Job Posts",
    href: "/company/jobs",
    desc: "Post new roles and manage your open positions",
    icon: Briefcase,
  },
  {
    label: "Candidates",
    href: "/company/candidates",
    desc: "Browse ranked, AI-matched candidates for each role",
    icon: Users,
  },
];

export default function CompanyDashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
        Company Dashboard
      </h1>
      <p className="mb-8 mt-2 text-sm text-slate-400">
        Manage your job posts and review top candidates.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
