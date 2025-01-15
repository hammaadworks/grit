# Grit: AI-Native Project Context & LLM Guide

> [!IMPORTANT]
> This file is the primary source of truth for AI agents (CommitScribe). It contains the technical DNA, architectural constraints, and behavioral rules of Grit.

## 1. Project Identity
Grit is a professional CLI utility that intelligently distributes git commits to maintain a consistent contribution graph.
- **Core Value:** Maintains an unbreakable GitHub streak by distributing real work across an optimized timeline.
- **Paradigm:** Intercepts `git commit`, calculates the optimal `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`, and executes the native binary.
- **Stack:** Python (>=3.10), Typer (CLI), Rich (UI), SQLite (State), Pydantic AI (CommitScribe), Loguru (Logging), uv (Package Manager).

## 2. Technical Architecture

### A. The Atomic State (SQLite)
- **Location:** `~/.grit/state.db`
- **Tables:**
  - `config`: KV pairs (`daily_target`, `start_date`, `github_username`).
  - `commits`: `date` (PK, YYYY-MM-DD), `count` (INT).
- **Invariants:** 
  - Never use JSON/YAML for state to prevent race conditions.
  - State only increments if `git commit` exit code is `0`.

### B. The O(1) Allocator (Recursive CTE)
Instead of expensive Python loops, we use a single SQL query to find the first available date matching the target.
- **Rules:** 1. Today (if space) -> 2. Past (earliest first) -> 3. Future.
- **Query:** Uses a Recursive Common Table Expression bounded to `+365` days to prevent hangs.

### C. Self-Healing Sync Engine
- **Local:** Parses `git log --format="%ad" --date=short`.
- **Remote:** Scrapes public GitHub contribution grid.
- **Merge Rule:** `MAX(internal_db, local_git, remote_github)`. We never overwrite with lower numbers.

### D. CommitScribe AI (Pydantic AI)
- **Persona:** Distinguished System Architect.
- **Implementation:** `src/grit/ai.py` uses Pydantic AI for structured commit message generation.
- **Requirements:** Every message MUST include a technical body with RATIONALE, IMPACT, and FUTURE implications.
- **Guardrails:** Uses Pydantic models to ensure the header follows `type(scope): message` format.

### E. Professional Logging (Loguru)
- **Configuration:** `src/grit/logger.py` handles system-wide logging.
- **Rotation:** Automatically rotates and compresses logs in `~/.grit/logs/`.
- **Global Control:** The `--logs` flag enables detailed console output across all Grit commands.

## 3. Development Workflow (The "Grit Way")
- **Dependency Management:** `uv` is mandatory. Use `uv sync` and `uv run`.
- **TDD:** No feature or bug fix is accepted without a reproducing test in `tests/`.
- **Mocking:** Always mock `subprocess.run` and `pathlib` in unit tests.
- **CLI UX:**
  - Errors must go to `stderr`.
  - Use Rich for high-fidelity dashboards.
  - Provide non-interactive flags for all prompts.

## 4. Troubleshooting & Edge Cases
- **`--amend`:** Grit intercepts and warns users that amends do not count as new commits.
- **Timezones:** `executor.py` generates local system timestamps for both date variables.
- **Scraper Lag:** GitHub's public graph can lag by ~10 minutes.
- **Infinite Loops:** The date allocator is bounded to 1 year forward.

## 5. Command Reference
- `grit config`: Settings management with --logs support.
- `grit commit`: Interactive wizard with CommitScribe AI analysis.
- `grit status`: Progress dashboard + future forecast.
- `grit sync`: Multi-source (Local/Remote) state reconciliation.
- `grit log`: Human-readable enhanced git log.
- `grit spread`: Historical redistribution.
- `grit undo`: Safely revert last commit and state.
- `grit ungrit`: Secure decommission.
