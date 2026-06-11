"use client";

import { useState } from "react";
import api from "@/lib/api";
import type { CV } from "@/lib/types";
import { FontPicker } from "@/components/cv/FontPicker";

const LANGUAGES = ["English", "Hebrew", "Spanish", "French", "German", "Arabic"];

interface ImproveResponse {
  cv: CV;
  original_structured_data: Record<string, unknown>;
}

function summaryOf(data: Record<string, unknown> | null | undefined): string {
  return (data?.summary as string) ?? "";
}

function skillsOf(data: Record<string, unknown> | null | undefined): string[] {
  return (data?.skills as string[]) ?? [];
}

export function ImproveCvForm({ onCreated }: { onCreated: (cv: CV) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("English");
  const [fontId, setFontId] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImproveResponse | null>(null);

  async function handleSubmit() {
    if (!file) return;
    setWorking(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<ImproveResponse>(
        `/cv/improve-uploaded?language=${encodeURIComponent(language)}${
          fontId ? `&font_id=${encodeURIComponent(fontId)}` : ""
        }`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(data);
      onCreated(data.cv);
    } catch {
      setError("Failed to improve CV. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-300">CV file (PDF or DOCX)</label>
        <input
          type="file"
          accept=".pdf,.docx,.doc"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-600 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-blue-500"
        />
      </div>

      <div className="flex flex-col gap-2 sm:max-w-xs">
        <label className="text-sm font-medium text-slate-300">Target language</label>
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

      <button type="button" onClick={handleSubmit} disabled={working || !file} className="btn-primary">
        {working ? "Improving…" : "Improve & Translate"}
      </button>

      {result && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="glass-card space-y-2 p-4">
            <h4 className="text-sm font-semibold text-slate-300">Original</h4>
            <p className="text-sm text-slate-400">{summaryOf(result.original_structured_data) || "—"}</p>
            <p className="text-xs text-slate-500">
              Skills: {skillsOf(result.original_structured_data).join(", ") || "—"}
            </p>
          </div>
          <div className="glass-card space-y-2 border-emerald-500/20 bg-emerald-500/5 p-4">
            <h4 className="text-sm font-semibold text-emerald-300">Improved</h4>
            <p className="text-sm text-slate-200">{summaryOf(result.cv.structured_data) || "—"}</p>
            <p className="text-xs text-slate-400">
              Skills: {skillsOf(result.cv.structured_data).join(", ") || "—"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
