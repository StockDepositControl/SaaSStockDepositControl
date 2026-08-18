"use client";

import React, { useState } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { UserRole } from "@/lib/types/domain";
import { AlertCircle, Plus, MinusCircle, Check, Info } from "lucide-react";

export default function UsersPage() {
  const { currentRole, currentUser, users: initialUsers } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  
  // Local state for UI interactivity (deactivate/reactivate mock)
  const [users, setUsers] = useState(initialUsers);

  const totalUsers = users.length;
  const activeUsers = users.filter((u) => u.is_active).length;
  const inactiveUsers = users.filter((u) => !u.is_active).length;
  const auditors = users.filter((u) => u.role === UserRole.AUDITOR).length;
  const supervisors = users.filter((u) => u.role === UserRole.SUPERVISOR).length;
  const administrators = users.filter((u) => u.role === UserRole.ADMINISTRADOR).length;

  const toggleUserStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, is_active: !u.is_active } : u))
    );
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();
  };

  const getMockLastActive = (isActive: boolean, role: UserRole) => {
    if (!isActive) return "Última vez: 14/07/2026";
    if (role === UserRole.ADMINISTRADOR) return "Última vez: Hoy, 09:14";
    if (role === UserRole.SUPERVISOR) return "Última vez: Hoy, 07:30";
    return "Última vez: Ayer, 17:45";
  };

  return (
    <DemoShell>
      <div className="max-w-[1000px] mx-auto py-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
              Gestión de Personal
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Gestione accesos y roles de usuarios para Audit Global
            </p>
          </div>
          {isAdmin && (
            <button className="flex items-center gap-2 bg-[#1a56db] hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-sm">
              <Plus className="w-5 h-5" />
              <span>Nuevo Usuario</span>
            </button>
          )}
        </div>

        {isAdmin ? (
          <>
            {/* KPI Strip */}
            <div className="bg-white border border-slate-200 rounded-xl px-8 py-5 flex items-center justify-between mb-6 shadow-sm overflow-x-auto">
              <div className="flex items-baseline gap-2 shrink-0 pr-6">
                <span className="text-2xl font-bold text-slate-900">{totalUsers}</span>
                <span className="text-sm text-slate-500 font-medium">usuarios totales</span>
              </div>
              <div className="h-8 w-px bg-slate-200 shrink-0"></div>
              <div className="flex items-baseline gap-2 shrink-0 px-6">
                <span className="text-2xl font-bold text-emerald-600">{activeUsers}</span>
                <span className="text-sm text-slate-500 font-medium">activos</span>
              </div>
              <div className="h-8 w-px bg-slate-200 shrink-0"></div>
              <div className="flex items-baseline gap-2 shrink-0 px-6">
                <span className="text-2xl font-bold text-red-600">{inactiveUsers}</span>
                <span className="text-sm text-slate-500 font-medium">inactivos</span>
              </div>
              <div className="h-8 w-px bg-slate-200 shrink-0"></div>
              <div className="flex items-baseline gap-2 shrink-0 px-6">
                <span className="text-2xl font-bold text-[#1a56db]">{auditors}</span>
                <span className="text-sm text-slate-500 font-medium">auditores</span>
              </div>
              <div className="h-8 w-px bg-slate-200 shrink-0"></div>
              <div className="flex items-baseline gap-2 shrink-0 px-6">
                <span className="text-2xl font-bold text-amber-600">{supervisors}</span>
                <span className="text-sm text-slate-500 font-medium">supervisores</span>
              </div>
              <div className="h-8 w-px bg-slate-200 shrink-0"></div>
              <div className="flex items-baseline gap-2 shrink-0 pl-6">
                <span className="text-2xl font-bold text-slate-900">{administrators}</span>
                <span className="text-sm text-slate-500 font-medium">administradores</span>
              </div>
            </div>

            {/* Data Table */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600 min-w-[800px]">
                  <thead className="bg-white border-b border-slate-200 text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                    <tr>
                      <th className="px-6 py-4">NOMBRE</th>
                      <th className="px-6 py-4">EMAIL</th>
                      <th className="px-6 py-4">ROL</th>
                      <th className="px-6 py-4">ESTADO</th>
                      <th className="px-6 py-4 text-right">ACCIONES</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map((u) => {
                      const isMe = currentUser?.id === u.id;
                      const opacityClass = u.is_active ? "opacity-100" : "opacity-60";
                      return (
                        <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4">
                            <div className={`flex items-center gap-4 ${opacityClass}`}>
                              <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                                  u.is_active
                                    ? "bg-[#1a56db] text-white"
                                    : "bg-slate-200 text-slate-500"
                                }`}
                              >
                                {getInitials(u.name)}
                              </div>
                              <div>
                                <div className="flex items-center">
                                  <span className={`font-bold ${u.is_active ? "text-slate-900" : "text-slate-500"}`}>
                                    {u.name}
                                  </span>
                                  {isMe && (
                                    <span className="ml-2 bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                      Tú
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-slate-400 mt-0.5">
                                  {getMockLastActive(!!u.is_active, u.role)}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className={`px-6 py-4 text-slate-500 ${opacityClass}`}>
                            {u.email}
                          </td>
                          <td className={`px-6 py-4 ${opacityClass}`}>
                            {u.role === UserRole.ADMINISTRADOR && (
                              <span className="bg-slate-900 text-white px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                ADMINISTRADOR
                              </span>
                            )}
                            {u.role === UserRole.AUDITOR && (
                              <span className="bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                AUDITOR
                              </span>
                            )}
                            {u.role === UserRole.SUPERVISOR && (
                              <span className="bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                SUPERVISOR
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            {u.is_active ? (
                              <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                ACTIVO
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 bg-red-50 text-red-600 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                                INACTIVO
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-right">
                            {u.is_active ? (
                              <button
                                onClick={() => toggleUserStatus(u.id)}
                                disabled={isMe}
                                className={`inline-flex items-center gap-1.5 text-sm font-medium ${
                                  isMe
                                    ? "text-slate-300 pointer-events-none"
                                    : "text-red-500 hover:text-red-700"
                                } transition-colors`}
                              >
                                <MinusCircle className="w-4 h-4" />
                                <span>Desactivar</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => toggleUserStatus(u.id)}
                                className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
                              >
                                <Check className="w-4 h-4" />
                                <span>Reactivar</span>
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              {/* Footer Note */}
              <div className="bg-slate-50/80 border-t border-slate-200 p-4 flex items-center gap-2 text-sm text-slate-500 font-medium">
                <Info className="w-4 h-4 shrink-0 text-slate-400" />
                <span>Los usuarios no pueden ser eliminados — la desactivación preserva la trazabilidad completa de las auditorías.</span>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 px-6 bg-white rounded-3xl border border-slate-200 border-dashed text-center mt-6">
            <AlertCircle className="w-16 h-16 text-slate-300 mb-6" />
            <h2 className="text-xl font-bold text-slate-900 mb-2">Acceso Restringido</h2>
            <p className="text-sm text-slate-500 max-w-sm">
              Esta sección está restringida a administradores del sistema.
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
