# 🎨 Brand & Design Rules

This document outlines the design language, formatting rules, and visual identity for the Grit project and its documentation.

## 1. Visual Identity & Theme
- **Primary Color:** Black
- **Accent Color:** Deep Purple (Light Mode) / Cyan (Dark Mode)
- **Typography:** `Inter` for standard text, `Fira Code` for code blocks and monospace elements.
- **Theme Engine:** `mkdocs-material` (with custom CSS overriding headers to use subtle gradients).

## 2. The "Fun" Rule (Media & Memes)
Documentation should not be a boring wall of text. We embrace internet culture to make reading fun.
- **Rule:** Every major section landing page MUST include at least one high-quality, relevant media asset (Anime GIF, coding meme, or tasteful joke).
- **Placement:** Place the media asset directly under the H1 and subtitle of the page to hook the reader.
- **Vibe:** Keep it lighthearted but professional. "Hackerman", anime typing, and dog-coding memes are excellent choices.

## 3. The Documentation Journey
We guide our users. A user should never reach the bottom of a page and wonder "What do I click next?".
- **Rule:** Every page MUST have a "Where to go next?" section at the bottom.
- **Format:** Use MkDocs Material Grid Cards with explicit `➔` arrows.
- **Footer Navigation:** Native `navigation.footer` is enabled in MkDocs to allow users to click `Next` and `Previous` seamlessly at the bottom right of their screen.

## 4. UI/UX Principles
- **Bite-Sized Information:** Avoid long paragraphs. Use bullet points, bold text for emphasis, and MkDocs Admonitions (`!!! tip`, `!!! warning`, `!!! success`).
- **Interactive Code:** Use tabbed code blocks for different OS instructions (e.g., macOS vs Windows installation).
- **High Contrast:** Ensure all UI elements pass accessibility contrast ratios (especially in the custom Dark Mode palette).