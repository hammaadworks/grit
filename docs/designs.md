# 🎨 Billion Dollar Design System (Grit)

This document defines the official visual identity and UI/UX standards for Grit. Adhering to these rules ensures that Grit remains a premium, high-fidelity tool that provides a delightful developer experience.

## 1. Core Palette

Grit uses a "Midnight High-Contrast" palette, optimized for dark-mode terminals and modern web browsers.

| Name | Role | Terminal | Hex |
|------|------|----------|-----|
| **Brand** | Primary Highlights | `bright_cyan` | `#00e5ff` |
| **Success** | Completion / Positive | `spring_green3` | `#00ff87` |
| **Warning** | Attention / ETA | `gold1` | `#ffd700` |
| **Error** | Destruction / Fatal | `deep_pink3` | `#ff007f` |
| **Accent** | Secondary Details | `bright_cyan` | `#00e5ff` |

## 2. Typography

Grit prioritizes readability and "hacker aesthetic."

- **Heading & UI:** `Inter` (Sans-serif). Use bold weights for headers.
- **Code & Data:** `Fira Code` (Monospace). Use for commit hashes, date strings, and terminal tables.

## 3. UI Components (Web Dashboard)

The built-in dashboard (`grit dashboard`) utilizes a "Glassmorphism" style.

### Glass Cards
- **Background:** `rgba(30, 41, 59, 0.7)` (Slate 800 at 70% opacity).
- **Blur:** `12px` backdrop filter.
- **Border:** `1px solid rgba(255, 255, 255, 0.1)`.
- **Corner Radius:** `1rem` (16px).

### Progress Bars
- **Container:** Rounded pill shape with subtle dark background.
- **Fill:** Gradient from `Brand` to `Success`.
- **Animation:** Linear ease-out on load.

### Charts
- **Velocity Chart:** Bar chart using the `Brand` color with rounded corners.
- **Target Line:** Dashed line representing the daily goal.

## 4. UX Principles

1. **Zero Latency Feel:** Every CLI interaction should feel instantaneous.
2. **High Information Density:** Use tables and grids to show a lot of data without clutter.
3. **Interactive Pickers:** Use arrow-key navigation for configuration and file staging.
4. **Visual Feedback:** Use icons (Lucide/SVG) and colors to communicate status immediately.
5. **Brand Consistency:** The terminal output must mirror the web dashboard's color logic exactly.

## 5. Media Rules

As per our internal "Fun" rule:
- Documentation pages should include relevant anime typing GIFs or clean coding memes to maintain a lighthearted but high-performance vibe.
