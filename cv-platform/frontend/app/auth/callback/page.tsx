"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { exchangeCodeForSession } from "@/lib/auth";

export default function AuthCallbackPage() {
  const router = useRouter();
  const hasRun = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode double-invocation consuming the PKCE code twice
    if (hasRun.current) return;
    hasRun.current = true;

    (async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      // Role is stored in localStorage before OAuth redirect — don't rely on URL params
      const rawRole = localStorage.getItem("pending_oauth_role");
      const role = rawRole === "company_admin" || rawRole === "job_seeker" ? rawRole : undefined;

      try {
        if (!code) {
          throw new Error("Missing OAuth callback code");
        }

        const { user } = await exchangeCodeForSession(code, role);
        localStorage.removeItem("pending_oauth_role");
        router.replace(user.role === "company_admin" ? "/company" : "/dashboard");
      } catch (error) {
        console.error("Google OAuth callback failed", error);
        localStorage.removeItem("pending_oauth_role");
        router.replace("/auth/login?error=oauth");
      }
    })();
  }, [router]);

  return (
    <div className="mesh-bg flex min-h-screen items-center justify-center bg-navy px-4">
      <div className="glass-card w-full max-w-sm p-8 text-center">
        <p className="text-sm text-slate-300">Signing you in…</p>
      </div>
    </div>
  );
}
