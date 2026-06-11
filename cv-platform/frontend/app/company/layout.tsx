"use client";

import { LayoutDashboard, Briefcase, Users } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import type { SidebarNavItem } from "@/components/layout/Sidebar";

const navItems: SidebarNavItem[] = [
  { label: "Overview", href: "/company", icon: LayoutDashboard },
  { label: "Job Posts", href: "/company/jobs", icon: Briefcase },
  { label: "Candidates", href: "/company/candidates", icon: Users },
];

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardShell
      brand="CV Intelligence"
      navItems={navItems}
      requiredRole="company_admin"
      redirectTo="/dashboard"
    >
      {children}
    </DashboardShell>
  );
}
