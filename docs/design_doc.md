# 🎨 Grit Unified Design System

This document serves as the absolute "Frozen" source of truth for the visual identity, UI patterns, and brand standards across all Grit products: CLI, Web Dashboard, and Documentation.

## 1. Core Palette (Midnight Teal)

Grit uses a high-contrast, OLED-optimized palette built on extremely dark teals and vibrant accents.

| Role | Color | HSL / Hex | Usage |
|------|-------|-----------|-------|
| **Background** | Deep Midnight | `hsl(180 100% 2%)` / `#000505` | Page body, terminal background |
| **Card** | Surface | `hsl(180 100% 4%)` / `#000a0a` | Bento cards, sidebar, code blocks |
| **Primary** | Vibrant Teal | `hsl(175 84% 45%)` / `#14b8a6` | Buttons, accents, optimization bars |
| **Success** | Emerald | `hsl(142 70% 45%)` / `#10b981` | Completed goals, synced status |
| **Border** | Stroke | `hsl(180 50% 15%)` / `#133838` | Card outlines, dividers |
| **Text Main** | Frost White | `hsl(174 100% 98%)` / `#f0fdfa` | Headings, primary content |
| **Text Dim** | Slate Gray | `hsl(174 20% 65%)` / `#94a3b8` | Subtitles, labels, descriptions |

## 2. Typography

- **Interface:** `Inter` (Variable). Priority: Extra Bold for metrics, Medium for navigation.
- **Data/Code:** `JetBrains Mono` or `Fira Code`. Use for commit hashes, date strings, and logs.

## 3. UI Architecture (The Bento Grid)

All interfaces must follow a modular, "Bento" layout:
- **Border Radius:** `0.75rem` (12px) for cards, `1rem` (16px) for larger sections.
- **Spacing:** `1.5rem` (24px) grid gap.
- **Shadows:** Avoid soft blurs. Use 1px borders (`var(--border)`) for definition.

## 4. The "Fun" Rule (Identity & Media)

Grit is professional but personality-driven.
- **Media Asset:** Every dashboard or documentation header MUST feature a relevant high-quality media asset (Anime coding GIF or technical meme).
- **Placement:** Positioned immediately following the primary heading.

## 5. CLI Branding

The terminal interface must mirror the web design system:
- **Logo art:** Apple-style bold ASCII.
- **Colors:** Use `bright_cyan` for Teal accents and `spring_green3` for Success states.
- **Layout:** Tables with minimal padding and clear vertical hierarchy.

## 6. Dashboard Integrity

- **OLED Black:** All backgrounds must be `#000000` or `#000505`.
- **Live State:** Every UI element must show its sync status (e.g., `ENGINE_SYNCED`).
- **Real-time:** Use cache-busting on all API calls to ensure the database is the instantaneous source of truth.
