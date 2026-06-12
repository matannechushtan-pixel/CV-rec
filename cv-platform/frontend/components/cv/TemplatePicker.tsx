"use client";

import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import type { CvTemplateInfo } from "@/lib/types";
import { Check, ChevronDown, ChevronUp, Image as ImageIcon, ImageOff } from "lucide-react";
import { StyleCustomizer } from "@/components/cv/StyleCustomizer";

type PhotoFilter = "all" | "photo" | "nophoto";

const FILTERS: { id: PhotoFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "photo", label: "With Photo" },
  { id: "nophoto", label: "Without Photo" },
];

function designLabel(design: string): string {
  return design
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function TemplatePicker({
  selectedId,
  onSelect,
  onContinue,
}: {
  selectedId: string | null;
  onSelect: (template: CvTemplateInfo) => void;
  onContinue?: () => void;
}) {
  const [templates, setTemplates] = useState<CvTemplateInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<PhotoFilter>("all");

  useEffect(() => {
    api
      .get<CvTemplateInfo[]>("/cv/design-templates")
      .then(({ data }) => setTemplates(data))
      .catch(() => setError("Failed to load templates."))
      .finally(() => setLoading(false));
  }, []);

  const groups = useMemo(() => {
    const byDesign = new Map<string, CvTemplateInfo[]>();
    for (const tpl of templates) {
      const list = byDesign.get(tpl.design) ?? [];
      list.push(tpl);
      byDesign.set(tpl.design, list);
    }
    return Array.from(byDesign.entries());
  }, [templates]);

  const selected = templates.find((t) => t.id === selectedId) ?? null;

  function visible(tpl: CvTemplateInfo): boolean {
    if (filter === "photo") return tpl.has_photo;
    if (filter === "nophoto") return !tpl.has_photo;
    return true;
  }

  if (loading) {
    return <p className="text-sm text-slate-400">Loading templates…</p>;
  }

  if (error) {
    return <p className="text-sm text-red-400">{error}</p>;
  }

  return (
    <div className="space-y-5">
      <div className="inline-flex flex-wrap gap-1 rounded-xl border border-white/10 bg-white/5 p-1">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFilter(f.id)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f.id
                ? "bg-indigo-500/20 text-indigo-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {groups.map(([design, items]) => {
          const shown = items.filter(visible);
          if (shown.length === 0) return null;
          return (
            <div key={design} className="space-y-2">
              <h3 className="text-sm font-semibold text-white">{designLabel(design)}</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {shown.map((tpl) => {
                  const isSelected = tpl.id === selectedId;
                  return (
                    <button
                      key={tpl.id}
                      type="button"
                      onClick={() => onSelect(tpl)}
                      className={`group relative text-left rounded-2xl border p-4 transition-all hover:scale-[1.02] ${
                        isSelected
                          ? "border-indigo-500 ring-2 ring-indigo-500/50 bg-indigo-500/10"
                          : "border-white/10 bg-white/5 hover:border-indigo-500/40"
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-white">
                          <Check className="h-3.5 w-3.5" />
                        </div>
                      )}
                      <div className="flex items-center gap-1.5">
                        {tpl.preview_colors.map((color, i) => (
                          <span
                            key={i}
                            className="h-4 w-4 rounded-full border border-white/20"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <p className="mt-2 flex items-center gap-1.5 text-sm font-semibold text-white">
                        {tpl.has_photo ? (
                          <ImageIcon className="h-3.5 w-3.5 text-slate-400" />
                        ) : (
                          <ImageOff className="h-3.5 w-3.5 text-slate-400" />
                        )}
                        {tpl.name}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">{tpl.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {onContinue && (
        <div className="flex items-center justify-between gap-3 border-t border-white/10 pt-4">
          <p className="text-sm text-slate-400">
            {selected ? (
              <>
                Selected: <span className="font-semibold text-white">{selected.name}</span>{" "}
                {selected.has_photo ? (
                  <span className="ml-1 rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-300">
                    With photo
                  </span>
                ) : (
                  <span className="ml-1 rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-300">
                    No photo
                  </span>
                )}
              </>
            ) : (
              "Choose a template to continue"
            )}
          </p>
          <button
            type="button"
            onClick={onContinue}
            disabled={!selected}
            className="btn-primary"
          >
            Continue →
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Compact field that shows the currently selected CV design and lets the
 * user expand a TemplatePicker to change it.
 */
export function TemplateField({
  selectedId,
  onSelect,
  accentColor,
  fontFamily,
  onAccentChange,
  onFontChange,
}: {
  selectedId: string;
  onSelect: (templateId: string) => void;
  accentColor?: string | null;
  fontFamily?: string | null;
  onAccentChange?: (color: string | null) => void;
  onFontChange?: (font: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [templates, setTemplates] = useState<CvTemplateInfo[]>([]);

  useEffect(() => {
    api
      .get<CvTemplateInfo[]>("/cv/design-templates")
      .then(({ data }) => setTemplates(data))
      .catch(() => {});
  }, []);

  const selected = templates.find((t) => t.id === selectedId);

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition-colors hover:border-indigo-500/40"
      >
        <span>
          CV Template:{" "}
          <span className="font-semibold text-white">{selected?.name ?? "Loading…"}</span>
        </span>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {open && (
        <>
          <TemplatePicker
            selectedId={selectedId}
            onSelect={(tpl) => {
              onSelect(tpl.id);
              setOpen(false);
            }}
          />
          {onAccentChange && onFontChange && (
            <StyleCustomizer
              accentColor={accentColor ?? null}
              fontFamily={fontFamily ?? null}
              onAccentChange={onAccentChange}
              onFontChange={onFontChange}
            />
          )}
        </>
      )}
    </div>
  );
}
