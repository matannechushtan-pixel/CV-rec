"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { exchangeCodeForSession } from "@/lib/auth";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const params = new URLSearchParams(window.location.search);
      const roleParam = params.get("role");
      const role = roleParam === "company_admin" || roleParam === "job_seeker" ? roleParam : undefined;

      try {
        const { user } = await exchangeCodeForSession(window.location.href, role);
        localStorage.removeItem("pending_oauth_role");
        router.replace(user.role === "company_admin" ? "/company" : "/dashboard");
      } catch {
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
