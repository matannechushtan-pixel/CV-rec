"use client";

import {
  LayoutDashboard,
  FileText,
  Briefcase,
  ClipboardList,
  Map,
  MessageSquare,
  Compass,
  Settings,
} from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import type { SidebarNavItem } from "@/components/layout/Sidebar";

const navItems: SidebarNavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "My CVs", href: "/dashboard/cv", icon: FileText },
  { label: "Job Feed", href: "/dashboard/jobs", icon: Briefcase },
  { label: "Applications", href: "/dashboard/applications", icon: ClipboardList },
  { label: "Career Roadmap", href: "/dashboard/roadmap", icon: Map },
  { label: "Interview Prep", href: "/dashboard/interview-prep", icon: MessageSquare },
  { label: "Career Coach", href: "/dashboard/career-chat", icon: Compass },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardShell
      brand="CV Intelligence"
      navItems={navItems}
      requiredRole="job_seeker"
      redirectTo="/company"
    >
      {children}
    </DashboardShell>
  );
}
