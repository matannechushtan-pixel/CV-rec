"use client";

import { useState } from "react";
import api from "@/lib/api";
import type { InterviewQuestion } from "@/lib/types";
import { MessageSquare, Sparkles, ChevronDown } from "lucide-react";

export default function InterviewPrepPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [questions, setQuestions] = useState<InterviewQuestion[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setExpanded(new Set());
    try {
      const { data } = await api.post<{ questions: InterviewQuestion[] }>("/interview/questions", {
        job_description: jobDescription || undefined,
      });
      setQuestions(data.questions);
    } catch {
      setError("Failed to generate questions. Make sure you've uploaded a CV.");
    } finally {
      setLoading(false);
    }
  }

  function toggle(i: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  const behavioral = questions?.filter((q) => q.type === "behavioral") ?? [];
  const technical = questions?.filter((q) => q.type === "technical") ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Interview Prep
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          AI-generated interview questions tailored to your CV, with STAR-method guidance.
        </p>
      </div>

      <div className="glass-card space-y-3 p-5">
        <label className="block text-sm font-medium text-slate-300">
          Job description or target role (optional)
        </label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={4}
          placeholder="Paste a job description, or leave blank to use your profile's target role…"
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
        />
        <button onClick={handleGenerate} disabled={loading} className="btn-primary">
          <Sparkles className="h-4 w-4" />
          {loading ? "Generating…" : "Generate questions"}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {questions && (
        <div className="space-y-8">
          <QuestionGroup
            title="Behavioral questions"
            items={behavioral}
            expanded={expanded}
            toggle={toggle}
            offset={0}
          />
          <QuestionGroup
            title="Technical questions"
            items={technical}
            expanded={expanded}
            toggle={toggle}
            offset={behavioral.length}
          />
        </div>
      )}
    </div>
  );
}

function QuestionGroup({
  title,
  items,
  expanded,
  toggle,
  offset,
}: {
  title: string;
  items: InterviewQuestion[];
  expanded: Set<number>;
  toggle: (i: number) => void;
  offset: number;
}) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      {items.map((q, i) => {
        const idx = offset + i;
        const isOpen = expanded.has(idx);
        return (
          <div key={idx} className="glass-card overflow-hidden">
            <button
              onClick={() => toggle(idx)}
              className="flex w-full items-start gap-3 p-4 text-left"
            >
              <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-blue-400" />
              <span className="flex-1 text-sm font-medium text-white">{q.question}</span>
              <ChevronDown
                className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </button>
            {isOpen && (
              <div className="border-t border-white/10 px-4 py-3 text-sm text-slate-300">
                {q.guidance}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
