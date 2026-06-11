import Link from "next/link";
import {
  FileText,
  Target,
  Map,
  Briefcase,
  ClipboardList,
  MessageSquare,
  TrendingUp,
} from "lucide-react";

const stats = [
  { value: "10,000+", label: "CVs tailored" },
  { value: "85%", label: "Interview rate" },
  { value: "3.2x", label: "Faster job search" },
  { value: "50,000+", label: "Jobs matched" },
];

const features = [
  {
    title: "CV Tailoring",
    desc: "Match your CV to any job description instantly. Claude rewrites your bullets to mirror the role's language.",
    icon: FileText,
  },
  {
    title: "Gap Analysis",
    desc: "Know exactly what's missing before you apply. Get prioritised, actionable steps to close every gap.",
    icon: Target,
  },
  {
    title: "Career Roadmap",
    desc: "Set a target role and get a week-by-week plan built from O*NET data and your current profile.",
    icon: Map,
  },
  {
    title: "Smart Job Feed",
    desc: "AI-ranked listings sourced from multiple job boards, scored against your profile in real time.",
    icon: Briefcase,
  },
  {
    title: "Application Tracker",
    desc: "A Kanban board for every application — from applied to offer — so nothing falls through the cracks.",
    icon: ClipboardList,
  },
  {
    title: "Interview Prep",
    desc: "Practice tailored behavioural and technical questions with STAR-method answer frameworks.",
    icon: MessageSquare,
  },
];

export default function LandingPage() {
  return (
    <main className="mesh-bg min-h-screen text-white">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 sm:px-8">
        <span className="text-lg font-bold tracking-tight gradient-text">CV Intelligence</span>
        <div className="flex gap-3">
          <Link href="/auth/login" className="btn-secondary">
            Log in
          </Link>
          <Link href="/auth/register" className="btn-primary">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 py-16 sm:px-8 sm:py-24 lg:grid-cols-2 lg:py-32">
        <div>
          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            Land your next role with{" "}
            <span className="gradient-text">AI-powered</span> career tools
          </h1>
          <p className="mt-6 max-w-xl text-lg text-slate-300">
            Tailor your CV to any job in seconds, get a personalised gap analysis,
            and generate a step-by-step career roadmap — all in one place.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/auth/register" className="btn-primary px-6 py-3 text-base">
              Start for free
            </Link>
            <Link
              href="/auth/register?role=company_admin"
              className="btn-secondary px-6 py-3 text-base"
            >
              I&apos;m hiring
            </Link>
          </div>

          {/* Social proof stats */}
          <div className="mt-16 grid grid-cols-2 gap-6 sm:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label}>
                <p className="text-2xl font-bold gradient-text sm:text-3xl">{s.value}</p>
                <p className="mt-1 text-xs text-slate-400 sm:text-sm">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Floating dashboard mockup */}
        <div className="relative hidden lg:block">
          <div className="absolute -inset-8 -z-10 rounded-full bg-gradient-to-br from-blue-600/20 to-indigo-600/20 blur-3xl" />
          <div className="glass-card translate-x-6 p-3 shadow-2xl">
            <div className="mb-3 flex items-center gap-1.5 px-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
            </div>
            <div className="grid grid-cols-3 gap-3 rounded-xl bg-black/20 p-4">
              <div className="col-span-1 space-y-2">
                {["Overview", "My CVs", "Job Feed", "Applications", "Roadmap"].map((item, i) => (
                  <div
                    key={item}
                    className={`rounded-lg px-3 py-2 text-xs font-medium ${
                      i === 0
                        ? "bg-gradient-to-r from-blue-600/30 to-indigo-600/30 text-white"
                        : "text-slate-400"
                    }`}
                  >
                    {item}
                  </div>
                ))}
              </div>
              <div className="col-span-2 space-y-3">
                <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <TrendingUp className="h-3.5 w-3.5 text-blue-400" />
                    <span className="text-xs font-semibold text-white">Match score</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-1.5 w-4/5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500" />
                  </div>
                  <p className="mt-1 text-right text-xs text-slate-400">82%</p>
                </div>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="space-y-1.5 rounded-lg border border-white/10 bg-white/5 p-3">
                    <div className="h-2 w-3/4 rounded bg-white/10" />
                    <div className="h-2 w-1/2 rounded bg-white/10" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-6 pb-24 sm:px-8 sm:pb-32">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Everything you need to <span className="gradient-text">get hired faster</span>
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="glass-card glass-card-hover p-6">
                <div className="mb-4 inline-flex rounded-xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 p-2.5">
                  <Icon className="h-5 w-5 text-blue-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
                <p className="text-sm text-slate-400">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
