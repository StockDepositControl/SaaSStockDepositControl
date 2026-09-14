"use client";

import React from "react";
import { TipoAccion, UserRole } from "@/lib/types/domain";
import { CheckCircle2, Clock, AlertTriangle, AlertCircle, Info, ShieldCheck, Shield } from "lucide-react";

export type StatusBadgeType = "audit" | "movement" | "fefo" | "role";

export interface StatusBadgeProps {
  type: StatusBadgeType;
  value: boolean | TipoAccion | UserRole | string | null | undefined;
  expirationDate?: string | null;
  size?: "sm" | "md";
}

export function StatusBadge({
  type,
  value,
  expirationDate,
  size = "sm",
}: StatusBadgeProps) {
  const sizeClasses =
    size === "sm"
      ? "px-2.5 py-0.5 text-[11px] gap-1.5"
      : "px-3 py-1 text-xs gap-2";

  // 1. Audit Status (Auditado / Pendiente)
  if (type === "audit") {
    const isAudited = Boolean(value);
    if (isAudited) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-800/80 shadow-sm ${sizeClasses}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Auditado</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center rounded-full font-semibold bg-warning-950/80 text-warning-400 border border-warning-700/80 ${sizeClasses}`}
      >
        <Clock className="w-3.5 h-3.5 text-warning-400" />
        <span>Pendiente</span>
      </span>
    );
  }

  // 2. Movement Type (Alta / Baja / Sin Acción)
  if (type === "movement") {
    const movement = value as TipoAccion;
    if (movement === TipoAccion.ALTA) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700/90 shadow-[0_0_12px_-2px_rgba(16,185,129,0.3)] ${sizeClasses}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>ALTA (Sobrante)</span>
        </span>
      );
    }
    if (movement === TipoAccion.BAJA) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-semibold bg-rose-950/80 text-rose-300 border border-rose-700/90 shadow-[0_0_12px_-2px_rgba(244,63,94,0.3)] ${sizeClasses}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-pulse" />
          <span>BAJA (Faltante)</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center rounded-full font-semibold bg-slate-800/80 text-slate-300 border border-slate-700 ${sizeClasses}`}
      >
        <span>Sin Acción</span>
      </span>
    );
  }

  // 3. FEFO Expiration Tiers
  if (type === "fefo") {
    const rawDate = expirationDate || (typeof value === "string" ? value : null);
    if (!rawDate) {
      return (
        <span className={`inline-flex items-center rounded-full text-slate-500 font-mono ${sizeClasses}`}>
          Sin Vencimiento
        </span>
      );
    }

    const exp = new Date(rawDate);
    const now = new Date("2026-08-18"); // Reference mock date or current
    const diffTime = exp.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays <= 30) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-bold bg-rose-950/80 text-rose-300 border border-rose-600/90 shadow-[0_0_12px_-2px_rgba(239,68,68,0.4)] ${sizeClasses}`}
          title={`Vence el ${rawDate} (${diffDays} días restantes)`}
        >
          <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          <span>FEFO Crítico ({diffDays > 0 ? `${diffDays}d` : "Vencido"})</span>
        </span>
      );
    }

    if (diffDays <= 60) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-semibold bg-amber-950/80 text-amber-300 border border-amber-600/80 ${sizeClasses}`}
          title={`Vence el ${rawDate} (${diffDays} días restantes)`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Advertencia ({diffDays}d)</span>
        </span>
      );
    }

    if (diffDays <= 90) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-semibold bg-blue-950/80 text-blue-300 border border-blue-600/80 ${sizeClasses}`}
          title={`Vence el ${rawDate} (${diffDays} días restantes)`}
        >
          <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>Atención ({diffDays}d)</span>
        </span>
      );
    }

    return (
      <span
        className={`inline-flex items-center rounded-full font-semibold bg-emerald-950/50 text-emerald-400 border border-emerald-800/60 ${sizeClasses}`}
        title={`Vence el ${rawDate} (${diffDays} días restantes)`}
      >
        <span>Normal ({diffDays}d)</span>
      </span>
    );
  }

  // 4. Role Badges
  if (type === "role") {
    const role = value as UserRole;
    if (role === UserRole.ADMINISTRADOR) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-bold uppercase tracking-wider bg-amber-950/80 text-amber-300 border border-amber-600/80 shadow-[0_0_10px_-2px_rgba(245,158,11,0.3)] ${sizeClasses}`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
          <span>Administrador</span>
        </span>
      );
    }
    if (role === UserRole.SUPERVISOR) {
      return (
        <span
          className={`inline-flex items-center rounded-full font-bold uppercase tracking-wider bg-indigo-950/80 text-indigo-300 border border-indigo-600/80 ${sizeClasses}`}
        >
          <Shield className="w-3.5 h-3.5 text-indigo-400" />
          <span>Supervisor</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center rounded-full font-bold uppercase tracking-wider bg-emerald-950/80 text-emerald-300 border border-emerald-600/80 ${sizeClasses}`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        <span>Auditor</span>
      </span>
    );
  }

  return null;
}
