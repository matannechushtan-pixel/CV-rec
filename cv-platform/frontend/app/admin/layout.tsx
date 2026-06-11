"use client";

import { LayoutDashboard } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import type { SidebarNavItem } from "@/components/layout/Sidebar";

const navItems: SidebarNavItem[] = [{ label: "Overview", href: "/admin", icon: LayoutDashboard }];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardShell
      brand="CV Intelligence Admin"
      navItems={navItems}
      requiredRole="admin"
      redirectTo="/auth/login"
    >
      {children}
    </DashboardShell>
  );
}
