import React from "react";

export interface SummaryKPICardProps {
  title: string;
  amount: string | number;
  quantity?: string | number;
  quantityLabel?: string;
  isLoss?: boolean;
  subtitle?: string;
  icon?: React.ElementType;
}

export function SummaryKPICard({
  title,
  amount,
  quantity,
  quantityLabel = "unidades",
  isLoss = false,
  subtitle,
  icon: Icon,
}: SummaryKPICardProps) {
  const formattedAmount =
    typeof amount === "number"
      ? amount.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : amount;

  return (
    <div
      className={`bg-white p-5 rounded-xl shadow-sm border transition-all ${
        isLoss
          ? "border-slate-200 border-l-4 !border-l-[#EF4444]"
          : "border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">{title}</h3>
        {Icon && (
          <div
            className={`p-2 rounded-lg ${
              isLoss ? "text-[#EF4444] bg-slate-50" : "text-slate-500 bg-slate-50"
            }`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex justify-between items-baseline gap-2">
        <span
          className={`text-2xl font-bold font-mono text-right tracking-tight ${
            isLoss ? "text-red-600" : "text-slate-900"
          }`}
        >
          ${formattedAmount}
        </span>
        {quantity !== undefined && (
          <span className="text-xs text-slate-500 font-medium">
            {quantity} {quantityLabel}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-slate-400 font-medium truncate">{subtitle}</p>
      )}
    </div>
  );
}
