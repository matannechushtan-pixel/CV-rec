"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV } from "@/lib/types";
import { TemplateField } from "@/components/cv/TemplatePicker";
import { PhotoUpload } from "@/components/cv/PhotoUpload";

const LANGUAGES = ["English", "Hebrew", "Spanish", "French", "German", "Arabic"];

export function DescribeCvTab({ onGenerated }: { onGenerated: (cv: CV) => void }) {
  const [description, setDescription] = useState("");
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
    if (!description.trim()) return;
    setWorking(true);
    setError(null);
    try {
      const { data } = await api.post<CV>("/cv/generate/from-description", {
        description,
        language,
        cv_template_id: cvTemplateId,
        photo_base64: photo ?? undefined,
        accent_color: accentColor ?? undefined,
        font_family: fontFamily ?? undefined,
      });
      onGenerated(data);
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

      <PhotoUpload value={photo} onChange={setPhoto} />

      <TemplateField
        selectedId={cvTemplateId}
        onSelect={setCvTemplateId}
        accentColor={accentColor}
        fontFamily={fontFamily}
        onAccentChange={setAccentColor}
        onFontChange={setFontFamily}
      />

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
