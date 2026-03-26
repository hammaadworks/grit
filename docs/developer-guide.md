# 🛠️ Developer Guide

Welcome! This guide will get you contributing to Grit in **under 2 minutes**.

![Hackerman Meme](https://media.tenor.com/E8R-R6oMIE8AAAAC/hackerman-hack.gif)

We rely heavily on strict testing, fast tooling, and robust architectural patterns.

---

## 🚀 1. Local Setup

We use [`uv`](https://docs.astral.sh/uv/), an extremely fast Python package manager written in Rust.

=== "macOS / Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
=== "Windows"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Once `uv` is installed, clone and sync:

```bash
git clone https://github.com/your-org/grit.git
cd grit
uv sync
```
*Note: `uv sync` automatically creates your virtual environment (`.venv`) and installs everything.*

---

## 🏃‍♂️ 2. Running Your Local Code

If you fix a bug or add a feature, you need to run your local version of the code, not the globally installed one. 

Use `uv run` to execute the CLI directly from your local source code:

```bash
# Run the local interactive setup
uv run grit config

# Run a local commit
uv run grit commit -m "test: trying my new local code"

# Check local status
uv run grit status
```

---

## ✅ 3. Running Tests

Grit uses Test-Driven Development (TDD) via `pytest` and `pytest-mock`. **All tests must pass before opening a PR.**

```bash
# Run the entire test suite
uv run pytest tests/ -v
```

!!! tip "Test Structure"
    - **Unit:** Mock the subprocess and file system (`test_allocator.py`).
    - **Integration:** Ensure exact string formatting and data aggregation (`test_sync.py`).
    - **CLI (E2E):** Simulate user input via Typer's `CliRunner` (`test_cli.py`).

---

## 🏗️ 3. Project Map

Where does the code live?

| File | Purpose |
|------|---------|
| `cli.py` | The Typer application and user-facing terminal UI. |
| `state.py` | The atomic SQLite wrapper for configuration and state. |
| `allocator.py` | The core SQL CTE logic for finding the next commit date. |
| `sync.py` | Parses local `git log` and scrapes the GitHub public graph. |
| `executor.py` | Generates the timezone-aware `GIT_AUTHOR_DATE` and wraps `subprocess.run`. |

---

## 📜 4. Core Rules

Please follow these guidelines when submitting code:

1. **No JSON for State.** We use SQLite to handle terminal concurrency and file locking gracefully.
2. **Fast Critical Path.** Avoid network requests during `grit commit`. Network calls should only happen in `grit config` or `grit sync`.
3. **Test Everything.** Added a feature? Add a test. Fixed a bug? Write a test that reproduces it first.
4. **Standard Types.** Use modern Python (>= 3.10) typing.

## What's Next?
Ready to write code? Check out the Architecture Deep Dive to understand the SQL allocator.

<div class="grid cards" markdown>

-   :material-sitemap: **[Next Up: Architecture Deep Dive ➔](architecture.md)**
    
    Explore the raw SQL queries and sync logic that powers Grit.

</div>
