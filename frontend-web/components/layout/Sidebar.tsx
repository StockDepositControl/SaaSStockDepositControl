"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole } from "@/lib/types/domain";
import {
  LayoutDashboard,
  ClipboardCheck,
  PackageSearch,
  BarChart3,
  Users2,
  ChevronLeft,
  ChevronRight,
  Boxes,
  ShieldAlert,
  TestTube,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
  badge?: string;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Auditoría de Stock",
    href: "/audit",
    icon: ClipboardCheck,
    badge: "En vivo",
  },
  {
    label: "Catálogo Artículos",
    href: "/catalog",
    icon: PackageSearch,
  },
  {
    label: "Reportes y FEFO",
    href: "/reports",
    icon: BarChart3,
  },
  {
    label: "Gestión Usuarios",
    href: "/users",
    icon: Users2,
    adminOnly: true,
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { currentRole } = useDataClient();

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  return (
    <aside
      className={`glass-panel border-r border-slate-800/80 transition-all duration-300 flex flex-col justify-between z-30 shrink-0 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 px-4 border-b border-slate-800/80 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30 shrink-0">
              <Boxes className="w-5 h-5" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-extrabold text-sm text-white tracking-tight">
                  AUDIT GLOBAL
                </span>
                <span className="text-[10px] text-indigo-400 font-mono tracking-wider font-semibold">
                  DEPOSIT CONTROL
                </span>
              </div>
            )}
          </Link>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition hidden md:block"
            title={collapsed ? "Expandir Menú" : "Contraer Menú"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1.5">
          {navItems.map((item) => {
            if (item.adminOnly && !isAdmin) {
              return null; // Structurally omit admin-only navigation links
            }

            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.label}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 relative group ${
                  isActive
                    ? "bg-indigo-600/20 text-white border border-indigo-500/40 shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 transition-colors ${
                    isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-indigo-300"
                  }`}
                />

                {!collapsed && (
                  <span className="truncate flex-1">{item.label}</span>
                )}

                {!collapsed && item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {item.badge}
                  </span>
                )}

                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-indigo-500" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info / Sandbox Gateway */}
      <div className="p-3 border-t border-slate-800/80 space-y-2">
        <Link
          href="/debug"
          className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition"
          title="Sandbox Técnico / RBAC"
        >
          <TestTube className="w-4 h-4 text-amber-400 shrink-0" />
          {!collapsed && <span>Portal de Pruebas / RBAC</span>}
        </Link>

        {!collapsed && (
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[10px] text-slate-500">
            <div className="flex items-center gap-1.5 text-slate-400 font-semibold">
              <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
              <span>Multi-Tenant SSoT</span>
            </div>
            <p className="mt-1 leading-tight text-slate-500">
              Sucursal Central #01 · Farmanor Network
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
