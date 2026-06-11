"use client";

import { JobCard } from "./JobCard";
import type { JobListing } from "@/lib/types";

export function JobFeed({
  jobs,
  onTailor,
  onApply,
}: {
  jobs: JobListing[];
  onTailor?: (job: JobListing) => void;
  onApply?: (job: JobListing) => void;
}) {
  if (!jobs.length) {
    return <p className="text-sm text-slate-400">No jobs to show. Try refreshing the feed.</p>;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onTailor={onTailor} onApply={onApply} />
      ))}
    </div>
  );
}
