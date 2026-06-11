"use client";

import type { CV } from "@/lib/types";
import { cn } from "@/lib/utils";

export function CVVersionManager({
  cvs,
  onSelect,
  onActivate,
  activatingId,
  renderActions,
}: {
  cvs: CV[];
  onSelect?: (cv: CV) => void;
  onActivate?: (cv: CV) => void;
  activatingId?: string | null;
  renderActions?: (cv: CV) => React.ReactNode;
}) {
  if (!cvs.length) {
    return <p className="text-sm text-slate-400">No CVs uploaded yet.</p>;
  }

  return (
    <ul className="space-y-3">
      {cvs.map((cv) => (
        <li
          key={cv.id}
          onClick={() => onSelect?.(cv)}
          className={cn(
            "glass-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between",
            onSelect && "cursor-pointer"
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate text-sm font-medium text-white">
                {cv.version_name ?? "Untitled CV"}
              </p>
              {cv.is_base && (
                <span className="shrink-0 rounded-full bg-gradient-to-r from-blue-600/30 to-indigo-600/30 px-2 py-0.5 text-xs font-medium text-blue-300">
                  Active
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500">
              {new Date(cv.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-2">
            {!cv.is_base && onActivate && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onActivate(cv);
                }}
                disabled={activatingId === cv.id}
                className="btn-secondary !px-3 !py-1.5 text-xs"
              >
                {activatingId === cv.id ? "Setting…" : "Set active"}
              </button>
            )}
            {renderActions?.(cv)}
          </div>
        </li>
      ))}
    </ul>
  );
}
