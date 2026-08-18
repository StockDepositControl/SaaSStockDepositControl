"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { StatusBadge } from "../ui/StatusBadge";
import { Building2, Bell, RefreshCw, LogOut } from "lucide-react";

export function TopBar() {
  const router = useRouter();
  const { currentUser, currentRole, client, logout } = useDataClient();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="h-16 glass-panel border-b border-slate-800/80 px-6 flex items-center justify-between gap-4 z-20 shrink-0">
      {/* Branch & Warehouse Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 shadow-sm">
          <Building2 className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold text-white">Sucursal Central (01)</span>
          <span className="text-slate-600">/</span>
          <span className="text-indigo-300 font-mono">Depósito #01</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 font-mono">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Servidor en línea</span>
        </div>
      </div>

      {/* Right Controls: User Profile & Actions */}
      <div className="flex items-center gap-3">
        {/* Reset State Button */}
        <button
          onClick={() => client.resetData()}
          className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-slate-800/80 transition"
          title="Restablecer datos de demostración"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Demo</span>
        </button>

        {/* Notifications Icon */}
        <button
          className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-slate-800/80 transition relative"
          title="Notificaciones de Auditoría"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-500 ring-2 ring-slate-900" />
        </button>

        <div className="h-6 w-px bg-slate-800 hidden sm:block" />

        {/* Current User Pill */}
        <div className="flex items-center gap-3 pl-1">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-bold text-white tracking-tight leading-tight">
              {currentUser?.name || "Usuario"}
            </div>
            <div className="text-[10px] text-slate-400 font-mono">
              {currentUser?.email}
            </div>
          </div>

          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center font-bold text-xs text-indigo-300 shadow-sm">
            {currentUser?.name?.charAt(0) || "U"}
          </div>

          <div className="hidden lg:block">
            <StatusBadge type="role" value={currentRole} size="sm" />
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="p-2 rounded-xl text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition ml-2"
            title="Cerrar Sesión"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
