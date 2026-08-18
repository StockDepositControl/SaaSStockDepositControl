"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole } from "@/lib/types/domain";
import { LogOut } from "lucide-react";

export function TopBar() {
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
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between gap-4 z-20 shrink-0">
      {/* Left side: Page Title */}
      <div className="flex items-center">
        <span className="text-slate-500 font-medium text-lg">
          {getPageTitle()}
        </span>
      </div>

      {/* Right Controls: User Profile & Actions */}
      <div className="flex items-center gap-4">
        {/* Current User Pill */}
        <div className="flex items-center gap-3">
          {/* User Initials Circle */}
          <div className="h-9 w-9 rounded-full bg-[#1a56db] flex items-center justify-center font-semibold text-sm text-white shadow-sm">
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
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition ml-2"
            title="Cerrar Sesión"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
