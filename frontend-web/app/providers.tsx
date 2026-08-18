"use client";

import React from "react";
import { MockDataProvider } from "../lib/mocks/MockDataContext";
import { UserRole } from "../lib/types/domain";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MockDataProvider initialRole={UserRole.ADMINISTRADOR}>
      {children}
    </MockDataProvider>
  );
}
