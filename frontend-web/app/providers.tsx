"use client";

import React from "react";
import { ApiDataProvider } from "../lib/context/ApiDataContext";
import { MockDataProvider } from "../lib/mocks/MockDataContext";
import { UserRole } from "../lib/types/domain";

export function Providers({ children }: { children: React.ReactNode }) {
  const dataSource = process.env.NEXT_PUBLIC_DATA_SOURCE || "api";

  if (dataSource === "mock") {
    return (
      <MockDataProvider initialRole={UserRole.ADMINISTRADOR}>
        {children}
      </MockDataProvider>
    );
  }

  return (
    <ApiDataProvider>
      {children}
    </ApiDataProvider>
  );
}
