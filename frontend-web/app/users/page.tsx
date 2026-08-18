"use client";

import React from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { UserRole } from "@/lib/types/domain";
import { Users2, AlertCircle } from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";

export default function UsersPage() {
  const { currentRole, users } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  return (
    <DemoShell>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <Users2 className="w-8 h-8 text-indigo-400" />
              <span>Gestión de Usuarios Operativos</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Administración de personal de depósito y permisos RBAC.
            </p>
          </div>
        </div>

        {isAdmin ? (
          <div className="glass-panel rounded-2xl p-6 border border-slate-800 overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900 text-slate-400 uppercase border-b border-slate-800">
                <tr>
                  <th className="p-3">Nombre / Email</th>
                  <th className="p-3">Token Operativo</th>
                  <th className="p-3">Estado</th>
                  <th className="p-3 text-right">Rol Asignado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/30">
                    <td className="p-3">
                      <div className="font-bold text-white text-sm">{u.name}</div>
                      <div className="text-slate-500">{u.email}</div>
                    </td>
                    <td className="p-3 font-mono text-indigo-400">{u.badgeToken}</td>
                    <td className="p-3">
                      {u.is_active ? (
                        <span className="text-emerald-400 font-semibold">Activo</span>
                      ) : (
                        <span className="text-rose-400 font-semibold">Inactivo</span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <StatusBadge type="role" value={u.role} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-[50vh] text-center p-6 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed">
            <AlertCircle className="w-16 h-16 text-slate-600 mb-4" />
            <h2 className="text-xl font-bold text-white">Acceso Denegado</h2>
            <p className="text-sm text-slate-400 max-w-sm mt-2">
              Esta sección está restringida a administradores del sistema.
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
