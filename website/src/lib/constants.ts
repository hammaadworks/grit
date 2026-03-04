/**
 * @file lib/constants.ts
 * @description Centralized constants for theme colors, URLs, and UI configuration.
 */

export const SITE_CONFIG = {
  name: "Grit",
  version: "0.7.89",
  repo_url: "https://github.com/hammaadworks/grit",
  releases_url: "https://github.com/hammaadworks/grit/releases",
  pypi_url: "https://pypi.org/project/grit/",
  docs: {
    user: "/docs/user-guide",
    developer: "/docs/developer-guide",
    llms: "https://github.com/hammaadworks/grit/blob/main/docs/llms.md",
  },
} as const;

export const COMMANDS = {
  INSTALL: "uv tool install git2grit",
  CONFIG: "grit config",
  COMMIT: "grit commit -m 'feat: logic'",
  STATUS: "grit status",
  SYNC: "grit sync",
  UNGRIT: "grit ungrit",
} as const;

export const THEME = {
  PRIMARY: "text-primary",
  ACCENT: "text-teal-400",
  BORDER: "border-white/10",
  BG_MUTED: "bg-white/[0.01]",
} as const;
