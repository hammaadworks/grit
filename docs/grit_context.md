# Grit CLI Context & Memory Snapshot

## Date of Snapshot
March 24, 2026

## What We Have Done So Far
- **Project Scaffolding:** Initialized a `uv` project, set up the `grit` module structure, and configured the CLI entry point in `pyproject.toml`.
- **State Engine & Config:** Built an atomic SQLite-based `StateManager` (`src/grit/state.py`) that handles configuration and commit counts in a robust way to prevent concurrency desyncs. Unit tests written and passing.
- **The Allocator Engine:** Implemented `DateAllocator` (`src/grit/allocator.py`) with a bounded recursive SQL CTE to elegantly find the next available commit date without Python loops. Resolved an initial infinite loop issue by strictly capping the forward scan bound.
- **The Sync Engine:** Implemented `get_local_git_stats` to parse the git log, and a `beautifulsoup4` GitHub scraper (`fetch_github_contributions`) to retrieve public data, merging them via a defensive `MAX(current, new)` strategy in `src/grit/sync.py`.
- **The CLI Wrapper & Execution:** Hooked everything up in `src/grit/cli.py` using Typer and Rich. The CLI acts as a wrapper, generates accurate local timezone timestamps (`src/grit/executor.py`), and increments internal state only on successful Git operations. Comprehensive E2E tests are written.
- **CLI UX Redesign:** Refactored the Typer application based on strict `cli-ux-designer` principles. Added appropriate iconography (✓, ✗, !), routed errors to standard error, and introduced non-interactive headless flags (`--target`, `--start`, `--force`) to ensure scriptability.
- **Testing:** We maintained a test-driven approach throughout. All 19/19 tests passing.
- **CLI Status Dashboard:** Enhanced the `status` command to pull a richer dataset from the SQLite database. It now executes an O(1) query with `LIMIT 5` to forecast the next 3 future commit allocations (dates and counts), and aggregates the total commits achieved in the current month using the `LIKE 'YYYY-MM-%'` constraint.
- **Documentation & Next.js Landing Page:** Migrated from a basic MkDocs setup to a premium, static, client-only Next.js application (`website/` directory). 
  - Implemented high-converting copywriting and an interactive animated terminal component using Framer Motion and Tailwind CSS.
  - Built comprehensive, beautifully styled User and Developer Guides inside the Next.js app using the `mermaid` React integration for detailed architectural diagrams (O(1) sequence flow and the Self-Healing Sync graph).
  - Added explicit guides for local development execution (`uv run grit`) and global deployment (`uv tool install`).

## Key Decisions Made
1.  **Wrapper Paradigm:** Grit safely passes all CLI arguments directly to git using `subprocess.run` while injecting `GIT_AUTHOR_DATE`. It intercepts but does not modify `git commit --amend`.
2.  **Date Resolution Logic:** To avoid SQLite `ORDER BY` hangs, we limit the recursive CTE to `+365` days forward.
3.  **Testing Strategy:** Test-driven development from the bottom up ensuring state mutations mock the `subprocess` accurately.
4.  **GitHub Scraping:** Relies exclusively on `tool-tip` DOM parsing inside GitHub's public HTML grid.
5.  **Documentation:** Standardized on a static export Next.js App Router setup with Tailwind CSS and Framer Motion to maximize customer conversion and visual appeal.

## What Needs to be Done in the Next Session
1.  **Beta Testing / Dogfooding:** Install the tool globally (using `uv tool install .`) and test it locally on a real Git repository to shake out any undiscovered UX quirks or edge cases.
2.  **PyPI Publishing Prep:** Review `pyproject.toml` classifiers, add a `LICENSE` file (e.g., MIT), and ensure the build process works flawlessly for PyPI distribution.
3.  **GitHub Actions:** Set up a `.github/workflows/ci.yml` to automatically run the `uv run pytest` suite on every push and PR.

## Operational Rules
- **Rule:** Always update this context file (`docs/grit_context.md`) at the end of the session when the user prompts to update it.
