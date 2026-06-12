import type { GapAnalysis } from "@/lib/types";

const importanceColor = {
  critical: "bg-red-500/15 text-red-300",
  important: "bg-yellow-500/15 text-yellow-300",
  nice_to_have: "bg-white/10 text-slate-400",
};

export function GapAnalysisCard({ analysis, label }: { analysis: GapAnalysis; label?: string }) {
  return (
    <div className="glass-card space-y-4 p-5">
      {label && (
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      )}
      <div className="flex items-center gap-3">
        <span className="text-3xl font-extrabold gradient-text">{analysis.match_percentage}%</span>
        <span className="text-sm text-slate-400">overall match</span>
      </div>

      {analysis.strong_matches.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Strong matches
          </p>
          <ul className="space-y-1">
            {analysis.strong_matches.map((m) => (
              <li key={m} className="flex gap-1 text-sm text-green-400">
                <span>✓</span> {m}
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.gaps.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Gaps to close
          </p>
          <ul className="space-y-2">
            {analysis.gaps.map((g, i) => (
              <li key={i} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${importanceColor[g.importance]}`}
                  >
                    {g.importance.replace("_", " ")}
                  </span>
                  <p className="text-sm font-medium text-slate-100">{g.gap}</p>
                </div>
                <p className="text-xs text-slate-400">{g.how_to_close}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.interview_risks.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Likely interview questions
          </p>
          <ul className="space-y-1">
            {analysis.interview_risks.map((r, i) => (
              <li key={i} className="text-sm text-slate-300">
                • {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
