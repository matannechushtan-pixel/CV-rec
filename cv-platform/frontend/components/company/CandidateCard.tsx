interface CandidateCardProps {
  candidate: {
    id: string;
    full_name?: string;
    match_percentage: number;
    strong_matches?: string[];
    revealed?: boolean;
  };
  onReveal?: (id: string) => void;
}

export function CandidateCard({ candidate, onReveal }: CandidateCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="font-semibold text-slate-900">
          {candidate.revealed && candidate.full_name ? candidate.full_name : "Anonymous Candidate"}
        </p>
        <span
          className={`text-xs font-bold px-2.5 py-1 rounded-full ${
            candidate.match_percentage >= 75
              ? "bg-green-100 text-green-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {candidate.match_percentage}% match
        </span>
      </div>
      {candidate.strong_matches && (
        <ul className="text-xs text-slate-500 space-y-0.5 mb-3">
          {candidate.strong_matches.slice(0, 3).map((m) => (
            <li key={m}>✓ {m}</li>
          ))}
        </ul>
      )}
      {!candidate.revealed && onReveal && (
        <button
          onClick={() => onReveal(candidate.id)}
          className="text-xs px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 transition"
        >
          Reveal identity
        </button>
      )}
    </div>
  );
}
