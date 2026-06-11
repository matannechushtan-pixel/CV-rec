"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export interface SidebarNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export function Sidebar({
  items,
  brand,
  onNavigate,
}: {
  items: SidebarNavItem[];
  brand: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col gap-1 border-r border-white/10 bg-navy/95 px-4 py-6">
      <div className="mb-6 px-2">
        <span className="text-lg font-bold tracking-tight gradient-text">{brand}</span>
      </div>

      <nav className="flex flex-col gap-1">
        {items.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn("sidebar-link", active && "sidebar-link-active")}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
