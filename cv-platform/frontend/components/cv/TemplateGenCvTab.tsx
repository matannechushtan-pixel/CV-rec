"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV, CvTemplate } from "@/lib/types";
import { TemplateField } from "@/components/cv/TemplatePicker";
import { PhotoUpload } from "@/components/cv/PhotoUpload";

const LANGUAGES = ["English", "Hebrew", "Spanish", "French", "German", "Arabic"];

export function TemplateGenCvTab({ onGenerated }: { onGenerated: (cv: CV) => void }) {
  const [templates, setTemplates] = useState<CvTemplate[]>([]);
  const [selected, setSelected] = useState<CvTemplate | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [language, setLanguage] = useState("English");
  const [cvTemplateId, setCvTemplateId] = useState("classic_blue_photo");
  const [photo, setPhoto] = useState<string | null>(null);
  const [accentColor, setAccentColor] = useState<string | null>(null);
  const [fontFamily, setFontFamily] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CvTemplate[]>("/cv/templates")
      .then(({ data }) => setTemplates(data))
      .catch(() => {});
  }, []);

  // When photo changes, sync template variant
  useEffect(() => {
    if (photo && cvTemplateId.endsWith("_nophoto")) {
      setCvTemplateId(cvTemplateId.replace("_nophoto", "_photo"));
    } else if (!photo && cvTemplateId.endsWith("_photo")) {
      setCvTemplateId(cvTemplateId.replace("_photo", "_nophoto"));
    }
  }, [photo]);

  function selectTemplate(tpl: CvTemplate) {
    setSelected(tpl);
    setValues({});
  }

  async function handleSubmit() {
    if (!selected) return;
    setWorking(true);
    setError(null);
    try {
      const { data } = await api.post<CV>("/cv/generate/from-template", {
        template_id: selected.id,
        answers: { profession: selected.label, ...values },
        language,
        version_name: `${selected.label} CV`,
        cv_template_id: cvTemplateId,
        photo_base64: photo ?? undefined,
        accent_color: accentColor ?? undefined,
        font_family: fontFamily ?? undefined,
      });
      onGenerated(data);
      setSelected(null);
      setValues({});
      setPhoto(null);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Generation failed. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  if (!selected) {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {templates.map((tpl) => (
          <button
            key={tpl.id}
            type="button"
            onClick={() => selectTemplate(tpl)}
            className="glass-card p-5 text-left transition-colors hover:border-blue-500/40"
          >
            <h3 className="font-semibold text-white">{tpl.label}</h3>
            <p className="mt-1 text-xs text-slate-400">
              {tpl.fields.length} fields · structured profile form
            </p>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={() => setSelected(null)}
        className="text-sm text-slate-400 hover:text-slate-200"
      >
        ← Choose a different profession
      </button>

      <h3 className="text-lg font-semibold text-white">{selected.label}</h3>

      <div className="grid gap-3 sm:grid-cols-2">
        {selected.fields.map((field) => (
          <div key={field.name} className={field.type === "textarea" ? "sm:col-span-2" : ""}>
            <label className="mb-1 block text-sm font-medium text-slate-300">{field.label}</label>
            {field.type === "textarea" ? (
              <textarea
                value={values[field.name] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))}
                rows={4}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            ) : (
              <input
                value={values[field.name] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            )}
          </div>
        ))}
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

      <button type="button" onClick={handleSubmit} disabled={working} className="btn-primary">
        {working ? "Generating…" : "Generate CV"}
      </button>
    </div>
  );
}
