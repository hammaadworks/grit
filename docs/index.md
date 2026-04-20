---
hide:
  - navigation
  - toc
---

# 🧱 Grit

**The intelligent `git commit` wrapper that keeps your GitHub graph perfectly consistent with a unified backdated history.**

![Anime Typing Hacker Meme](../diagrams/anime-typing.gif)

<div class="grid cards" markdown>
-   **No More Ghost Towns**
    Set a daily commit target. Grit mathematically distributes your commits across a timeline.
-   **AI Intelligence Core**
    Generate perfect Conventional Commits using Gemini, OpenAI, or Ollama. Background generation with macOS notifications.
-   **High-Fidelity Dashboard**
    A beautiful, modern web GUI to monitor your pipeline, graph intensity, and velocity.
-   **Self-Healing**
    Bypassed Grit by accident? `grit sync` merges your local Git log and public GitHub profile to prevent overwriting past activity.
</div>

---

## 🛑 The Problem: You Code, But Your Graph Doesn't Show It

You are a developer. You write code. But maybe you batch your commits at the end of the week, or you work on personal projects in intense, sporadic bursts. 

The result? A GitHub contribution graph that looks sparse, even though you are putting in the hours. 

## 💡 The Solution: Meet Grit

**Grit** is a terminal-based CLI wrapper that intercepts your `git commit` commands. 

Instead of generating fake work, Grit takes your *real* work and intelligently assigns it to the most optimal date based on a target you set.

```bash
# You type this:
$ grit commit -m "feat: add user authentication"

# Feeling bored? AI-assisted commit in the background:
$ grit commit --ai
# ✨ AI draft is ready! (macOS Notification)

# Grit does the math in 0.001s and executes this:
GIT_AUTHOR_DATE="2024-03-24 14:30:00" git commit -m "feat: add user authentication"
```

## ⚙️ How It Works (The "Way" It's Built)

### 1. The AI Semantic Engine
Grit integrates with `pydantic-ai` to analyze your staged diffs. It can generate structured Conventional Commit messages (`feat`, `fix`, `docs`, etc.) using advanced LLMs like Gemini 1.5 Flash.

### 2. The O(1) SQLite Allocator
Grit uses a strictly normalized SQLite database to find the "next available date" using a lightning-fast Recursive CTE entirely inside the SQL engine.

### 3. The Web Intelligence Dashboard
Run `grit dash` to launch a local server and visualize your history, future pipeline, and activity velocity in a high-fidelity interface.

### 4. The Self-Healing Sync Engine
What happens if you merge a Pull Request on GitHub, or commit from another computer? Grit's database will fall out of sync. 

To solve this, running `grit sync` will:
1. Parse your local `git log`.
2. Scrape your public GitHub contribution graph (no API tokens required).
3. Merge the data using a strict `MAX(current, new)` rule. Grit will **never** accidentally overwrite a day you have already committed to.

---

## 🚀 Get Started in 60 Seconds

Ready to take control of your contribution graph?

### 1. Install
```bash
uv tool install git2grit
```

### 2. Configure
```bash
grit config
```

### 3. Commit
```bash
grit commit -m "Initial commit"
```

---

## 🗺️ Where to go next?

<div class="grid cards" markdown>

-   :material-book-open-page-variant: **[Read the User Guide ➔](user-guide.md)**
-   :material-palette: **[Brand & Design System ➔](brand.md)**
-   :material-robot: **[AI Skills & Agentic Context ➔](ai-skills.md)**
-   :material-help-circle: **[FAQ & Troubleshooting ➔](faq.md)**
    
    Learn about dashboards, headless CI/CD setups, and uninstallation.

</div>


