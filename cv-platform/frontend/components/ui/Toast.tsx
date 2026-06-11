"use client";

import { useEffect } from "react";
import { CheckCircle2 } from "lucide-react";

export function Toast({
  message,
  onDismiss,
  duration = 3000,
}: {
  message: string;
  onDismiss: () => void;
  duration?: number;
}) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, duration);
    return () => clearTimeout(timer);
  }, [onDismiss, duration]);

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-4">
      <div className="glass-card flex items-center gap-2 border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300 shadow-lg">
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        {message}
      </div>
    </div>
  );
}
