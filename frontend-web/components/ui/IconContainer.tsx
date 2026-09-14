"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

export type IconContainerVariant = "primary" | "danger" | "warning" | "success";

export interface IconContainerProps {
  icon: LucideIcon;
  variant?: IconContainerVariant;
  className?: string;
}

const variantStyles: Record<IconContainerVariant, string> = {
  primary: "bg-blue-50 text-[#1a56db]",
  danger: "bg-red-50 text-red-600",
  warning: "bg-orange-50 text-orange-500",
  success: "bg-emerald-50 text-emerald-600",
};

export function IconContainer({
  icon: Icon,
  variant = "primary",
  className = "",
}: IconContainerProps) {
  return (
    <div
      className={`w-10 h-10 p-2 rounded-xl flex items-center justify-center shrink-0 ${variantStyles[variant]} ${className}`}
    >
      <Icon className="w-full h-full" strokeWidth={2} />
    </div>
  );
}
