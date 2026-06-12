"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function DiscordCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const code = searchParams.get("code");
    if (!code) {
      router.replace("/dashboard/settings?discord=error");
      return;
    }

    const token = getToken();
    if (!token) {
      router.replace("/auth/login");
      return;
    }

    api
      .get(`/discord/callback?code=${code}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(() => router.replace("/dashboard/settings?discord=connected"))
      .catch(() => router.replace("/dashboard/settings?discord=error"));
  }, [router, searchParams]);

  return (
    <div className="mesh-bg flex min-h-screen items-center justify-center bg-navy px-4">
      <div className="glass-card w-full max-w-sm p-8 text-center">
        <p className="text-sm text-slate-300">Connecting Discord…</p>
      </div>
    </div>
  );
}
