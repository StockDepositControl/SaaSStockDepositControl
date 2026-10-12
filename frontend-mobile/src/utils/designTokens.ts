/**
 * Mobile Design Tokens Adapter
 * Re-exports & adapts design tokens from shared/design-tokens for the mobile client.
 */

export const colors = {
  // Base Surface / Backgrounds (Warehouse high-contrast light theme)
  background: {
    base: '#F8FAFC', // Slate 50 canvas
    surface: '#FFFFFF', // Pure white primary card
    surfaceElevated: '#F1F5F9', // Slate 100 secondary
    surfaceMuted: '#E2E8F0', // Slate 200 border/divider
    darkSurface: '#111827', // Charcoal 900 header / chrome
    drawerSurface: '#161926', // Deep navy drawer background
    drawerItemActive: '#252B43', // Active drawer item
  },

  // Primary Audit Blue Accent
  primary: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    500: '#1A56DB', // Brand Primary Action Blue
    600: '#1E40AF',
    700: '#1D4ED8',
  },

  // Text Hierarchy
  text: {
    primary: '#0F172A', // Slate 900
    secondary: '#475569', // Slate 600
    muted: '#64748B', // Slate 500
    disabled: '#94A3B8', // Slate 400
    inverse: '#FFFFFF',
    danger: '#DC2626',
    success: '#047857',
    warning: '#B45309',
  },

  // Semantic Movement & Audit Discrepancies
  semantic: {
    alta: {
      text: '#047857',
      bg: '#D1FAE5',
      dot: '#059669',
      border: '#A7F3D0',
      label: 'Alta',
    },
    baja: {
      text: '#B91C1C',
      bg: '#FEE2E2',
      dot: '#DC2626',
      border: '#FECACA',
      label: 'Baja',
    },
    sinAccion: {
      text: '#475569',
      bg: '#F1F5F9',
      dot: '#64748B',
      border: '#E2E8F0',
      label: 'Sin Acción',
    },
    fefo: {
      critical: {
        text: '#B91C1C',
        bg: '#FEF2F2',
        border: '#DC2626',
        tag: 'PRÓXIMO',
      },
      expired: {
        text: '#B91C1C',
        bg: '#FEF2F2',
        border: '#DC2626',
        tag: 'VENCIDO',
      },
      safe: {
        text: '#047857',
        bg: '#D1FAE5',
        border: '#10B981',
        tag: 'NORMAL',
      },
    },
    roles: {
      auditor: {
        bg: '#E2E8F0',
        text: '#1E293B',
        label: 'AUDITOR',
      },
      supervisor: {
        bg: '#E0E7FF',
        text: '#3730A3',
        label: 'SUPERVISOR',
      },
    },
  },
} as const;

export const spacing = {
  minTouchTarget: 48, // 48dp minimum warehouse target
  cardPadding: 16,
  screenPadding: 16,
  itemGap: 12,
} as const;
