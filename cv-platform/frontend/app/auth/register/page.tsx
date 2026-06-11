"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { register, signInWithGoogle } from "@/lib/auth";
import { getUser } from "@/lib/auth";

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();

  const [role, setRole] = useState<"job_seeker" | "company_admin">("job_seeker");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  async function handleGoogleSignIn() {
    setError(null);
    setGoogleLoading(true);
    try {
      localStorage.setItem("pending_oauth_role", role);
      await signInWithGoogle();
    } catch {
      localStorage.removeItem("pending_oauth_role");
      setError("Google sign-in failed");
      setGoogleLoading(false);
    }
  }

  useEffect(() => {
    const r = params.get("role");
    if (r === "company_admin") setRole("company_admin");
  }, [params]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, role, fullName || undefined);
      const user = getUser();
      router.push(user?.role === "company_admin" ? "/company" : "/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mesh-bg flex min-h-screen items-center justify-center bg-navy px-4">
      <div className="glass-card w-full max-w-sm p-8">
        <Link href="/" className="gradient-text text-lg font-bold tracking-tight">
          CV Intelligence
        </Link>
        <h1 className="mt-4 mb-1 text-2xl font-bold text-white">Create account</h1>
        <p className="mb-6 text-sm text-slate-400">Start your CV Intelligence journey</p>

        {error && (
          <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Role selector */}
        <div className="mb-5 grid grid-cols-2 gap-2">
          {(["job_seeker", "company_admin"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`rounded-xl border py-2 text-sm font-medium transition-colors ${
                role === r
                  ? "border-blue-500/50 bg-blue-500/10 text-blue-300"
                  : "border-white/10 bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {r === "job_seeker" ? "Job Seeker" : "Hiring / Company"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {role === "job_seeker" && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300" htmlFor="name">
                Full name
              </label>
              <input
                id="name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-300" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-300" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full justify-center">
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs text-slate-500">OR</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={googleLoading}
          className="btn-secondary w-full justify-center"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.51h6.47c-.28 1.48-1.13 2.73-2.4 3.58v2.98h3.88c2.27-2.09 3.54-5.17 3.54-8.8z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.07 7.93-2.91l-3.88-2.98c-1.08.72-2.45 1.15-4.05 1.15-3.11 0-5.75-2.1-6.69-4.93H1.3v3.07A12 12 0 0 0 12 24z"
            />
            <path
              fill="#FBBC05"
              d="M5.31 14.33A7.2 7.2 0 0 1 4.93 12c0-.81.14-1.6.38-2.33V6.6H1.3A12 12 0 0 0 0 12c0 1.94.46 3.77 1.3 5.4l4.01-3.07z"
            />
            <path
              fill="#EA4335"
              d="M12 4.77c1.76 0 3.34.6 4.58 1.79l3.44-3.44C17.94 1.19 15.24 0 12 0A12 12 0 0 0 1.3 6.6l4.01 3.07C6.25 6.84 8.89 4.77 12 4.77z"
            />
          </svg>
          {googleLoading ? "Redirecting…" : "Continue with Google"}
        </button>

        <p className="mt-5 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-medium text-blue-400 hover:text-blue-300">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
