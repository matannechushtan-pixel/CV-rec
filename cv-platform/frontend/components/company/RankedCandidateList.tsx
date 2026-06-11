"use client";

import { CandidateCard } from "./CandidateCard";

interface Candidate {
  id: string;
  full_name?: string;
  match_percentage: number;
  strong_matches?: string[];
  revealed?: boolean;
}

export function RankedCandidateList({
  candidates,
  onReveal,
}: {
  candidates: Candidate[];
  onReveal?: (id: string) => void;
}) {
  if (!candidates.length) {
    return <p className="text-sm text-slate-500">No candidates yet for this role.</p>;
  }
  const sorted = [...candidates].sort((a, b) => b.match_percentage - a.match_percentage);
  return (
    <div className="space-y-3">
      {sorted.map((c) => (
        <CandidateCard key={c.id} candidate={c} onReveal={onReveal} />
      ))}
    </div>
  );
}
