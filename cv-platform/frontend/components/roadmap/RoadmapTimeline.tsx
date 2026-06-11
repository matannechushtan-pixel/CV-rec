import type { RoadmapStep } from "@/lib/types";

export function RoadmapTimeline({ steps }: { steps: RoadmapStep[] }) {
  const sorted = [...steps].sort((a, b) => a.priority - b.priority);
  return (
    <ol className="relative ml-3 space-y-6 border-l border-white/10">
      {sorted.map((step, i) => (
        <li key={i} className="ml-6">
          <span className="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-300 ring-4 ring-navy-light">
            {step.priority}
          </span>
          <h3 className="font-semibold text-white">{step.area}</h3>
          <p className="mt-0.5 text-sm text-slate-300">{step.action}</p>
          <p className="mt-1 text-xs text-slate-500">
            {step.resource} · ~{step.estimated_weeks}w
          </p>
        </li>
      ))}
    </ol>
  );
}
