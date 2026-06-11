"use client";

import { useState } from "react";
import api from "@/lib/api";

export function CVUploader({ onUploaded }: { onUploaded?: () => void }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    const allowed = [".pdf", ".docx", ".doc"];
    if (!allowed.some((ext) => file.name.toLowerCase().endsWith(ext))) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }
    setError(null);
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      await api.post("/cv/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
      onUploaded?.();
    } catch {
      setError("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
      className={`rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 ${dragging ? "border-blue-500 bg-blue-500/10" : "border-white/10 bg-white/5"}`}
    >
      <p className="mb-3 text-slate-300">Drag and drop your CV here, or</p>
      <label className={`btn-primary cursor-pointer ${loading ? "pointer-events-none opacity-50" : ""}`}>
        {loading ? "Uploading…" : "Choose file"}
        <input
          type="file"
          accept=".pdf,.docx,.doc"
          className="hidden"
          disabled={loading}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />
      </label>
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      <p className="mt-3 text-xs text-slate-500">PDF or DOCX, max 10 MB</p>
    </div>
  );
}
