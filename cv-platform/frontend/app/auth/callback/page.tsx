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
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <p className="text-sm text-slate-500">Signing you in…</p>
    </div>
  );
}
