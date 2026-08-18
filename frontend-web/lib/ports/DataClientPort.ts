import {
  UserRole,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditEntry,
  AuditResult,
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  MockUser,
} from "../types/domain";

export interface DataClientPort {
  /**
   * Returns articles tailored to the requester's role.
   * If role is ADMINISTRADOR, returns ArticuloAdminView[] with pcio_com_siva.
   * If role is SUPERVISOR or AUDITOR, returns ArticuloPublicView[] without pcio_com_siva.
   */
  getArticulos(role?: UserRole): Promise<ArticuloPublicView[] | ArticuloAdminView[]>;

  /**
   * Search an article by its exact identifier or barcode.
   */
  getArticuloByBarcode(
    barcodeOrId: string,
    role?: UserRole
  ): Promise<ArticuloPublicView | ArticuloAdminView | null>;

  /**
   * Registers a physical audit record for an article, updating stock and audit status.
   */
  registerAudit(entry: AuditEntry): Promise<AuditResult>;

  /**
   * Retrieves live computed KPIs according to the role.
   */
  getKPIs(role?: UserRole): Promise<DashboardKPIsBase | DashboardKPIsAdmin>;

  /**
   * Retrieves full chronological audit logs.
   */
  getAuditLog(): Promise<AuditResult[]>;

  /**
   * Gets current active mock role.
   */
  getCurrentRole(): UserRole;

  /**
   * Switches the active mock role.
   */
  setRole(role: UserRole): void;

  /**
   * Retrieves list of all available mock users.
   */
  getUsers(): Promise<MockUser[]>;

  /**
   * Gets current authenticated mock user.
   */
  getCurrentUser(): Promise<MockUser | null>;

  /**
   * Authenticates with email and password, updating current user & role.
   */
  login(email: string, password?: string): Promise<MockUser>;

  /**
   * Quick-switches current user by ID.
   */
  switchUser(userId: string): void;

  /**
   * Logs out current user, reverting to default role or guest.
   */
  logout(): void;

  /**
   * Resets mock data to initial seed state.
   */
  resetData(): void;
}

