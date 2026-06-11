"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { CV, GapAnalysis } from "@/lib/types";
import { CVUploader } from "@/components/cv/CVUploader";
import { CVVersionManager } from "@/components/cv/CVVersionManager";
import { GenerateCvForm } from "@/components/cv/GenerateCvForm";
import { TemplateCvForm } from "@/components/cv/TemplateCvForm";
import { ImproveCvForm } from "@/components/cv/ImproveCvForm";
import { GapAnalysisCard } from "@/components/roadmap/GapAnalysisCard";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { Sparkles, Target, Download, FileText, Trash2, Check, X } from "lucide-react";

type CreateMode = "upload" | "describe" | "template" | "improve";

const CREATE_MODES: { id: CreateMode; label: string }[] = [
  { id: "upload", label: "Upload CV" },
  { id: "describe", label: "Describe & Generate" },
  { id: "template", label: "Fill a Template" },
  { id: "improve", label: "Upload & Improve" },
];

type ModalState =
  | { type: "tailor"; cv: CV }
  | { type: "gap"; cv: CV }
  | null;

export default function CVPage() {
  const [cvs, setCvs] = useState<CV[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [modal, setModal] = useState<ModalState>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [working, setWorking] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [tailoredText, setTailoredText] = useState<string | null>(null);
  const [gapResult, setGapResult] = useState<GapAnalysis | null>(null);

  const [createMode, setCreateMode] = useState<CreateMode>("upload");

  async function loadCvs() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<CV[]>("/cv/");
      setCvs(data);
    } catch {
      setError("Failed to load CVs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCvs();
  }, []);

  async function handleActivate(cv: CV) {
    setActivatingId(cv.id);
    try {
      await api.patch<CV>(`/cv/${cv.id}/activate`);
      await loadCvs();
    } catch {
      setError("Failed to set active CV.");
    } finally {
      setActivatingId(null);
    }
  }

  async function handleDelete(cv: CV) {
    setDeletingId(cv.id);
    try {
      await api.delete(`/cv/${cv.id}`);
      await loadCvs();
      setToast("CV deleted");
    } catch {
      setError("Failed to delete CV.");
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  }

  function openModal(type: "tailor" | "gap", cv: CV) {
    setModal({ type, cv });
    setJobDescription("");
    setModalError(null);
    setTailoredText(null);
    setGapResult(null);
  }

  function closeModal() {
    setModal(null);
  }

  async function handleSubmitModal() {
    if (!modal || !jobDescription.trim()) return;
    setWorking(true);
    setModalError(null);
    try {
      if (modal.type === "tailor") {
        const { data } = await api.post<{ tailored_text: string }>(
          `/cv/${modal.cv.id}/tailor`,
          { job_description: jobDescription }
        );
        setTailoredText(data.tailored_text);
      } else {
        const { data } = await api.post<GapAnalysis>(`/cv/${modal.cv.id}/gap-analysis`, {
          job_description: jobDescription,
        });
        setGapResult(data);
      }
    } catch {
      setModalError(
        modal.type === "tailor" ? "Failed to tailor CV." : "Failed to run gap analysis."
      );
    } finally {
      setWorking(false);
    }
  }

  function handleCreated() {
    setToast("CV created");
    loadCvs();
  }

  function downloadTailored() {
    if (!tailoredText || !modal) return;
    const blob = new Blob([tailoredText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(modal.cv.version_name ?? "cv").replace(/\.[^.]+$/, "")}-tailored.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">My CVs</h1>
        <p className="mt-2 text-sm text-slate-400">
          Upload, manage, and tailor your CV versions to specific roles.
        </p>
      </div>

      <div className="space-y-4">
        <div className="inline-flex flex-wrap gap-1 rounded-xl border border-white/10 bg-white/5 p-1">
          {CREATE_MODES.map((mode) => (
            <button
              key={mode.id}
              type="button"
              onClick={() => setCreateMode(mode.id)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                createMode === mode.id
                  ? "bg-blue-500/20 text-blue-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {createMode === "upload" && <CVUploader onUploaded={loadCvs} />}
        {createMode === "describe" && (
          <div className="glass-card p-5">
            <GenerateCvForm onCreated={handleCreated} />
          </div>
        )}
        {createMode === "template" && (
          <div className="glass-card p-5">
            <TemplateCvForm onCreated={handleCreated} />
          </div>
        )}
        {createMode === "improve" && (
          <div className="glass-card p-5">
            <ImproveCvForm onCreated={handleCreated} />
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <CVVersionManager
          cvs={cvs}
          onActivate={handleActivate}
          activatingId={activatingId}
          renderActions={(cv) => (
            <>
              {cv.pdf_url && (
                <a
                  href={cv.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="btn-secondary !px-3 !py-1.5 text-xs"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Download PDF
                </a>
              )}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  openModal("tailor", cv);
                }}
                className="btn-secondary !px-3 !py-1.5 text-xs"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Tailor to Job
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  openModal("gap", cv);
                }}
                className="btn-secondary !px-3 !py-1.5 text-xs"
              >
                <Target className="h-3.5 w-3.5" />
                Gap Analysis
              </button>
              {confirmDeleteId === cv.id ? (
                <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-2 py-1 text-xs text-red-300">
                  <span>Delete this CV?</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(cv);
                    }}
                    disabled={deletingId === cv.id}
                    className="flex items-center gap-1 rounded-lg bg-red-500/20 px-2 py-1 font-medium text-red-200 hover:bg-red-500/30"
                  >
                    <Check className="h-3 w-3" />
                    {deletingId === cv.id ? "Deleting…" : "Yes"}
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirmDeleteId(null);
                    }}
                    className="flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1 font-medium text-slate-300 hover:bg-white/10"
                  >
                    <X className="h-3 w-3" />
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfirmDeleteId(cv.id);
                  }}
                  className="btn-secondary !px-3 !py-1.5 text-xs !text-red-400 hover:!bg-red-500/10"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete
                </button>
              )}
            </>
          )}
        />
      )}

      {modal && (
        <Modal
          title={
            modal.type === "tailor"
              ? `Tailor "${modal.cv.version_name ?? "CV"}" to a job`
              : `Gap analysis for "${modal.cv.version_name ?? "CV"}"`
          }
          onClose={closeModal}
        >
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">
                Job description
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                placeholder="Paste the job description here…"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            </div>

            {modalError && <p className="text-sm text-red-400">{modalError}</p>}

            <button
              type="button"
              onClick={handleSubmitModal}
              disabled={working || !jobDescription.trim()}
              className="btn-primary"
            >
              {working
                ? "Working…"
                : modal.type === "tailor"
                  ? "Generate tailored CV"
                  : "Run gap analysis"}
            </button>

            {tailoredText && (
              <div className="space-y-3">
                <div className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200">
                  {tailoredText}
                </div>
                <button type="button" onClick={downloadTailored} className="btn-secondary">
                  <Download className="h-3.5 w-3.5" />
                  Download as .txt
                </button>
              </div>
            )}

            {gapResult && <GapAnalysisCard analysis={gapResult} />}
          </div>
        </Modal>
      )}

      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}
    </div>
  );
}
