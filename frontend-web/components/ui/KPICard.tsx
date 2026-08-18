"use client";

import React from "react";
import { LucideIcon, Lock } from "lucide-react";

export type KPICardVariant = "primary" | "success" | "danger" | "warning" | "neutral";

export interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: KPICardVariant;
  trend?: {
    value: string | number;
    isPositive?: boolean;
    label?: string;
  };
  isRestricted?: boolean;
  restrictedMessage?: string;
}

const variantStyles: Record<
  KPICardVariant,
  {
    iconBg: string;
    iconColor: string;
    glow: string;
    border: string;
  }
> = {
  primary: {
    iconBg: "bg-indigo-500/10",
    iconColor: "text-indigo-400",
    glow: "shadow-[0_0_24px_-4px_rgba(99,102,241,0.25)]",
    border: "border-indigo-500/20",
  },
  success: {
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-400",
    glow: "shadow-[0_0_24px_-4px_rgba(16,185,129,0.25)]",
    border: "border-emerald-500/20",
  },
  danger: {
    iconBg: "bg-rose-500/10",
    iconColor: "text-rose-400",
    glow: "shadow-[0_0_24px_-4px_rgba(244,63,94,0.25)]",
    border: "border-rose-500/20",
  },
  warning: {
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-400",
    glow: "shadow-[0_0_24px_-4px_rgba(245,158,11,0.25)]",
    border: "border-amber-500/20",
  },
  neutral: {
    iconBg: "bg-slate-500/10",
    iconColor: "text-slate-400",
    glow: "shadow-[0_0_24px_-4px_rgba(148,163,184,0.15)]",
    border: "border-slate-700/50",
  },
};

export function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = "primary",
  trend,
  isRestricted = false,
  restrictedMessage = "Solo Administrador",
}: KPICardProps) {
  const currentVariant = variantStyles[variant];

  if (isRestricted) {
    return (
      <div className="glass-panel rounded-2xl p-5 relative overflow-hidden border border-slate-800/80 transition-all duration-300">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </span>
          <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 text-slate-500">
            <Lock className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-4 flex flex-col justify-center py-2">
          <div className="text-sm font-semibold text-slate-400 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400/80 animate-pulse" />
            <span>{restrictedMessage}</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Campo financiero protegido por RBAC estructural.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`glass-panel rounded-2xl p-5 relative overflow-hidden border transition-all duration-300 hover:scale-[1.01] hover:border-slate-700/80 ${currentVariant.border} ${currentVariant.glow}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </span>
          <div className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight mt-1.5 font-mono">
            {value}
          </div>
        </div>

        <div
          className={`p-3 rounded-xl ${currentVariant.iconBg} border ${currentVariant.border} ${currentVariant.iconColor} transition-transform duration-200`}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {(subtitle || trend) && (
        <div className="mt-3.5 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
          {subtitle && <span>{subtitle}</span>}
          {trend && (
            <span
              className={`font-semibold flex items-center gap-0.5 ${
                trend.isPositive ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {trend.isPositive ? "+" : ""}
              {trend.value} {trend.label || ""}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
