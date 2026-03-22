# Product Requirements Document (PRD): Grit

## 1. Overview & Objective
**Grit** is a terminal-based CLI wrapper for `git commit`. Its primary objective is to intelligently distribute commits across a timeline to help users consistently hit a specific `daily_target` of commits, starting from a mutable `start_date`.

It achieves this by dynamically calculating and injecting the `GIT_AUTHOR_DATE` environment variable into the vanilla `git commit` process. `GIT_COMMITTER_DATE` is left untouched to preserve the repository's true chronological history while still painting the GitHub contribution graph.

## 2. Core Behavior & Algorithm
When a user runs `grit commit <args>`:
1.  **State Check:** Grit queries its local database for the commit count of "today".
2.  **Date Allocation:**
    *   If today's count < `daily_target`, assign the commit to today.
    *   If today is full, scan forwards from the configured `start_date` up to today. Find the *first* date where count < `daily_target`.
    *   If all past dates are full, assign the commit to the next future date (e.g., tomorrow).
3.  **Timestamp Generation:** The injected date uses the target `YYYY-MM-DD` combined with the current system time (`HH:MM:SS`) and timezone.
4.  **Execution:** Run `git commit <args>` with the injected `GIT_AUTHOR_DATE`.
5.  **State Update:** If the `git commit` command succeeds (exit code 0), increment the commit count for that date in the local database.

## 3. UX & Command Structure
Built using Python, Typer, and Rich for a premium, interactive terminal experience.

*   **`grit`** (or `grit config`): 
    *   Clears the terminal and opens an interactive, typing-friendly menu.
    *   Prompts for `daily_target`, `start_date`, and `github_username`.
    *   *Cold Start Magic:* Upon completion, immediately triggers a background fetch of the user's public GitHub contribution graph to pre-fill the database, preventing Grit from overwriting days that already have commits.
*   **`grit info`** (also `man grit` via alias): 
    *   Renders a beautiful Markdown manual in the terminal.
    *   Contains crucial **Disclaimers**:
        *   "Use grit primarily in personal or solo projects. Modifying author dates in heavily collaborative repositories can cause timeline confusion."
        *   "Squash merging via GitHub UI will destroy individual commit dates. Use rebase or merge commits."
        *   "Using `--amend` modifies existing commits and is not tracked by Grit."
*   **`grit status`**: 
    *   Displays a Rich dashboard showing today's count `[x/target]`, the next available date, and overall progress.
*   **`grit sync`**: 
    *   The self-healing command. 
    *   Fetches the latest public contribution graph from GitHub.
    *   Parses the *local* repository's `git log`.
    *   Merges both data sources into the database using a "Lower Bound Update" (`MAX(current, new)`).
*   **`grit commit <args>`**: 
    *   The core wrapper. Transparently passes all arguments to vanilla git.
    *   If run before configuration, prompts the user to run `grit`.
*   **`grit ungrit`**: 
    *   Prompts for confirmation, then securely deletes the configuration directory and exits.

## 4. Architecture & Data Handling
To ensure high performance, zero-dependency data handling, and concurrency safety (e.g., multiple terminal panes committing at once), Grit uses a local **SQLite database** (`~/.config/grit/state.db`), explicitly rejecting JSON.

### Database Schema
*   **`config` table:** `(key TEXT PRIMARY KEY, value TEXT)`
    *   Keys: `start_date`, `daily_target`, `github_username`.
*   **`commits` table:** `(date TEXT PRIMARY KEY, count INTEGER)`
    *   Stores `YYYY-MM-DD` and the integer count. Only stores dates with >0 commits.

### The Allocator Query
Finding the next available date requires zero Python loops. It relies on an O(1) SQL query:
```sql
SELECT date 
FROM commits 
WHERE count < {daily_target} 
  AND date >= '{start_date}' 
  AND date <= '{today}'
ORDER BY date ASC 
LIMIT 1;
```

## 5. Constraints & Edge Cases
*   **State Accuracy:** Grit only knows what it touches. If a user bypasses Grit (e.g., VSCode UI), the database desyncs. This is solved permanently by `grit sync` and the initial setup fetch.
*   **Git Failure:** Grit must monitor the exit code of `subprocess.run(['git', 'commit', ...])`. It only increments the state if the commit actually succeeds.
*   **Privacy:** The GitHub fetch only scrapes public data (no PAT required) to minimize friction and security risks.
*   **Warnings:** Grit should intercept `grit commit --amend` to warn the user that amends are not tracked towards the daily goal. It should also optionally warn if committing to a non-default branch (e.g., `feature/xyz`), as GitHub only counts default branch commits immediately.
