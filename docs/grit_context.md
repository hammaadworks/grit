# Grit CLI Context & Memory Snapshot

## Date of Snapshot
March 22, 2026

## What We Have Done So Far
- **Brainstormed and refined the core concept:** Designed a smart, terminal-based CLI wrapper (`grit`) that intercepts `git commit` to dynamically inject `GIT_AUTHOR_DATE`, distributing commits intelligently across a timeline to meet a `daily_target` without rewriting history or `GIT_COMMITTER_DATE`.
- **Architected the State Engine:** Decided to use a local **SQLite database** (`~/.config/grit/state.db`) instead of JSON. This provides O(1) lightning-fast querying for the "next available date", prevents concurrency issues (file locking), and keeps the schema minimal.
- **Defined the Command Ecosystem & UX:** Settled on a Typer/Rich-powered CLI with an interactive setup menu (`grit`), a beautiful manual (`grit info`), a dashboard (`grit status`), the core wrapper (`grit commit`), and a cleanup utility (`grit ungrit`).
- **Solved the "Cold Start" & Desync Problem:** Designed a unified `grit sync` strategy. On setup, Grit will silently scrape the user's public GitHub contribution graph to pre-fill the database. The `sync` command will merge this global GitHub data with the local repository's `git log` using a `MAX(current, new)` SQL constraint to ensure Grit never overwrites past activity.
- **Documented Requirements and Tests:** Generated a comprehensive Product Requirements Document (`grit_prd.md`) and a rigorous Test Plan (`grit_test_plan.md`) covering unit, integration, and CLI behavior tests.

## Key Decisions Made
1.  **Wrapper Paradigm:** Grit wraps `git commit` and passes arguments through. It only increments its internal state if the underlying `git` command exits successfully (exit code 0).
2.  **No Global Git Config Scraping:** To keep things lean and robust, Grit stores only `start_date`, `daily_target`, and `github_username` in its DB. It delegates identity (Name/Email) entirely to native Git.
3.  **No Private Data Scraping (For Now):** We will only scrape public GitHub data during the cold start/sync to avoid the friction and security risks of handling Personal Access Tokens (PATs).
4.  **No Randomization:** The injected timestamp will simply be the target `YYYY-MM-DD` combined with the current system time (`HH:MM:SS`).

## What Needs to be Done in the Next Session
1.  **Phase 1: Project Scaffolding & Setup**
    *   Create the Python virtual environment and project directory.
    *   Install core dependencies: `typer`, `rich`, `httpx`, and `beautifulsoup4` (for scraping the GitHub graph).
2.  **Phase 2: State Engine & Config (Test-Driven)**
    *   Implement `state.py` (SQLite DB initialization and querying).
    *   Implement the interactive setup prompt (`grit config`) that writes to the DB.
3.  **Phase 3: The Allocator Engine**
    *   Write the O(1) SQL query logic to find the next available date based on the daily target.
4.  **Phase 4: The Sync Engine**
    *   Implement the GitHub public graph scraper.
    *   Implement the local `git log` parser.
    *   Write the `MAX()` merge logic into the DB.
5.  **Phase 5: The CLI Wrapper**
    *   Implement `grit commit`, injecting the environment variables and safely passing arguments via `subprocess.run`.

## Operational Rules
- **Rule:** Always update this context file (`docs/grit_context.md`) at the end of the session when the user prompts to update it.