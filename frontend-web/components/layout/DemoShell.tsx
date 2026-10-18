"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export interface DemoShellProps {
  children: React.ReactNode;
}

export function DemoShell({ children }: DemoShellProps) {
  const { currentUser } = useDataClient();
  const router = useRouter();
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);

  useEffect(() => {
    if (!currentUser) {
      router.push("/login");
    }
  }, [currentUser, router]);

  if (!currentUser) {
    return null; // or a loader
  }

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-slate-50 text-slate-900 antialiased selection:bg-indigo-500 selection:text-white">
      {/* Collapsible Left Navigation Sidebar */}
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      {/* Main Column */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative bg-slate-50">
        {/* Top Header */}
        <TopBar onMenuToggle={() => setMobileSidebarOpen((prev) => !prev)} />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 space-y-6 pb-[calc(1rem+env(safe-area-inset-bottom))]">
          {children}
        </main>
      </div>
    </div>
  );
}
