"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole } from "@/lib/types/domain";
import { LogOut, Menu } from "lucide-react";

export interface TopBarProps {
  onMenuToggle?: () => void;
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { currentUser, currentRole, logout } = useDataClient();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getPageTitle = () => {
    if (pathname.includes("dashboard")) return "Dashboard";
    if (pathname.includes("audit")) return "Auditoría";
    if (pathname.includes("catalog")) return "Catálogo";
    if (pathname.includes("reports")) return "Reportes";
    if (pathname.includes("users")) return "Usuarios";
    return "Dashboard";
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 md:px-6 flex items-center justify-between gap-4 z-20 shrink-0">
      {/* Left side: Mobile Menu Button & Page Title */}
      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            className="w-11 h-11 rounded-xl flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-slate-100 active:scale-95 transition md:hidden shrink-0 cursor-pointer"
            title="Abrir Menú"
            aria-label="Abrir Menú"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <span className="text-slate-700 font-semibold text-base sm:text-lg truncate">
          {getPageTitle()}
        </span>
      </div>

      {/* Right Controls: User Profile & Actions */}
      <div className="flex items-center gap-2 sm:gap-4 shrink-0">
        {/* Current User Pill */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* User Initials Circle */}
          <div className="h-9 w-9 rounded-full bg-[#1a56db] flex items-center justify-center font-semibold text-xs text-white shadow-sm shrink-0">
            {currentUser?.name?.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase() || "U"}
          </div>

          {/* Name */}
          <div className="hidden sm:block text-slate-900 font-medium text-sm">
            {currentUser?.name || "Usuario"}
          </div>

          {/* Role Badge */}
          <div
            className={`hidden lg:flex items-center justify-center px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase ml-1 ${
              currentRole === UserRole.ADMINISTRADOR
                ? "bg-slate-900 text-white"
                : currentRole === UserRole.SUPERVISOR
                ? "bg-purple-100 text-purple-700"
                : "bg-blue-100 text-blue-700"
            }`}
          >
            {currentRole === UserRole.ADMINISTRADOR
              ? "ADMINISTRADOR"
              : currentRole === UserRole.SUPERVISOR
              ? "SUPERVISOR"
              : "AUDITOR"}
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 active:scale-95 transition cursor-pointer"
            title="Cerrar Sesión"
            aria-label="Cerrar Sesión"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
