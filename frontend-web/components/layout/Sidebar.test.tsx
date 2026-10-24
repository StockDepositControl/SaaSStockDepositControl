// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sidebar } from "./Sidebar";
import { UserRole } from "@/lib/types/domain";

let mockRole: UserRole = UserRole.AUDITOR;

vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => ({
    currentUser: { id: "U1", name: "Test User", role: mockRole },
    currentRole: mockRole,
    logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard",
}));

describe("Sidebar audit entry", () => {
  it("hides the stock audit link for administrators", () => {
    mockRole = UserRole.ADMINISTRADOR;
    render(<Sidebar />);
    expect(screen.queryByText("Auditoría de Stock")).toBeNull();
  });

  it.each([UserRole.SUPERVISOR, UserRole.AUDITOR])("shows the stock audit link for %s", (role) => {
    mockRole = role;
    render(<Sidebar />);
    expect(screen.getAllByText("Auditoría de Stock").length).toBeGreaterThan(0);
  });
});
