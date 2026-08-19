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
  X,
} from "lucide-react";

export interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

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
    adminOnly: true,
  },
  {
    label: "Gestión Usuarios",
    href: "/users",
    icon: Users2,
    adminOnly: true,
  },
];

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { currentUser, currentRole } = useDataClient();

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  // Extract initials for the user card avatar
  const userInitials =
    currentUser?.name
      ?.split(" ")
      .map((part) => part[0])
      .join("")
      .substring(0, 2)
      .toUpperCase() || "U";

  const roleLabel =
    currentRole === UserRole.ADMINISTRADOR
      ? "Administrador"
      : currentRole === UserRole.SUPERVISOR
      ? "Supervisor"
      : "Auditor";

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          onClick={onMobileClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Main Sidebar Aside */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col justify-between border-r transition-all duration-300 shrink-0 bg-[var(--sidebar-background)] border-[var(--sidebar-divider)] relative ${
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        } ${collapsed ? "md:w-20" : "md:w-64"} w-64 h-full`}
      >
        {/* Brand Header */}
        <div
          className={`h-16 border-b border-[var(--sidebar-divider)] flex items-center shrink-0 relative ${
            collapsed ? "justify-center px-2" : "justify-between px-4"
          }`}
        >
          <Link
            href="/dashboard"
            onClick={onMobileClose}
            className={`flex items-center gap-3 transition-opacity hover:opacity-90 ${
              collapsed ? "justify-center shrink-0" : "min-w-0"
            }`}
            title="Audit Global"
          >
            {/* Logo Icon Ring */}
            <div className="w-10 h-10 rounded-xl border border-[var(--sidebar-item-active-bg)] bg-[var(--sidebar-surface-elevated)] flex items-center justify-center shrink-0 text-[var(--sidebar-item-active-bg)] shadow-sm">
              <ClipboardCheck className="w-5 h-5 shrink-0" strokeWidth={2.2} />
            </div>

            {/* Logo Text Hierarchy */}
            {!collapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-extrabold text-sm text-[var(--sidebar-item-active-fg)] tracking-tight truncate">
                  AUDIT GLOBAL
                </span>
                <span className="text-[10px] text-[var(--sidebar-text-secondary)] font-mono tracking-wider font-semibold truncate">
                  Control de Stock
                </span>
              </div>
            )}
          </Link>

          {/* Desktop Collapse / Expand Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={`transition hidden md:flex items-center justify-center shrink-0 ${
              collapsed
                ? "absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-[var(--sidebar-surface-elevated)] border border-[var(--sidebar-divider)] text-[var(--sidebar-item-inactive-fg)] hover:text-[var(--sidebar-item-active-fg)] hover:bg-[var(--sidebar-item-active-bg)] hover:border-transparent shadow-md z-20 cursor-pointer"
                : "p-1.5 rounded-lg text-[var(--sidebar-item-inactive-fg)] hover:text-[var(--sidebar-item-active-fg)] hover:bg-[var(--sidebar-surface-elevated)]"
            }`}
            title={collapsed ? "Expandir Menú" : "Contraer Menú"}
            aria-label={collapsed ? "Expandir Menú" : "Contraer Menú"}
          >
            {collapsed ? (
              <ChevronRight className="w-3.5 h-3.5" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={onMobileClose}
            className="p-1.5 rounded-lg text-[var(--sidebar-item-inactive-fg)] hover:text-[var(--sidebar-item-active-fg)] hover:bg-[var(--sidebar-surface-elevated)] transition md:hidden"
            aria-label="Cerrar Menú"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Middle Scrollable Section: Navigation */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-1.5">
          <nav aria-label="Navegación Principal" className="space-y-1.5">
            {navItems.map((item) => {
              if (item.adminOnly && !isAdmin) {
                return null; // Structurally omit admin-only links
              }

              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={onMobileClose}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 relative group ${
                    collapsed ? "justify-center px-2" : ""
                  } ${
                    isActive
                      ? "bg-[var(--sidebar-item-active-bg)] text-[var(--sidebar-item-active-fg)] shadow-sm"
                      : "text-[var(--sidebar-item-inactive-fg)] hover:text-[var(--sidebar-item-active-fg)] hover:bg-[var(--sidebar-surface-elevated)]"
                  }`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 transition-colors ${
                      isActive
                        ? "text-[var(--sidebar-item-active-fg)]"
                        : "text-[var(--sidebar-item-inactive-fg)] group-hover:text-[var(--sidebar-item-active-fg)]"
                    }`}
                  />

                  {!collapsed && (
                    <span className="truncate flex-1">{item.label}</span>
                  )}

                  {!collapsed && item.badge && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-[var(--sidebar-surface-elevated)] text-[var(--sidebar-item-active-fg)] border border-[var(--sidebar-divider)]">
                      {item.badge}
                    </span>
                  )}

                  {isActive && !collapsed && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-[var(--sidebar-item-active-fg)]" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Lower Section: Bottom User Card */}
        <div className="p-3 border-t border-[var(--sidebar-divider)] shrink-0">
          <div
            className={`bg-[var(--sidebar-surface-elevated)] rounded-xl transition-all duration-200 flex items-center gap-3 ${
              collapsed ? "p-1.5 justify-center" : "p-2.5"
            }`}
            title={collapsed ? `${currentUser?.name || "Usuario"} (${roleLabel})` : undefined}
          >
            {/* User Avatar Circle */}
            <div className="w-8 h-8 rounded-full bg-[var(--sidebar-item-active-bg)] text-[var(--sidebar-item-active-fg)] flex items-center justify-center font-bold text-xs shrink-0 shadow-sm">
              {userInitials}
            </div>

            {/* User Identity Details */}
            {!collapsed && (
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-xs font-semibold text-[var(--sidebar-item-active-fg)] truncate">
                  {currentUser?.name || "Usuario"}
                </span>
                <span className="text-[10px] text-[var(--sidebar-text-secondary)] font-medium truncate uppercase tracking-wider">
                  {roleLabel}
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
