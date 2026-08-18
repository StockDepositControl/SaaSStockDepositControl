/**
 * Audit Global Design Tokens
 * Source of truth for color palette, typography, spacing, and visual elevation.
 * Extracted from Figma Design File 4CYjLgmWy7JyhRGrAtpEjH
 */

export const colors = {
  // Base Surface / Backgrounds
  background: {
    base: "#0B0F19", // Deep space dark background
    surface: "#0F172A", // Slate 900 primary cards
    surfaceElevated: "#1E293B", // Slate 800 hover / elevated cards
    surfaceMuted: "#090D16", // Slate 950 deep inset background
  },

  // Primary Accent (Audit Brand)
  primary: {
    50: "#EEF2FF",
    100: "#E0E7FF",
    200: "#C7D2FE",
    300: "#A5B4FC",
    400: "#818CF8",
    500: "#6366F1", // Brand Accent Indigo
    600: "#4F46E5",
    700: "#4338CA",
    800: "#3730A3",
    900: "#312E81",
  },

  // Text Hierarchy
  text: {
    primary: "#F8FAFC", // Slate 50
    secondary: "#94A3B8", // Slate 400
    muted: "#64748B", // Slate 500
    disabled: "#475569", // Slate 600
    inverse: "#0B0F19",
  },

  // Semantic Movement & Audit Discrepancies
  semantic: {
    // Alta (Surplus / Positive discrepancy)
    alta: {
      text: "#34D399",
      bg: "rgba(6, 78, 59, 0.35)",
      border: "rgba(5, 150, 105, 0.4)",
      badge: "#10B981",
    },
    // Baja (Deficit / Shrinkage / Loss)
    baja: {
      text: "#F87171",
      bg: "rgba(127, 29, 29, 0.35)",
      border: "rgba(220, 38, 38, 0.4)",
      badge: "#EF4444",
    },
    // Sin Acción (Exact match / Routine)
    sinAccion: {
      text: "#94A3B8",
      bg: "rgba(30, 41, 59, 0.5)",
      border: "rgba(71, 85, 105, 0.4)",
      badge: "#64748B",
    },
    // FEFO Expiration Tiers
    fefo: {
      critical: {
        label: "Crítico (≤30 días)",
        color: "#EF4444",
        bg: "rgba(239, 68, 68, 0.15)",
        border: "rgba(239, 68, 68, 0.4)",
      },
      warning: {
        label: "Advertencia (≤60 días)",
        color: "#F59E0B",
        bg: "rgba(245, 158, 11, 0.15)",
        border: "rgba(245, 158, 11, 0.4)",
      },
      attention: {
        label: "Atención (≤90 días)",
        color: "#3B82F6",
        bg: "rgba(59, 130, 246, 0.15)",
        border: "rgba(59, 130, 246, 0.4)",
      },
      safe: {
        label: "Normal (>90 días)",
        color: "#10B981",
        bg: "rgba(16, 185, 129, 0.15)",
        border: "rgba(16, 185, 129, 0.4)",
      },
    },
    // Role Badges
    roles: {
      admin: {
        label: "Administrador",
        color: "#F59E0B",
        bg: "rgba(120, 53, 15, 0.35)",
        border: "rgba(217, 119, 6, 0.5)",
      },
      supervisor: {
        label: "Supervisor",
        color: "#818CF8",
        bg: "rgba(49, 46, 129, 0.35)",
        border: "rgba(99, 102, 241, 0.5)",
      },
      auditor: {
        label: "Auditor",
        color: "#34D399",
        bg: "rgba(6, 78, 59, 0.35)",
        border: "rgba(5, 150, 105, 0.5)",
      },
    },
  },

  // Glassmorphism System
  glass: {
    bg: "rgba(15, 23, 42, 0.72)",
    bgElevated: "rgba(30, 41, 59, 0.75)",
    border: "rgba(255, 255, 255, 0.07)",
    borderHover: "rgba(99, 102, 241, 0.3)",
    highlight: "rgba(255, 255, 255, 0.03)",
  },
};

export const typography = {
  fontFamily: {
    sans: 'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'var(--font-geist-mono), monospace',
  },
  fontSize: {
    xs: "0.75rem", // 12px
    sm: "0.875rem", // 14px
    base: "1rem", // 16px
    lg: "1.125rem", // 18px
    xl: "1.25rem", // 20px
    "2xl": "1.5rem", // 24px
    "3xl": "1.875rem", // 30px
    "4xl": "2.25rem", // 36px
  },
  fontWeight: {
    normal: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
    extrabold: "800",
  },
};

export const spacing = {
  containerMax: "1440px",
  sidebarWidth: "260px",
  sidebarCollapsed: "72px",
  topBarHeight: "64px",
};

export const radius = {
  sm: "0.375rem", // 6px
  md: "0.5rem", // 8px
  lg: "0.75rem", // 12px
  xl: "1rem", // 16px
  "2xl": "1.25rem", // 20px
  full: "9999px",
};

export const shadows = {
  glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
  card: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
  glowPrimary: "0 0 20px -2px rgba(99, 102, 241, 0.35)",
  glowSuccess: "0 0 20px -2px rgba(16, 185, 129, 0.35)",
  glowDanger: "0 0 20px -2px rgba(239, 68, 68, 0.35)",
};
