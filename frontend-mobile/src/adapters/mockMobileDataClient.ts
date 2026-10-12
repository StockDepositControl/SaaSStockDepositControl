import AsyncStorage from '@react-native-async-storage/async-storage';
import { MobileDataClientPort } from '../ports/MobileDataClientPort';
import { ActiveTenantSession, LoginCredentials } from '../types/auth';
import { ArticuloAuditorView, ArticleStockPositionView, CatalogFilterParams, CatalogResult } from '../types/article';
import { AuditEntryRequest, AuditEntryResult, AuditDailyProgress } from '../types/audit';
import { DeltaCalculator } from '../services/domain/DeltaCalculator';
import { STORAGE_KEYS } from '../utils/constants';

const INITIAL_ARTICLES: ArticuloAuditorView[] = [
  {
    id_articulo: 'ART-001',
    barcode: '7798010343227',
    barcodes: ['7798010343227'],
    code: '7798010343227',
    des_articulo: 'Ibuprofeno 400mg x 10',
    presentacion: 'Caja x 10 comp.',
    des_marca: 'Bayer',
    des_grupo: 'Analgésicos',
    des_familia: 'Medicamentos',
    id_familia: 'FAM-MED',
    id_grupo: 'GRP-ANA',
    status: 'pending',
    stock_real: 85,
    fefo_expiration_date: '01/03/2026',
    fefo_lot_code: 'LOT-BAY-001',
  },
  {
    id_articulo: 'ART-002',
    barcode: '7798010343228',
    barcodes: ['7798010343228'],
    code: '7798010343228',
    des_articulo: 'Paracetamol 500mg x 20',
    presentacion: 'Caja x 20 comp.',
    des_marca: 'Bayer',
    des_grupo: 'Analgésicos',
    des_familia: 'Medicamentos',
    id_familia: 'FAM-MED',
    id_grupo: 'GRP-ANA',
    status: 'audited',
    stock_real: 120,
    fefo_expiration_date: '15/08/2026',
    fefo_lot_code: 'LOT-BAY-002',
  },
  {
    id_articulo: 'ART-003',
    barcode: '7798010343229',
    barcodes: ['7798010343229'],
    code: '7798010343229',
    des_articulo: 'Amoxicilina 500mg x 12',
    presentacion: 'Caja x 12 comp.',
    des_marca: 'GSK',
    des_grupo: 'Antibióticos',
    des_familia: 'Medicamentos',
    id_familia: 'FAM-MED',
    id_grupo: 'GRP-ANT',
    status: 'pending',
    stock_real: 0,
    fefo_expiration_date: '10/01/2026',
    fefo_lot_code: 'LOT-GSK-003',
  },
  {
    id_articulo: 'ART-004',
    barcode: '7798010343230',
    barcodes: ['7798010343230'],
    code: '7798010343230',
    des_articulo: 'Omeprazol 20mg x 30',
    presentacion: 'Frasco x 30 caps.',
    des_marca: 'Roemmers',
    des_grupo: 'Antiulcerosos',
    des_familia: 'Medicamentos',
    id_familia: 'FAM-MED',
    id_grupo: 'GRP-DIG',
    status: 'pending',
    stock_real: 45,
    fefo_expiration_date: '12/12/2026',
    fefo_lot_code: 'LOT-ROE-004',
  },
  {
    id_articulo: 'ART-005',
    barcode: '7798010343231',
    barcodes: ['7798010343231'],
    code: '7798010343231',
    des_articulo: 'Loratadina 10mg x 10',
    presentacion: 'Caja x 10 comp.',
    des_marca: 'Bagó',
    des_grupo: 'Antialérgicos',
    des_familia: 'Medicamentos',
    id_familia: 'FAM-MED',
    id_grupo: 'GRP-ALE',
    status: 'pending',
    stock_real: 60,
    fefo_expiration_date: '05/04/2026',
    fefo_lot_code: 'LOT-BAG-005',
  },
];

export class MockMobileDataClient implements MobileDataClientPort {
  private articles: ArticuloAuditorView[] = [...INITIAL_ARTICLES];
  private currentSession: ActiveTenantSession | null = null;

  async login(credentials: LoginCredentials): Promise<ActiveTenantSession> {
    const email = credentials.email.trim().toLowerCase();

    // Check for admin prohibition
    if (email.includes('admin')) {
      throw new Error('Acceso denegado: tu perfil no tiene permisos operativos móviles o se encuentra bloqueado.');
    }

    const isSupervisor = email.includes('super');
    const role = isSupervisor ? 'supervisor' : 'auditor';

    const session: ActiveTenantSession = {
      token: 'mock-jwt-token-field-operator',
      email,
      displayName: isSupervisor ? 'Carlos Supervisor' : 'Luis Operario',
      initials: isSupervisor ? 'CS' : 'LO',
      role,
      tenantId: '1',
      branchId: 1,
      depositId: 1,
      userId: isSupervisor ? 2 : 1,
      expiresAtMs: Date.now() + 86400 * 1000,
    };

    this.currentSession = session;
    await AsyncStorage.setItem(
      `${STORAGE_KEYS.SESSION_PREFIX}:1:1`,
      JSON.stringify(session)
    );

    return session;
  }

  async logout(): Promise<void> {
    this.currentSession = null;
    await AsyncStorage.removeItem(`${STORAGE_KEYS.SESSION_PREFIX}:1:1`);
  }

  async restoreSession(): Promise<ActiveTenantSession | null> {
    const raw = await AsyncStorage.getItem(`${STORAGE_KEYS.SESSION_PREFIX}:1:1`);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw) as ActiveTenantSession;
      if (parsed.expiresAtMs > Date.now()) {
        this.currentSession = parsed;
        return parsed;
      }
    } catch {
      // Ignore parse failure
    }
    return null;
  }

  async getDailyProgress(): Promise<AuditDailyProgress> {
    const totalCount = this.articles.length;
    const auditedCount = this.articles.filter((a) => a.status === 'audited').length;
    const pendingCount = totalCount - auditedCount;
    const percentage = totalCount > 0 ? Math.round((auditedCount / totalCount) * 100) : 0;

    return {
      totalCount,
      auditedCount,
      pendingCount,
      percentage,
    };
  }

  async searchArticles(query: string): Promise<ArticuloAuditorView[]> {
    const clean = query.trim().toLowerCase();
    if (!clean) return [];

    return this.articles.filter((a) => {
      return (
        a.barcode.toLowerCase() === clean ||
        a.id_articulo.toLowerCase() === clean ||
        a.code.toLowerCase() === clean ||
        a.des_articulo.toLowerCase().includes(clean)
      );
    });
  }

  async getArticleCatalog(params?: CatalogFilterParams): Promise<CatalogResult<ArticuloAuditorView>> {
    let list = [...this.articles];

    if (params?.search) {
      const s = params.search.trim().toLowerCase();
      list = list.filter(
        (a) =>
          a.des_articulo.toLowerCase().includes(s) ||
          a.barcode.toLowerCase().includes(s) ||
          (a.des_marca && a.des_marca.toLowerCase().includes(s))
      );
    }

    if (params?.status && params.status !== 'all') {
      list = list.filter((a) => a.status === params.status);
    }

    if (params?.criticalOnly) {
      list = list.filter((a) => a.stock_real === 0);
    }

    if (params?.familyId) {
      list = list.filter((a) => a.id_familia === params.familyId);
    }

    return {
      items: list,
      total: list.length,
    };
  }

  async getArticleStockPosition(articleId: string, depositId: number = 1): Promise<ArticleStockPositionView> {
    const article = this.articles.find((a) => a.id_articulo === articleId || a.barcode === articleId);
    if (!article) {
      throw new Error(`Artículo no encontrado: ${articleId}`);
    }

    return {
      id_articulo: article.id_articulo,
      des_articulo: article.des_articulo,
      presentacion: article.presentacion,
      des_marca: article.des_marca,
      des_familia: article.des_familia,
      des_grupo: article.des_grupo,
      id_sucursal: 1,
      id_deposito: depositId,
      stock_real: article.stock_real,
      lotes: article.fefo_lot_code
        ? [
            {
              lote: article.fefo_lot_code,
              vencimiento: article.fefo_expiration_date || null,
              stock_real: article.stock_real,
            },
          ]
        : [],
    };
  }

  async registerAudit(request: AuditEntryRequest): Promise<AuditEntryResult> {
    const article = this.articles.find((a) => a.id_articulo === request.id_articulo);
    if (!article) {
      throw new Error(`Artículo no encontrado: ${request.id_articulo}`);
    }

    const baseline = article.stock_real;
    const computed = DeltaCalculator.compute(baseline, request.stock_fisico_contado);

    // Update in-memory state
    article.status = 'audited';
    article.stock_real = request.stock_fisico_contado;

    return {
      id_articulo: article.id_articulo,
      stock_real: baseline,
      stock_fisico_contado: request.stock_fisico_contado,
      delta_stock: computed.deltaStock,
      tipo_accion: computed.actionType,
      cantidad_afectada: computed.affectedQuantity,
      audit_quantity: request.stock_fisico_contado,
      audit_id: Math.floor(Math.random() * 10000) + 1,
    };
  }
}

export const mockMobileDataClient = new MockMobileDataClient();
