"use client";

import React from "react";
import { TrendingDown, TrendingUp, BarChart2, History } from "lucide-react";

export type ReportTabId = "shrinkage" | "goods_received" | "net_balance" | "audit_history";

export interface TabItem {
  id: ReportTabId;
  label: string;
  icon: React.ElementType;
}

export const REPORT_TABS: TabItem[] = [
  {
    id: "shrinkage",
    label: "Pérdidas y Faltantes",
    icon: TrendingDown,
  },
  {
    id: "goods_received",
    label: "Ingresos y Altas",
    icon: TrendingUp,
  },
  {
    id: "net_balance",
    label: "Balance Neto Diario",
    icon: BarChart2,
  },
  {
    id: "audit_history",
    label: "Historial de Auditoría",
    icon: History,
  },
];

export interface ReportsTabNavigationProps {
  activeTab: ReportTabId;
  onTabChange: (tabId: ReportTabId) => void;
}

export function ReportsTabNavigation({
  activeTab,
  onTabChange,
}: ReportsTabNavigationProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <nav
        className="flex overflow-x-auto divide-x divide-slate-100 no-scrollbar"
        aria-label="Pestañas de Reportes"
      >
        {REPORT_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange(tab.id)}
              className={`flex-1 min-w-[200px] flex items-center justify-center gap-2.5 px-5 py-3.5 text-xs sm:text-sm font-semibold transition-all relative border-b-2 cursor-pointer ${
                isActive
                  ? "text-[#0F2C59] border-[#0F2C59] bg-slate-50/50"
                  : "text-slate-500 border-transparent hover:text-slate-800 hover:bg-slate-50/30"
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? "text-[#0F2C59]" : "text-slate-400"
                }`}
              />
              <span className="whitespace-nowrap">{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
