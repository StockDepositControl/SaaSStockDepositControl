import { ActiveTenantSession, LoginCredentials } from '../types/auth';
import { ArticuloAuditorView, ArticleStockPositionView, CatalogFilterParams, CatalogResult } from '../types/article';
import { AuditEntryRequest, AuditEntryResult, AuditDailyProgress } from '../types/audit';

export interface MobileDataClientPort {
  login(credentials: LoginCredentials): Promise<ActiveTenantSession>;
  logout(): Promise<void>;
  restoreSession(): Promise<ActiveTenantSession | null>;
  getDailyProgress(): Promise<AuditDailyProgress>;
  searchArticles(query: string): Promise<ArticuloAuditorView[]>;
  getArticleCatalog(params?: CatalogFilterParams): Promise<CatalogResult<ArticuloAuditorView>>;
  getArticleStockPosition(articleId: string, depositId?: number): Promise<ArticleStockPositionView>;
  registerAudit(request: AuditEntryRequest): Promise<AuditEntryResult>;
}
