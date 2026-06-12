"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV } from "@/lib/types";
import { TemplateField } from "@/components/cv/TemplatePicker";
import { PhotoUpload } from "@/components/cv/PhotoUpload";

const LANGUAGES = ["English", "Hebrew", "Spanish", "French", "German", "Arabic"];

export function UploadImproveCvTab({ onGenerated }: { onGenerated: (cv: CV) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("English");
  const [cvTemplateId, setCvTemplateId] = useState("classic_blue_photo");
  const [photo, setPhoto] = useState<string | null>(null);
  const [accentColor, setAccentColor] = useState<string | null>(null);
  const [fontFamily, setFontFamily] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // When photo changes, sync template variant
  useEffect(() => {
    if (photo && cvTemplateId.endsWith("_nophoto")) {
      setCvTemplateId(cvTemplateId.replace("_nophoto", "_photo"));
    } else if (!photo && cvTemplateId.endsWith("_photo")) {
      setCvTemplateId(cvTemplateId.replace("_photo", "_nophoto"));
    }
  }, [photo]);

  async function handleSubmit() {
    if (!file) return;
    setWorking(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      if (photo) form.append("photo_base64", photo);
      if (accentColor) form.append("accent_color", accentColor);
      if (fontFamily) form.append("font_family", fontFamily);
      const { data } = await api.post<CV>(
        `/cv/generate/improve-uploaded?language=${encodeURIComponent(language)}&cv_template_id=${encodeURIComponent(cvTemplateId)}`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      onGenerated(data);
      setFile(null);
      setPhoto(null);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Generation failed. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-300">CV file (PDF or DOCX)</label>
        <div className="flex items-center gap-3">
          <label className="btn-secondary cursor-pointer">
            Choose file
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="hidden"
            />
          </label>
          <span className="text-sm text-slate-400">{file ? file.name : "No file selected"}</span>
        </div>
      </div>

      <PhotoUpload value={photo} onChange={setPhoto} />

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

      <TemplateField
        selectedId={cvTemplateId}
        onSelect={setCvTemplateId}
        accentColor={accentColor}
        fontFamily={fontFamily}
        onAccentChange={setAccentColor}
        onFontChange={setFontFamily}
      />

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button type="button" onClick={handleSubmit} disabled={working || !file} className="btn-primary">
        {working ? "Improving…" : "Improve & Translate"}
      </button>
    </div>
  );
}
