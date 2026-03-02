---
hide:
  - navigation
  - toc
---

# 🧱 Grit

**The intelligent `git commit` wrapper that keeps your GitHub graph perfectly consistent with a unified backdated history.**

![Anime Typing Hacker Meme](https://media.tenor.com/81Bta-H1NqIAAAAC/anime-typing.gif)

<div class="grid cards" markdown>
-   **No More Ghost Towns**
    Set a daily commit target. Grit mathematically distributes your commits across a timeline.
-   **Consistent History**
    Grit modifies both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to ensure a consistent backdated history on GitHub.
-   **Self-Healing**
    Bypassed Grit by accident? `grit sync` merges your local Git log and public GitHub profile to prevent overwriting past activity.
</div>

---

## 🛑 The Problem: You Code, But Your Graph Doesn't Show It

You are a developer. You write code. But maybe you batch your commits at the end of the week, or you work on personal projects in intense, sporadic bursts. 

The result? A GitHub contribution graph that looks sparse, even though you are putting in the hours. 

You *could* use scripts that randomly generate 100 fake commits and force-push them to a dummy repository. But those look artificial to recruiters, and they don't reflect your actual work. You *could* manually change your system clock before every commit, but that is tedious and prone to error.

## 💡 The Solution: Meet Grit

**Grit** is a terminal-based CLI wrapper that intercepts your `git commit` commands. 

Instead of generating fake work, Grit takes your *real* work and intelligently assigns it to the most optimal date based on a target you set (e.g., "I want 3 commits per day"). 

```bash
# You type this:
$ grit commit -m "feat: add user authentication"

# Grit does the math in 0.001s and executes this:
GIT_AUTHOR_DATE="2024-03-24 14:30:00" git commit -m "feat: add user authentication"
```

## ⚙️ How It Works (The "Way" It's Built)

Grit is built on modern Python (`uv`, `typer`, `rich`) and is engineered for speed and safety. 

### 1. The O(1) SQLite Allocator
Grit does not use slow JSON files. It uses a strictly normalized SQLite database to prevent race conditions when you commit from multiple terminal panes. To find the "next available date", it executes a lightning-fast Recursive Common Table Expression (CTE) entirely inside the SQL engine. No Python loops. No waiting.

### 2. Frictionless Passthrough
Grit is completely transparent. Want to bypass git hooks? Run `grit commit -m "wip" --no-verify`. Need to amend? Run `grit commit --amend`. Grit safely passes every single argument directly to the underlying `git` binary using `subprocess.run`.

### 3. The Self-Healing Sync Engine
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
uv tool install grit
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

/CD setups, and uninstallation.

</div>

ps, and uninstallation.

</div>

