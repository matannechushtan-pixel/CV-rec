"use client";

import { useRef, useState } from "react";
import { Camera, X } from "lucide-react";

interface Props {
  value: string | null; // base64 data URI or null
  onChange: (b64: string | null) => void;
}

export function PhotoUpload({ value, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFile(file: File) {
    setError(null);
    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file (JPG, PNG, WEBP).");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Image must be under 5 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => onChange(e.target?.result as string);
    reader.readAsDataURL(file);
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-300">
        Profile photo <span className="text-slate-500">(optional)</span>
      </label>

      <div className="flex items-center gap-4">
        {/* Preview circle */}
        <div className="relative h-20 w-20 shrink-0">
          {value ? (
            <>
              <img
                src={value}
                alt="Profile preview"
                className="h-20 w-20 rounded-full object-cover border-2 border-white/20"
              />
              {/* Remove button */}
              <button
                type="button"
                onClick={() => onChange(null)}
                className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center
                           rounded-full bg-red-500 text-white hover:bg-red-400 transition"
                aria-label="Remove photo"
              >
                <X className="h-3 w-3" />
              </button>
            </>
          ) : (
            <div className="flex h-20 w-20 items-center justify-center rounded-full
                            border-2 border-dashed border-white/20 bg-white/5 text-slate-500">
              <Camera className="h-7 w-7" />
            </div>
          )}
        </div>

        {/* Upload button */}
        <div className="flex flex-col gap-1">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="btn-secondary !px-4 !py-2 text-sm"
          >
            {value ? "Change photo" : "Upload photo"}
          </button>
          <p className="text-xs text-slate-500">JPG, PNG or WEBP · max 5 MB</p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = ""; // allow re-selecting same file
          }}
        />
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
