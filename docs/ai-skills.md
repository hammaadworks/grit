# 🤖 Grit AI-Native Skills & Agentic Context

Grit is developed with an AI-first mindset, leveraging a suite of specialized agentic skills to maintain high engineering standards across its Python and TypeScript codebases.

## 🛠 Core AI Skills

The following specialized skills are used by AI agents (like Gemini CLI) to build, refactor, and maintain Grit:

### 🖥 `cli-ux-designer`
Used to craft the Typer-based terminal interface. This skill ensures:
- **Consistent Iconography:** Precise use of ANSI symbols (✓, ✗, ✦).
- **Logical Flow:** Clear command structures and help text.
- **Rich Dashboards:** High-density, readable layouts using the `Rich` library.

### 🎨 `ui-ux-pro-max`
Powering the Next.js landing page and the built-in `grit dashboard`.
- **Bento Grid:** Ensures a modular, modern layout.
- **Glassmorphism:** Applies high-fidelity backdrop filters and borders.
- **Responsiveness:** Maintains visual integrity across screen sizes.

### 🧹 `clean-code`
Enforces the principles of "Clean Code" by Robert C. Martin.
- **Surgical Refactoring:** Consolidating logic into clean abstractions.
- **Meaningful Naming:** Variables and functions that explain their intent.
- **SOLID Principles:** Ensuring single responsibility and decoupled architectures.

### 🧠 `brainstorming`
Used during the research phase for every major feature (like the `grit spread` or `grit sync` logic) to explore user intent and edge cases before implementation.

### ✍️ `writing-plans`
Mandatory for multi-step tasks. Every significant change starts with a grounded implementation plan to ensure safety and precision.

## 🔬 AI Project Snapshot (`docs/llms.md`)

AI agents are bootstrapped with `docs/llms.md`, which contains the "Technical DNA" of Grit. This file includes:
- **Architectural Invariants:** (e.g., SQLite for state, never JSON).
- **Core Algorithms:** (The O(1) SQL CTE allocator).
- **Development Workflows:** (uv mandatory, TDD requirement).

By keeping this file updated, we ensure that every AI agent that joins the project starts with senior-level context on day zero.
