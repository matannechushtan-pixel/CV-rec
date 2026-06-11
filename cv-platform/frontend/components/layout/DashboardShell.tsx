"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu, X, LogOut } from "lucide-react";
import { getUser, logout } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import { Sidebar, type SidebarNavItem } from "./Sidebar";

export function DashboardShell({
  brand,
  navItems,
  requiredRole,
  redirectTo,
  children,
}: {
  brand: string;
  navItems: SidebarNavItem[];
  requiredRole: UserRole;
  redirectTo: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [ready, setReady] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      router.push("/auth/login");
      return;
    }
    if (user.role !== requiredRole) {
      router.push(redirectTo);
      return;
    }
    setEmail(user.email);
    setReady(true);
  }, [router, requiredRole, redirectTo]);

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  if (!ready) {
    return <div className="min-h-screen mesh-bg" />;
  }

  return (
    <div className="flex min-h-screen mesh-bg text-slate-100">
      {/* Desktop sidebar */}
      <aside className="hidden lg:block">
        <Sidebar items={navItems} brand={brand} />
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full">
            <Sidebar items={navItems} brand={brand} onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-4 backdrop-blur-md sm:px-8">
          <button
            className="rounded-lg p-2 text-slate-300 hover:bg-white/10 lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <span className="hidden text-sm text-slate-400 lg:block">{email}</span>

          <div className="flex items-center gap-3 sm:hidden" />

          <button
            onClick={handleLogout}
            className="btn-secondary !px-3 !py-1.5 text-xs"
          >
            <LogOut className="h-3.5 w-3.5" />
            Log out
          </button>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-8 sm:py-8">{children}</main>
      </div>

      {mobileOpen && (
        <button
          className="fixed right-4 top-4 z-50 rounded-lg bg-navy p-2 text-slate-200 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}
