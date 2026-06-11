"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CvFont } from "@/lib/types";

export function FontPicker({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (fontId: string) => void;
}) {
  const [fonts, setFonts] = useState<CvFont[]>([]);

  useEffect(() => {
    api
      .get<CvFont[]>("/cv/fonts")
      .then(({ data }) => setFonts(data))
      .catch(() => {});
  }, []);

  if (!fonts.length) return null;

  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-300">CV font</label>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
        {fonts.map((font) => (
          <button
            key={font.id}
            type="button"
            onClick={() => onChange(font.id)}
            className={`rounded-xl border px-3 py-2 text-left text-sm transition-colors ${
              value === font.id
                ? "border-blue-500/50 bg-blue-500/10 text-blue-200"
                : "border-white/10 bg-white/5 text-slate-300 hover:border-white/20"
            }`}
            style={{ fontFamily: font.css_family }}
          >
            {font.name}
          </button>
        ))}
      </div>
    </div>
  );
}
