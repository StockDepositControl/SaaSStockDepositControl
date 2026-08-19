import { primitives } from "../primitives";

/**
 * Semantic Sidebar Tokens
 * Contextual design tokens for the navigation sidebar, mapped to foundational primitives.
 */
export const sidebar = {
  background: primitives.charcoal,
  surfaceElevated: primitives.navySoft,
  itemActive: {
    bg: primitives.primary,
    fg: "#FFFFFF", // opacity 100
  },
  itemInactive: {
    fg: "rgba(255, 255, 255, 0.55)", // white / opacity 55
  },
  divider: "rgba(255, 255, 255, 0.07)", // white / opacity 7
  textSecondary: "rgba(255, 255, 255, 0.45)", // white / opacity 45
} as const;

export type SidebarTokens = typeof sidebar;
