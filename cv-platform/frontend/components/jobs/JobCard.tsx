"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { JobListing } from "@/lib/types";

interface SalaryRange {
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  source: "listing" | "adzuna" | "ai_estimate" | "unavailable";
}

export function JobCard({
  job,
  onTailor,
  onApply,
}: {
  job: JobListing;
  onTailor?: (job: JobListing) => void;
  onApply?: (job: JobListing) => void;
}) {
  const [salary, setSalary] = useState<SalaryRange | null>(null);

  useEffect(() => {
    if (job.salary_min || job.salary_max) return;
    let cancelled = false;
    api
      .get<SalaryRange>(`/jobs/${job.id}/salary`)
      .then(({ data }) => {
        if (!cancelled) setSalary(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [job.id, job.salary_min, job.salary_max]);

  const salaryMin = job.salary_min ?? salary?.salary_min ?? null;
  const salaryMax = job.salary_max ?? salary?.salary_max ?? null;
  const isEstimate = !job.salary_min && !job.salary_max && salary?.source === "ai_estimate";

  return (
    <div className="glass-card-hover p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white">{job.title}</h3>
          <p className="text-sm text-slate-400">
            {job.company} · {job.location}
          </p>
        </div>
        {job.match_percentage !== undefined && (
          <span
            className={`shrink-0 text-xs font-bold px-2.5 py-1 rounded-full ${
              job.match_percentage >= 75
                ? "bg-green-500/15 text-green-400"
                : job.match_percentage >= 50
                ? "bg-yellow-500/15 text-yellow-400"
                : "bg-white/10 text-slate-400"
            }`}
          >
            {job.match_percentage}% match
          </span>
        )}
      </div>
      {(salaryMin || salaryMax) && (
        <p className="mt-2 text-xs text-slate-500">
          {salaryMin && `$${salaryMin.toLocaleString()}`}
          {salaryMin && salaryMax && " – "}
          {salaryMax && `$${salaryMax.toLocaleString()}`}
          {isEstimate && (
            <span className="ml-1.5 rounded-full bg-blue-500/15 px-1.5 py-0.5 text-[10px] font-medium text-blue-300">
              AI estimate
            </span>
          )}
        </p>
      )}
      {job.description && (
        <p className="mt-2 line-clamp-2 text-xs text-slate-500">{job.description}</p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        {job.apply_url && (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => onApply?.(job)}
            className="btn-primary !px-3 !py-1.5 text-xs"
          >
            Apply
          </a>
        )}
        {onTailor && (
          <button
            onClick={() => onTailor(job)}
            className="btn-secondary !px-3 !py-1.5 text-xs"
          >
            Tailor CV
          </button>
        )}
      </div>
    </div>
  );
}
