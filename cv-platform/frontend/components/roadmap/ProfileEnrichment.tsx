"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Sparkles, ChevronDown, ChevronUp } from "lucide-react";

interface EnrichResult {
  behavioral_profile: Record<string, unknown>;
  writing_style: Record<string, unknown>;
}

export function ProfileEnrichment() {
  const [open, setOpen] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnrichResult | null>(null);

  useEffect(() => {
    api
      .get<string[]>("/profile/enrich-questions")
      .then(({ data }) => {
        setQuestions(data);
        setAnswers(data.map(() => ""));
      })
      .catch(() => {});
  }, []);

  async function handleSubmit() {
    setWorking(true);
    setError(null);
    try {
      const { data } = await api.post<EnrichResult>("/profile/enrich", { answers });
      setResult(data);
    } catch {
      setError("Failed to save your answers. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  const allAnswered = answers.every((a) => a.trim().length > 0);

  return (
    <div className="glass-card p-5">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            Personalize Your Profile
          </h2>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {open && (
        <div className="mt-4 space-y-4">
          <p className="text-sm text-slate-400">
            Answer a few quick questions so we can tailor your CVs and cover letters to sound
            like you.
          </p>

          {questions.map((q, i) => (
            <div key={i}>
              <label className="mb-1 block text-sm font-medium text-slate-300">{q}</label>
              <textarea
                value={answers[i] ?? ""}
                onChange={(e) =>
                  setAnswers((a) => a.map((val, idx) => (idx === i ? e.target.value : val)))
                }
                rows={3}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
          ))}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={working || !allAnswered}
            className="btn-primary"
          >
            {working ? "Saving…" : "Save profile"}
          </button>

          {result && (
            <p className="text-sm text-emerald-400">
              Saved! Your CVs and cover letters will now better reflect your style.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
