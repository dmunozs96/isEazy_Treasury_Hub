"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Upload,
  GitMerge,
  Tag,
  TrendingUp,
  Table2,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/import", label: "Import", icon: Upload },
  { href: "/ledger", label: "Ledger", icon: BookOpen },
  { href: "/classification", label: "Clasificacion", icon: Tag },
  { href: "/intercompany", label: "Intercompany", icon: GitMerge },
  { href: "/cashflow", label: "Cash Flow", icon: Table2 },
  { href: "/forecast", label: "Forecast", icon: TrendingUp },
  { href: "/settings", label: "Integridad", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 flex-shrink-0 border-r bg-card flex flex-col">
      <div className="px-4 py-5 border-b">
        <span className="text-sm font-semibold text-foreground tracking-tight">
          isEazy Treasury Hub
        </span>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              pathname.startsWith(href)
                ? "bg-primary/10 text-primary font-medium"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
