// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import UsersPage from "./page";
import { UserRole, MockUser } from "@/lib/types/domain";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/users",
}));

const mockUseDataClient = vi.fn();
vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => mockUseDataClient(),
}));

describe("UsersPage (Administrator User Management)", () => {
  const mockAdminUser: MockUser = {
    id: "1",
    email: "admin@example.com",
    name: "Admin User",
    role: UserRole.ADMINISTRADOR,
    is_active: true,
  };

  const mockUsersList: MockUser[] = [
    {
      id: "1",
      email: "admin@example.com",
      name: "Admin User",
      role: UserRole.ADMINISTRADOR,
      is_active: true,
    },
    {
      id: "2",
      email: "auditor@example.com",
      name: "Auditor User",
      role: UserRole.AUDITOR,
      is_active: true,
    },
    {
      id: "3",
      email: "supervisor@example.com",
      name: "Supervisor User",
      role: UserRole.SUPERVISOR,
      is_active: false,
    },
  ];

  let mockClient: {
    getUsers: ReturnType<typeof vi.fn>;
    updateUserStatus: ReturnType<typeof vi.fn>;
    updateUserRole: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient = {
      getUsers: vi.fn().mockResolvedValue(mockUsersList),
      updateUserStatus: vi.fn().mockResolvedValue({}),
      updateUserRole: vi.fn().mockResolvedValue({}),
    };
  });

  it("renders 'Acceso Restringido' when user is not ADMINISTRADOR", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "2", role: UserRole.AUDITOR, name: "Auditor User" },
      currentRole: UserRole.AUDITOR,
      client: mockClient,
    });

    render(<UsersPage />);

    expect(screen.getByText("Acceso Restringido")).toBeDefined();
    expect(mockClient.getUsers).not.toHaveBeenCalled();
  });

  it("fetches and renders users table with KPI counters for administrator", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: mockAdminUser,
      currentRole: UserRole.ADMINISTRADOR,
      client: mockClient,
    });

    render(<UsersPage />);

    expect(screen.getByText("Gestión de Personal")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeDefined();
      expect(screen.getByText("auditor@example.com")).toBeDefined();
      expect(screen.getByText("supervisor@example.com")).toBeDefined();
    });

    // Verify KPI counters (total: 3, active: 2, inactive: 1, auditors: 1, supervisors: 1, admins: 1)
    expect(screen.getByText("3")).toBeDefined();
    expect(screen.getByText("2")).toBeDefined();
    expect(screen.getAllByText("1").length).toBe(4);
    expect(screen.getByText("usuarios totales")).toBeDefined();
    expect(screen.getByText("activos")).toBeDefined();
    expect(screen.getByText("inactivos")).toBeDefined();
  });

  it("disables deactivation and role demotion for the active administrator (isMe)", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: mockAdminUser,
      currentRole: UserRole.ADMINISTRADOR,
      client: mockClient,
    });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText("admin@example.com")).toBeDefined();
    });

    // Check "Tú" indicator
    expect(screen.getByText("Tú")).toBeDefined();

    // The deactivation button for isMe must be disabled
    const selfDeactivateBtn = screen.getByLabelText("Desactivar usuario Admin User") as HTMLButtonElement;
    expect(selfDeactivateBtn.disabled).toBe(true);

    // The role select for isMe must be disabled
    const selfRoleSelect = screen.getByLabelText("Rol para Admin User") as HTMLSelectElement;
    expect(selfRoleSelect.disabled).toBe(true);
  });

  it("allows updating another user's role and calls client.updateUserRole", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: mockAdminUser,
      currentRole: UserRole.ADMINISTRADOR,
      client: mockClient,
    });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText("auditor@example.com")).toBeDefined();
    });

    const auditorRoleSelect = screen.getByLabelText("Rol para Auditor User") as HTMLSelectElement;
    expect(auditorRoleSelect.disabled).toBe(false);

    fireEvent.change(auditorRoleSelect, { target: { value: UserRole.SUPERVISOR } });

    expect(mockClient.updateUserRole).toHaveBeenCalledWith("2", UserRole.SUPERVISOR);
  });

  it("allows toggling status for another user and calls client.updateUserStatus", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: mockAdminUser,
      currentRole: UserRole.ADMINISTRADOR,
      client: mockClient,
    });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText("auditor@example.com")).toBeDefined();
    });

    const deactivateBtn = screen.getByLabelText("Desactivar usuario Auditor User");
    fireEvent.click(deactivateBtn);

    expect(mockClient.updateUserStatus).toHaveBeenCalledWith("2", false);
  });

  it("handles update failure with rollback and surfaces error message", async () => {
    mockClient.updateUserStatus.mockRejectedValueOnce(
      new Error("Network connection error")
    );

    mockUseDataClient.mockReturnValue({
      currentUser: mockAdminUser,
      currentRole: UserRole.ADMINISTRADOR,
      client: mockClient,
    });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText("auditor@example.com")).toBeDefined();
    });

    const deactivateBtn = screen.getByLabelText("Desactivar usuario Auditor User");
    fireEvent.click(deactivateBtn);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeDefined();
      expect(screen.getByText("Network connection error")).toBeDefined();
    });

    // Rollback: Auditor User should still have "Desactivar" button
    expect(screen.getByLabelText("Desactivar usuario Auditor User")).toBeDefined();
  });
});
