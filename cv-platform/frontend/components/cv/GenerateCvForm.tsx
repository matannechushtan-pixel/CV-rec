"use client";

import { useState } from "react";
import api from "@/lib/api";
import type { CV } from "@/lib/types";
import { FontPicker } from "@/components/cv/FontPicker";

const LANGUAGES = ["English", "Hebrew", "Spanish", "French", "German", "Arabic"];

export function GenerateCvForm({ onCreated }: { onCreated: (cv: CV) => void }) {
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("English");
  const [fontId, setFontId] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!description.trim()) return;
    setWorking(true);
    setError(null);
    try {
      const { data } = await api.post<CV>("/cv/generate", {
        description,
        language,
        font_id: fontId,
      });
      onCreated(data);
      setDescription("");
    } catch {
      setError("Failed to generate CV. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-300">
          Describe your background
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={8}
          placeholder="Tell us about your experience, skills, education, and what kind of role you're after…"
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
        />
      </div>

      <div className="flex flex-col gap-2 sm:max-w-xs">
        <label className="text-sm font-medium text-slate-300">Language</label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang} value={lang} className="bg-slate-900">
              {lang}
            </option>
          ))}
        </select>
      </div>

      <FontPicker value={fontId} onChange={setFontId} />

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={working || !description.trim()}
        className="btn-primary"
      >
        {working ? "Generating…" : "Generate CV"}
      </button>
    </div>
  );
}
