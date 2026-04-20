# Architecture & Internals

Grit might seem like a simple script, but it is carefully engineered to handle terminal concurrency, edge cases, and performance constraints.

## 1. The State Engine (SQLite)

Initially, it is tempting to store CLI configuration and state in a `config.json` file. Grit explicitly rejects this approach.

**Why SQLite?**
If a user is running a build script, or committing from multiple tmux panes, JSON files are susceptible to race conditions and corruption during concurrent writes. SQLite provides robust, OS-level file locking.

The schema is heavily normalized:
* `config` table: Key-value pairs for `daily_target`, `start_date`, etc.
* `commits` table: Primary key `date` (YYYY-MM-DD), and `count` (integer).

[View Database Schema Diagram](../diagrams/db-schema.mmd)

## 2. The O(1) Allocator

When a user runs `grit commit`, the CLI needs to know exactly what date to assign the commit to. 

**The Rules:**
1. If today has space (count < target), use today.
2. If today is full, look backwards to `start_date` and find the first day with space.
3. If all past days are full, schedule it in the future.

Instead of writing a Python `while` loop that queries the database hundreds of times, we push the complexity to the SQLite query engine using a **Recursive Common Table Expression (CTE)**.

```sql
WITH RECURSIVE dates(d) AS (
    SELECT ? -- Start Date
    UNION ALL
    SELECT date(d, '+1 day')
    FROM dates
    WHERE d < date(?, '+365 days') -- Boundary to prevent infinite loops
)
SELECT d.d
FROM dates d
LEFT JOIN commits c ON d.d = c.date
WHERE COALESCE(c.count, 0) < ? -- Target
ORDER BY d.d ASC
LIMIT 1;
```

### The "Virtual Two-Pointer" Optimization
To support "Streak-First" allocation (filling recent gaps before future ones), we evolved this query into a virtual two-pointer system. Instead of a simple forward scan, the SQL engine handles two search directions simultaneously:

1. **The Backfill Pointer:** Scans `d.d < today` in `DESC` order.
2. **The Spillover Pointer:** Scans `d.d > today` in `ASC` order.

This is achieved via a multi-level `ORDER BY` with `CASE` statements, ensuring the database engine always yields the most "streak-preserving" date in $O(1)$ time.

[View Allocator Sequence Diagram](../diagrams/allocator.mmd)

## 3. The Sync Engine
Grit is "dumb" by design—it only increments its internal database when `subprocess.run(['git', 'commit'])` returns an exit code of `0`. 

If a user bypasses Grit, desynchronization occurs. The `sync.py` module is the self-healing mechanism.

[View Sync Engine Diagram](../diagrams/sync-engine.mmd)

**Local Sync:**
It runs `git log --format="%ad" --date=short` and parses the output to calculate how many commits exist on each day locally.

**Remote Sync:**
It fetches `https://github.com/users/<username>/contributions`. We purposefully avoid using the GitHub API to eliminate the need for users to generate Personal Access Tokens (PATs). Instead, we use `httpx` and `beautifulsoup4` to parse the HTML tooltips on the public contribution graph grid.

## 4. The DevX Intelligence Layer
When users execute `grit commit` with zero arguments, the CLI enters an interactive wizard:
1. **Interactive `git add`**: Uses `--porcelain` to identify changed files and presents a TUI checklist.
2. **AI Commit Generation**: Optionally sends the output of `git diff --staged` to an LLM endpoint (Ollama, Claude, Groq, etc., configurable via `ai_base_url` and `ai_api_key`) to generate perfect Conventional Commits.
3. **Smart Push**: Automatically handles push rejections by offering an immediate `git pull --rebase` to prevent timeline collisions.
4. **Quantum Undo**: `grit undo` performs a `git reset --soft HEAD~1` and explicitly decrements the database count for the author date of `HEAD`, allowing risk-free regression. It halts if the commit has already been pushed.

**The Merge Logic:**
When merging these three sources of truth (Internal DB, Local Git, Remote GitHub), Grit uses a strict `MAX()` constraint.
```python
if new_count > current_count:
    set_commit_count(date, new_count)
```
This guarantees that Grit never accidentally overwrites high activity days with lower numbers, ensuring historical safety.
