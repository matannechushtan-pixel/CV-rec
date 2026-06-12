"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Plus, Sparkles, Trash2 } from "lucide-react";
import api from "@/lib/api";
import type {
  CvData,
  CvEducationEntry,
  CvExperienceEntry,
  CvLanguageEntry,
  CvSectionTitles,
  CvVolunteeringEntry,
} from "@/lib/types";

interface BrainstormSummaryResult {
  gemini: string | null;
  claude: string | null;
  gpt: string | null;
}

const BRAINSTORM_LABELS: { key: keyof BrainstormSummaryResult; label: string }[] = [
  { key: "gemini", label: "Gemini 2.0 Flash" },
  { key: "claude", label: "Claude" },
  { key: "gpt", label: "GPT-4o-mini" },
];

const inputClass =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30";

const SECTION_TITLE_FIELDS: { key: keyof CvSectionTitles; label: string; placeholder: string }[] = [
  { key: "experience", label: "Experience", placeholder: "Professional Experience" },
  { key: "education", label: "Education", placeholder: "Education" },
  { key: "skills", label: "Skills", placeholder: "Skills" },
  { key: "languages", label: "Languages", placeholder: "Languages" },
  { key: "hobbies", label: "Hobbies", placeholder: "Hobbies" },
  { key: "military", label: "Military Service", placeholder: "Military Service" },
  { key: "volunteering", label: "Volunteering", placeholder: "Volunteering" },
];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-300">{label}</label>
      {children}
    </div>
  );
}

function RemovableCard({
  onRemove,
  children,
}: {
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="relative space-y-2 rounded-xl border border-white/10 bg-white/5 p-3">
      <button
        type="button"
        onClick={onRemove}
        className="absolute right-2 top-2 text-slate-500 hover:text-red-400"
      >
        <Trash2 className="h-4 w-4" />
      </button>
      {children}
    </div>
  );
}

export function CvContentEditor({
  data,
  onChange,
  cvId,
}: {
  data: CvData;
  onChange: (data: CvData) => void;
  cvId?: string;
}) {
  const [skillsText, setSkillsText] = useState((data.skills ?? []).join(", "));
  const [titlesOpen, setTitlesOpen] = useState(false);
  const [brainstorming, setBrainstorming] = useState(false);
  const [brainstormError, setBrainstormError] = useState<string | null>(null);
  const [brainstormResult, setBrainstormResult] = useState<BrainstormSummaryResult | null>(null);

  async function handleBrainstormSummary() {
    if (!cvId) return;
    setBrainstorming(true);
    setBrainstormError(null);
    try {
      const { data: result } = await api.post<BrainstormSummaryResult>(
        `/cv/${cvId}/brainstorm-summary`
      );
      setBrainstormResult(result);
    } catch {
      setBrainstormError("Failed to brainstorm summaries. Please try again.");
    } finally {
      setBrainstorming(false);
    }
  }

  function useSummary(text: string) {
    update("summary", text);
    setBrainstormResult(null);
  }

  function update<K extends keyof CvData>(key: K, value: CvData[K]) {
    onChange({ ...data, [key]: value });
  }

  function updateSectionTitle(key: keyof CvSectionTitles, value: string) {
    onChange({ ...data, section_titles: { ...data.section_titles, [key]: value } });
  }

  function updateContact(key: keyof NonNullable<CvData["contact"]>, value: string) {
    onChange({ ...data, contact: { ...data.contact, [key]: value } });
  }

  // Education
  function updateEducation(index: number, patch: Partial<CvEducationEntry>) {
    const list = [...(data.education ?? [])];
    list[index] = { ...list[index], ...patch };
    update("education", list);
  }
  function addEducation() {
    update("education", [...(data.education ?? []), {}]);
  }
  function removeEducation(index: number) {
    update("education", (data.education ?? []).filter((_, i) => i !== index));
  }

  // Languages
  function updateLanguage(index: number, patch: Partial<CvLanguageEntry>) {
    const list = [...(data.languages ?? [])];
    list[index] = { ...list[index], ...patch };
    update("languages", list);
  }
  function addLanguage() {
    update("languages", [...(data.languages ?? []), {}]);
  }
  function removeLanguage(index: number) {
    update("languages", (data.languages ?? []).filter((_, i) => i !== index));
  }

  // Experience
  function updateExperience(index: number, patch: Partial<CvExperienceEntry>) {
    const list = [...(data.experience ?? [])];
    list[index] = { ...list[index], ...patch };
    update("experience", list);
  }
  function addExperience() {
    update("experience", [...(data.experience ?? []), { bullets: [] }]);
  }
  function removeExperience(index: number) {
    update("experience", (data.experience ?? []).filter((_, i) => i !== index));
  }

  // Volunteering
  function updateVolunteering(index: number, patch: Partial<CvVolunteeringEntry>) {
    const list = [...(data.volunteering ?? [])];
    list[index] = { ...list[index], ...patch };
    update("volunteering", list);
  }
  function addVolunteering() {
    update("volunteering", [...(data.volunteering ?? []), {}]);
  }
  function removeVolunteering(index: number) {
    update("volunteering", (data.volunteering ?? []).filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-5">
      {/* Section Titles */}
      <div className="rounded-xl border border-white/10 bg-white/5">
        <button
          type="button"
          onClick={() => setTitlesOpen((o) => !o)}
          className="flex w-full items-center justify-between px-3 py-2 text-sm font-semibold text-white"
        >
          Section Titles
          {titlesOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {titlesOpen && (
          <div className="grid gap-2 border-t border-white/10 p-3 sm:grid-cols-2">
            {SECTION_TITLE_FIELDS.map((field) => (
              <Field key={field.key} label={field.label}>
                <input
                  className={inputClass}
                  placeholder={field.placeholder}
                  value={data.section_titles?.[field.key] ?? ""}
                  onChange={(e) => updateSectionTitle(field.key, e.target.value)}
                />
              </Field>
            ))}
          </div>
        )}
      </div>

      <Field label="Full name">
        <input
          className={inputClass}
          value={data.full_name ?? ""}
          onChange={(e) => update("full_name", e.target.value)}
        />
      </Field>

      <Field label="Summary">
        <textarea
          className={inputClass}
          rows={3}
          value={data.summary ?? ""}
          onChange={(e) => update("summary", e.target.value)}
        />
        {cvId && (
          <button
            type="button"
            onClick={handleBrainstormSummary}
            disabled={brainstorming}
            className="btn-secondary mt-2 !px-2 !py-1 text-xs"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {brainstorming ? "Brainstorming…" : "Brainstorm 3 versions"}
          </button>
        )}
        {brainstormError && <p className="mt-2 text-sm text-red-400">{brainstormError}</p>}
        {brainstormResult && (
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {BRAINSTORM_LABELS.map(({ key, label }) => {
              const text = brainstormResult[key];
              return (
                <div key={key} className="space-y-2 rounded-xl border border-white/10 bg-white/5 p-3">
                  <h5 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {label}
                  </h5>
                  {text ? (
                    <>
                      <p className="text-sm text-slate-200">{text}</p>
                      <button
                        type="button"
                        onClick={() => useSummary(text)}
                        className="btn-secondary !px-2 !py-1 text-xs"
                      >
                        Use this one
                      </button>
                    </>
                  ) : (
                    <p className="text-sm text-slate-500">Unavailable</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Field>

      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Location">
          <input
            className={inputClass}
            value={data.contact?.location ?? ""}
            onChange={(e) => updateContact("location", e.target.value)}
          />
        </Field>
        <Field label="Phone">
          <input
            className={inputClass}
            value={data.contact?.phone ?? ""}
            onChange={(e) => updateContact("phone", e.target.value)}
          />
        </Field>
        <Field label="Email">
          <input
            className={inputClass}
            value={data.contact?.email ?? ""}
            onChange={(e) => updateContact("email", e.target.value)}
          />
        </Field>
      </div>

      <Field label="Skills (comma separated)">
        <input
          className={inputClass}
          value={skillsText}
          onChange={(e) => {
            setSkillsText(e.target.value);
            update(
              "skills",
              e.target.value.split(",").map((s) => s.trim()).filter(Boolean)
            );
          }}
        />
      </Field>

      <Field label="Hobbies">
        <input
          className={inputClass}
          value={data.hobbies ?? ""}
          onChange={(e) => update("hobbies", e.target.value)}
        />
      </Field>

      {/* Education */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-white">Education</h4>
          <button type="button" onClick={addEducation} className="btn-secondary !px-2 !py-1 text-xs">
            <Plus className="h-3.5 w-3.5" /> Add
          </button>
        </div>
        {(data.education ?? []).map((edu, i) => (
          <RemovableCard key={i} onRemove={() => removeEducation(i)}>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                className={inputClass}
                placeholder="Institution"
                value={edu.institution ?? ""}
                onChange={(e) => updateEducation(i, { institution: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Degree"
                value={edu.degree ?? ""}
                onChange={(e) => updateEducation(i, { degree: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Dates"
                value={edu.dates ?? ""}
                onChange={(e) => updateEducation(i, { dates: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Notes"
                value={edu.notes ?? ""}
                onChange={(e) => updateEducation(i, { notes: e.target.value })}
              />
            </div>
          </RemovableCard>
        ))}
      </div>

      {/* Languages */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-white">Languages</h4>
          <button type="button" onClick={addLanguage} className="btn-secondary !px-2 !py-1 text-xs">
            <Plus className="h-3.5 w-3.5" /> Add
          </button>
        </div>
        {(data.languages ?? []).map((lang, i) => (
          <RemovableCard key={i} onRemove={() => removeLanguage(i)}>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                className={inputClass}
                placeholder="Language"
                value={lang.name ?? ""}
                onChange={(e) => updateLanguage(i, { name: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Level"
                value={lang.level ?? ""}
                onChange={(e) => updateLanguage(i, { level: e.target.value })}
              />
            </div>
          </RemovableCard>
        ))}
      </div>

      {/* Experience */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-white">Experience</h4>
          <button type="button" onClick={addExperience} className="btn-secondary !px-2 !py-1 text-xs">
            <Plus className="h-3.5 w-3.5" /> Add
          </button>
        </div>
        {(data.experience ?? []).map((exp, i) => (
          <RemovableCard key={i} onRemove={() => removeExperience(i)}>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                className={inputClass}
                placeholder="Company"
                value={exp.company ?? ""}
                onChange={(e) => updateExperience(i, { company: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Location"
                value={exp.location ?? ""}
                onChange={(e) => updateExperience(i, { location: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Role"
                value={exp.role ?? ""}
                onChange={(e) => updateExperience(i, { role: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Dates"
                value={exp.dates ?? ""}
                onChange={(e) => updateExperience(i, { dates: e.target.value })}
              />
            </div>
            <textarea
              className={inputClass}
              rows={3}
              placeholder="One bullet point per line"
              value={(exp.bullets ?? []).join("\n")}
              onChange={(e) =>
                updateExperience(i, {
                  bullets: e.target.value.split("\n").map((b) => b.trim()).filter(Boolean),
                })
              }
            />
          </RemovableCard>
        ))}
      </div>

      {/* Military */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-white">Military Service (optional)</h4>
        <div className="grid gap-2 sm:grid-cols-3">
          <input
            className={inputClass}
            placeholder="Unit"
            value={data.military?.unit ?? ""}
            onChange={(e) => update("military", { ...data.military, unit: e.target.value })}
          />
          <input
            className={inputClass}
            placeholder="Role"
            value={data.military?.role ?? ""}
            onChange={(e) => update("military", { ...data.military, role: e.target.value })}
          />
          <input
            className={inputClass}
            placeholder="Dates"
            value={data.military?.dates ?? ""}
            onChange={(e) => update("military", { ...data.military, dates: e.target.value })}
          />
        </div>
        <textarea
          className={inputClass}
          rows={2}
          placeholder="One bullet point per line"
          value={(data.military?.bullets ?? []).join("\n")}
          onChange={(e) =>
            update("military", {
              ...data.military,
              bullets: e.target.value.split("\n").map((b) => b.trim()).filter(Boolean),
            })
          }
        />
      </div>

      {/* Volunteering */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-white">Volunteering (optional)</h4>
          <button type="button" onClick={addVolunteering} className="btn-secondary !px-2 !py-1 text-xs">
            <Plus className="h-3.5 w-3.5" /> Add
          </button>
        </div>
        {(data.volunteering ?? []).map((v, i) => (
          <RemovableCard key={i} onRemove={() => removeVolunteering(i)}>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                className={inputClass}
                placeholder="Organization"
                value={v.org ?? ""}
                onChange={(e) => updateVolunteering(i, { org: e.target.value })}
              />
              <input
                className={inputClass}
                placeholder="Year"
                value={v.year ?? ""}
                onChange={(e) => updateVolunteering(i, { year: e.target.value })}
              />
            </div>
            <input
              className={inputClass}
              placeholder="Description"
              value={v.description ?? ""}
              onChange={(e) => updateVolunteering(i, { description: e.target.value })}
            />
          </RemovableCard>
        ))}
      </div>
    </div>
  );
}
