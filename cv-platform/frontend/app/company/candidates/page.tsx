import { Users } from "lucide-react";

export default function CandidatesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Candidates</h1>
      <p className="mt-2 text-sm text-slate-400">
        Browse ranked, AI-matched candidates for each role.
      </p>

      <div className="glass-card mt-8 flex flex-col items-center gap-3 p-12 text-center">
        <div className="inline-flex rounded-xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 p-3">
          <Users className="h-6 w-6 text-blue-400" />
        </div>
        <h2 className="text-lg font-semibold text-white">Coming soon</h2>
        <p className="max-w-sm text-sm text-slate-400">
          Once you post a role, AI-ranked candidates matched to that job will appear here.
        </p>
      </div>
    </div>
  );
}
