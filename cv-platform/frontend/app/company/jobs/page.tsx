import { Briefcase } from "lucide-react";

export default function CompanyJobsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Job Posts</h1>
      <p className="mt-2 text-sm text-slate-400">
        Post new roles and manage your open positions.
      </p>

      <div className="glass-card mt-8 flex flex-col items-center gap-3 p-12 text-center">
        <div className="inline-flex rounded-xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 p-3">
          <Briefcase className="h-6 w-6 text-blue-400" />
        </div>
        <h2 className="text-lg font-semibold text-white">Coming soon</h2>
        <p className="max-w-sm text-sm text-slate-400">
          Job post management is on its way — soon you&apos;ll be able to create roles and track
          applicants from here.
        </p>
      </div>
    </div>
  );
}
