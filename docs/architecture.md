# Architecture & Internals

Grit might seem like a simple script, but it is carefully engineered to handle terminal concurrency, edge cases, and performance constraints.

## 1. The State Engine (SQLite)

Initially, it is tempting to store CLI configuration and state in a `config.json` file. Grit explicitly rejects this approach.

**Why SQLite?**
If a user is running a build script, or committing from multiple tmux panes, JSON files are susceptible to race conditions and corruption during concurrent writes. SQLite provides robust, OS-level file locking.

The schema is heavily normalized:
* `config` table: Key-value pairs for `daily_target`, `start_date`, etc.
* `commits` table: Primary key `date` (YYYY-MM-DD), and `count` (integer).

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

This query instantly generates an ephemeral table of all dates from the `start_date` up to a year into the future, joins it against the actual commits table, and returns the first date that falls below the target. It executes in milliseconds.

## 3. The Sync Engine

Grit is "dumb" by design—it only increments its internal database when `subprocess.run(['git', 'commit'])` returns an exit code of `0`. 

If a user bypasses Grit, desynchronization occurs. The `sync.py` module is the self-healing mechanism.

**Local Sync:**
It runs `git log --format="%ad" --date=short` and parses the output to calculate how many commits exist on each day locally.

**Remote Sync:**
It fetches `https://github.com/users/<username>/contributions`. We purposefully avoid using the GitHub API to eliminate the need for users to generate Personal Access Tokens (PATs). Instead, we use `httpx` and `beautifulsoup4` to parse the HTML tooltips on the public contribution graph grid.

**The Merge Logic:**
When merging these three sources of truth (Internal DB, Local Git, Remote GitHub), Grit uses a strict `MAX()` constraint.
```python
if new_count > current_count:
    set_commit_count(date, new_count)
```
This guarantees that Grit never accidentally overwrites high activity days with lower numbers, ensuring historical safety.
