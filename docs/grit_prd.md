# Product Requirements Document (PRD): Grit

## 1. Overview & Objective
**Grit** is a terminal-based CLI wrapper for `git commit`. Its primary objective is to intelligently distribute commits across a timeline to help users consistently hit a specific `daily_target` of commits, starting from a mutable `start_date`.

It achieves this by dynamically calculating and injecting both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` environment variables into the vanilla `git commit` process to ensure a consistent backdated history.

## 2. Core Behavior & Algorithm
When a user runs `grit commit <args>`:
1.  **State Check:** Grit queries its local database for the commit count of "today".
2.  **Date Allocation:**
    *   **Priority 1 (Live):** If today's count < `daily_target`, assign the commit to today.
    *   **Priority 2 (Healing/Backfilling):** If today is full, scan for gaps between `today` and `start_date`. The direction depends on the `fill_strategy`:
        *   `start_date` (Default): Fills gaps closest to the start date first (chronological).
        *   `today`: Fills gaps closest to today first (reverse chronological).
    *   **Priority 3 (Future):** If all past dates are full, assign the commit to the earliest future date.
3.  **Timestamp Generation:** The injected date uses the target `YYYY-MM-DD` combined with the current system time (`HH:MM:SS`) and timezone.
4.  **Execution:** Run `git commit <args>` with the injected `GIT_AUTHOR_DATE`.
5.  **State Update:** If the `git commit` command succeeds (exit code 0), increment the commit count for that date in the local database.

## 3. UX & Command Structure
Built using Python, Typer, and Rich for a premium, interactive terminal experience.

*   **`grit`** (or `grit config`): 
    *   Clears the terminal and opens a premium, interactive "Control Center" TUI.
    *   Allows configuration of `daily_target`, `start_date`, `github_username`, `fill_strategy`, and AI LLM configurations.
    *   *Cold Start Magic:* Upon save, immediately triggers a background fetch of the user's public GitHub contribution graph.
*   **`grit info`**: 
    *   Renders a highly readable command reference and disclaimers in the terminal.
*   **`grit status`**: 
    *   Displays a sophisticated dashboard showing today's progress and a visually mapped pipeline. The `NEXT FILL` slot is highlighted with a dedicated color and label.
*   **`grit spread <range>`**: 
    *   The "History Redistributor". Takes a range of commits (e.g., `HEAD~5`) and spreads them across the timeline gaps automatically.
    *   Uses a safe "Shadow Branch" strategy to rewrite history and only applies changes if successful.
*   **`grit sync`**: 
    *   The self-healing command. Merges Local Git and Remote GitHub state into the database using `MAX(current, new)`.
*   **`grit commit <args>`**: 
    *   With arguments: Transparently passes all arguments to vanilla git.
    *   *Zero Arguments:* Opens the **Interactive DevX Wizard**.
        1. **File Picker:** Select files to `git add` interactively.
        2. **Semantic/AI Message:** Choose a conventional type or let the configured LLM generate a perfect commit based on `git diff`.
        3. **Smart Push:** Offers to push immediately. If the remote rejects it, offers to `git pull --rebase` automatically.
*   **`grit undo`**:
    *   The "Quantum Undo". Performs `git reset --soft HEAD~1` and explicitly decrements the database counter.
    *   *Safety:* If the commit has already been pushed to the remote, warns the user against rewriting public history and offers a safe `git revert` alternative.
*   **`grit ungrit`**: 
    *   Prompts for confirmation, then securely deletes the configuration directory and exits.

## 4. Architecture & Data Handling
To ensure high performance, zero-dependency data handling, and concurrency safety (e.g., multiple terminal panes committing at once), Grit uses a local **SQLite database** (`~/.config/grit/state.db`), explicitly rejecting JSON.

### Database Schema
*   **`config` table:** `(key TEXT PRIMARY KEY, value TEXT)`
    *   Keys: `start_date`, `daily_target`, `github_username`, `fill_strategy`.
*   **`commits` table:** `(date TEXT PRIMARY KEY, count INTEGER)`
    *   Stores `YYYY-MM-DD` and the integer count. Only stores dates with >0 commits.

### The Allocator Query
Finding the next available date requires zero Python loops. It relies on a single optimized SQL query:
```sql
SELECT d.d
FROM dates d -- Recursive CTE generated table
LEFT JOIN commits c ON d.d = c.date
WHERE COALESCE(c.count, 0) < {daily_target}
ORDER BY 
    CASE 
        WHEN d.d = '{today}' THEN 0 -- Priority 1
        WHEN d.d < '{today}' THEN 1 -- Priority 2
        ELSE 2                      -- Priority 3
    END ASC,
    CASE 
        WHEN d.d < '{today}' THEN d.d 
    END {order_dir}, -- ASC for start_date-first, DESC for today-first
    d.d ASC -- Forward fill future gaps
LIMIT 1;
```

## 5. Constraints & Edge Cases
*   **State Accuracy:** Grit only knows what it touches. If a user bypasses Grit (e.g., VSCode UI), the database desyncs. This is solved permanently by `grit sync` and the initial setup fetch.
*   **Git Failure:** Grit must monitor the exit code of `subprocess.run(['git', 'commit', ...])`. It only increments the state if the commit actually succeeds.
*   **Privacy:** The GitHub fetch only scrapes public data (no PAT required) to minimize friction and security risks.
*   **Warnings:** Grit should intercept `grit commit --amend` to warn the user that amends are not tracked towards the daily goal. It should also optionally warn if committing to a non-default branch (e.g., `feature/xyz`), as GitHub only counts default branch commits immediately.
