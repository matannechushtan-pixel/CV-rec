"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { FontOption } from "@/lib/types";

const ACCENT_PRESETS = [
  "#1e3a8a",
  "#6366f1",
  "#10b981",
  "#dc2626",
  "#f59e0b",
  "#0ea5e9",
  "#7c3aed",
  "#374151",
];

export function StyleCustomizer({
  accentColor,
  fontFamily,
  onAccentChange,
  onFontChange,
}: {
  accentColor: string | null;
  fontFamily: string | null;
  onAccentChange: (color: string | null) => void;
  onFontChange: (font: string | null) => void;
}) {
  const [fonts, setFonts] = useState<FontOption[]>([]);

  useEffect(() => {
    api
      .get<FontOption[]>("/cv/font-options")
      .then(({ data }) => setFonts(data))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-4 rounded-xl border border-white/10 bg-white/5 p-3">
      <div>
        <p className="mb-2 text-sm font-medium text-slate-300">Accent colour</p>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => onAccentChange(null)}
            className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
              !accentColor
                ? "bg-indigo-500/20 text-indigo-300 ring-1 ring-indigo-500/50"
                : "bg-white/10 text-slate-300 hover:text-white"
            }`}
          >
            Default
          </button>
          {ACCENT_PRESETS.map((color) => (
            <button
              key={color}
              type="button"
              onClick={() => onAccentChange(color)}
              title={color}
              className={`h-6 w-6 rounded-full border-2 transition-transform hover:scale-110 ${
                accentColor?.toLowerCase() === color.toLowerCase()
                  ? "border-white"
                  : "border-white/20"
              }`}
              style={{ backgroundColor: color }}
            />
          ))}
          <input
            type="color"
            value={accentColor ?? "#1e3a8a"}
            onChange={(e) => onAccentChange(e.target.value)}
            className="h-6 w-8 cursor-pointer rounded border border-white/20 bg-transparent p-0"
            title="Custom colour"
          />
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-slate-300">Font</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          <button
            type="button"
            onClick={() => onFontChange(null)}
            className={`flex-shrink-0 rounded-lg border px-3 py-1.5 text-sm transition-colors ${
              !fontFamily
                ? "border-blue-500 ring-2 ring-blue-500/30 text-white"
                : "border-white/10 text-slate-300 hover:border-white/30"
            }`}
          >
            Default
          </button>
          {fonts.map((font) => (
            <button
              key={font.id}
              type="button"
              onClick={() => onFontChange(font.name)}
              className={`flex-shrink-0 rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                fontFamily === font.name
                  ? "border-blue-500 ring-2 ring-blue-500/30 text-white"
                  : "border-white/10 text-slate-300 hover:border-white/30"
              }`}
              style={{ fontFamily: `'${font.name}', sans-serif` }}
            >
              {font.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
