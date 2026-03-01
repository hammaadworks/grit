# Grit: AI-Native Project Context & LLM Guide

> [!IMPORTANT]
> This file is the primary source of truth for AI agents. It contains the technical DNA, architectural constraints, and behavioral rules of Grit.

## 1. Project Identity
Grit is a Python CLI wrapper for `git commit`.
- **Core Value:** Maintains a consistent GitHub contribution graph by distributing real work across a timeline.
- **Paradigm:** Intercepts `git commit`, calculates the optimal `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`, and executes the native binary.
- **Stack:** Python (>=3.10), Typer (CLI), Rich (UI), SQLite (State), uv (Package Manager).

## 2. Technical Architecture

### A. The Atomic State (SQLite)
- **Location:** `~/.config/grit/state.db`
- **Tables:**
  - `config`: KV pairs (`daily_target`, `start_date`, `github_username`).
  - `commits`: `date` (PK, YYYY-MM-DD), `count` (INT).
- **Invariants:** 
  - Never use JSON/YAML for state to prevent race conditions.
  - State only increments if `git commit` exit code is `0`.

### B. The O(1) Allocator (Recursive CTE)
Instead of Python loops, we use a single SQL query to find the first available date matching the target.
- **Rules:** 1. Today (if space) -> 2. Past (earliest first) -> 3. Future.
- **Query:** Uses a Recursive Common Table Expression bounded to `+365` days to prevent hangs.

### C. Self-Healing Sync Engine
- **Local:** Parses `git log --format="%ad" --date=short`.
- **Remote:** Scrapes public GitHub contribution grid (no API tokens required).
- **Merge Rule:** `MAX(internal_db, local_git, remote_github)`. We never overwrite with lower numbers.

### D. Versioning & Update Logic
- **Sourcing:** `__version__` is defined in `src/grit/__init__.py`.
- **Update Engine:** `src/grit/updater.py` performs a daily background check against the remote `pyproject.toml`.
- **Environment Awareness:** Detects `uv` vs `pip` to provide the correct upgrade command (`uv tool upgrade grit` or `pip install -U grit`).
- **Notification:** `grit status` triggers the check and displays a "New Release" banner if a mismatch is detected.

### E. AI-Native Commit Generation
- **Philosophy:** Zero vendor lock-in. Supports any LLM (Ollama, Claude, Groq, OpenAI) via configurable endpoints.
- **Implementation:** `src/grit/ai.py` handles the payload construction and Conventional Commit enforcement.
- **Wizard Integration:** The zero-arg `grit commit` wizard allows users to trigger auto-generation based on the current staged diff.

## 3. Development Workflow (The "Grit Way")
- **Dependency Management:** `uv` is mandatory. Use `uv sync` and `uv run`.
- **TDD:** No feature or bug fix is accepted without a reproducing test in `tests/`.
- **Mocking:** Always mock `subprocess.run` and `pathlib` in unit tests.
- **CLI UX:**
  - Errors must go to `stderr`.
  - Use Rich for dashboards.
  - Provide non-interactive flags (`--target`, `--force`) for all prompts.

## 4. Troubleshooting & Edge Cases
- **`--amend`:** Grit intercepts and warns users that amends do not count as new commits.
- **Timezones:** `executor.py` generates local system timestamps for both date variables.
- **Scraper Lag:** GitHub's public graph can lag by ~10 minutes.
- **Infinite Loops:** The date allocator is bounded to 1 year forward.

## 5. Command Reference
- `grit config`: Wizard & headless updates.
- `grit commit <args>`: Transparent passthrough.
- `grit status`: Progress dashboard + future forecast.
- `grit sync`: Multi-source state alignment.
- `grit ungrit`: Secure teardown.

