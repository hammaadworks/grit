# 🎨 Grit Brand & Design System

This document serves as the absolute source of truth for the visual identity, UI patterns, and brand standards across all Grit products: CLI, Web Dashboard, and Documentation.

## 1. Core Palette (Midnight High-Contrast)

Grit uses a high-contrast, OLED-optimized palette built on deep midnight teals and vibrant, "sacred" accents.

| Role | Color Name | Terminal | Hex | Usage |
|------|------------|----------|-----|-------|
| **Primary/Brand** | Vibrant Teal | `bright_cyan` | `#00e5ff` | Buttons, accents, optimization bars |
| **Success** | Spring Green | `spring_green3` | `#00ff87` | Completed goals, synced status |
| **Warning** | Gold | `gold1` | `#ffd700` | Attention, ETA, warnings |
| **Error** | Deep Pink | `deep_pink3` | `#ff007f` | Destruction, fatal errors, deletes |
| **Background** | Deep Midnight | - | `#000505` | Page body, terminal background |
| **Card/Surface** | Surface | - | `#000a0a` | Bento cards, sidebar, code blocks |
| **Border** | Stroke | - | `#133838` | Card outlines, dividers |

> [!IMPORTANT]
> **The Purple Rule:** Never use purple or other colors that deviate from the core teal identity. `bright_cyan` is the core identity.

## 2. Typography

Grit prioritizes readability and a "premium hacker" aesthetic.

- **Interface:** `Inter` (Variable). Priority: Extra Bold for metrics, Medium for navigation.
- **Data/Code:** `JetBrains Mono` or `Fira Code`. Use for commit hashes, date strings, and logs.

## 3. UI Architecture (The Bento Grid)

All interfaces (Web & CLI) follow a modular, "Bento" layout:
- **Border Radius:** `0.75rem` (12px) for cards, `1rem` (16px) for larger sections.
- **Spacing:** `1.5rem` (24px) grid gap.
- **Shadows:** Avoid soft blurs. Use 1px borders (`var(--border)`) for definition.
- **Glassmorphism:** The dashboard uses `12px` backdrop filters with `rgba(30, 41, 59, 0.7)` backgrounds.

## 4. The "Fun" Rule (Identity & Media)

Grit is professional but personality-driven. Documentation and dashboards should not be a boring wall of text.
- **Media Asset:** Every major section landing page or dashboard header MUST feature a relevant high-quality media asset (Anime coding GIF or technical meme).
- **Placement:** Positioned immediately following the primary heading.
- **Vibe:** "Hackerman", anime typing, and dog-coding memes are preferred.

## 5. CLI Branding

The terminal interface must mirror the web design system exactly:
- **Logo art:** Apple-style bold ASCII.
- **Iconography:** Use consistent symbols (✓ for success, ✗ for error, ! for warning, ✦ for highlights).
- **Layout:** Tables with minimal padding and clear vertical hierarchy using `Rich`.

## 6. UX Principles

1. **Zero Latency Feel:** Every interaction should feel instantaneous. Use SQLite for O(1) lookups.
2. **High Information Density:** Use tables and grids to show a lot of data without clutter.
3. **Interactive Pickers:** Use arrow-key navigation for configuration and file staging in the CLI.
4. **Visual Feedback:** Use icons and colors to communicate status immediately.
5. **Real-time:** Use cache-busting on all API calls to ensure the database is the instantaneous source of truth.
