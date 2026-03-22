# Test Plan: Grit

This document outlines the testing strategy for the `grit` CLI tool. All test cases must pass before any feature is considered complete.

## 1. Unit Tests (Core Logic)

**1.1. Date Allocation (`allocator.py`)**
*   **`test_allocator_first_commit`**: 
    *   *Setup*: Empty DB, target=5, start=Today.
    *   *Action*: Request next date.
    *   *Expected*: Returns Today.
*   **`test_allocator_forward_scan_memoization`**:
    *   *Setup*: DB has Today (5/5), Yesterday (5/5), 2 Days Ago (5/5). target=5.
    *   *Action*: Request next date.
    *   *Expected*: Returns Tomorrow's date.
*   **`test_allocator_config_change_invalidates_memo`**:
    *   *Setup*: DB has Today (5/10), target changed from 5 to 10.
    *   *Action*: Request next date.
    *   *Expected*: Returns Today (even if previously considered "full" under the old target).
*   **`test_allocator_past_deficiency`**:
    *   *Setup*: Target=5. Start=2023-01-01. DB has 2023-01-01 (5), 2023-01-02 (2), 2023-01-03 (5). Today is 2023-01-04.
    *   *Action*: Request next date.
    *   *Expected*: Returns 2023-01-02.

**1.2. Timestamp Generation (`executor.py`)**
*   **`test_timestamp_formatting`**:
    *   *Setup*: Input date `2024-03-22`. Current system time `14:30:00`.
    *   *Action*: Format for `GIT_AUTHOR_DATE`.
    *   *Expected*: Outputs valid Git timestamp format (e.g., `2024-03-22 14:30:00 +0000` or equivalent ISO8601 string compatible with Git).

**1.3. Database Operations (`state.py`)**
*   **`test_db_init`**:
    *   *Setup*: Fresh install.
    *   *Action*: Initialize DB.
    *   *Expected*: Creates `config` and `commits` tables with correct schemas.
*   **`test_db_upsert_count`**:
    *   *Setup*: DB initialized.
    *   *Action*: Upsert commit count for `2024-01-01` to 3.
    *   *Expected*: `SELECT count FROM commits WHERE date='2024-01-01'` returns 3.

**1.4. Sync Engine (`sync.py`)**
*   **`test_sync_parser_local`**:
    *   *Setup*: Feed mock `git log --author="user" --format="%ad" --date=short` output string.
    *   *Action*: Parse and aggregate counts.
    *   *Expected*: Correctly calculates sums per day.
*   **`test_sync_github_scraper`**:
    *   *Setup*: Mock HTTP response from `github.com/users/<username>/contributions`.
    *   *Action*: Parse HTML grid for dates and counts.
    *   *Expected*: Correctly extracts a dictionary of `{date: count}` pairs.
*   **`test_sync_max_merge_logic`**:
    *   *Setup*: DB has `2024-01-01` (3). Sync data returns `2024-01-01` (5) and `2024-01-02` (2).
    *   *Action*: Run DB sync merge.
    *   *Expected*: DB now has `2024-01-01` (5) and `2024-01-02` (2). (Uses MAX, does not overwrite higher values with lower ones).

## 2. Integration Tests (Git Interoperability)

*   **`test_state_not_incremented_on_git_failure`**:
    *   *Setup*: Mock `subprocess.run` to return exit code `1` (e.g., pre-commit hook failed or nothing added).
    *   *Action*: Run `grit commit`.
    *   *Expected*: State manager does *not* increment the count for the allocated date.
*   **`test_state_incremented_on_git_success`**:
    *   *Setup*: Mock `subprocess.run` to return exit code `0`.
    *   *Action*: Run `grit commit`.
    *   *Expected*: State manager increments the count for the allocated date by 1.
*   **`test_typer_commit_passthrough`**:
    *   *Setup*: Call `grit commit -m "feat: test" --no-verify`.
    *   *Action*: Intercept subprocess call.
    *   *Expected*: The exact arguments `['-m', 'feat: test', '--no-verify']` are passed to the `git commit` command (along with the injected env var).

## 3. End-to-End / CLI Behavior Tests

*   **`test_cli_first_run_interception`**:
    *   *Setup*: No configuration DB exists.
    *   *Action*: Run `grit commit`.
    *   *Expected*: CLI exits gracefully with message prompting user to run `grit` setup.
*   **`test_cli_amend_warning`**:
    *   *Setup*: DB is configured.
    *   *Action*: Run `grit commit --amend`.
    *   *Expected*: Standard out captures a specific Rich warning panel about amends not being tracked, but the git command still executes.
*   **`test_interactive_setup_flow`**:
    *   *Setup*: Trigger `grit config`.
    *   *Action*: Simulate Typer prompt inputs (username, target, start date).
    *   *Expected*: DB is correctly populated with the provided values, and a background fetch is initiated.
*   **`test_cli_ungrit`**:
    *   *Setup*: DB exists.
    *   *Action*: Run `grit ungrit`, confirm `Y`.
    *   *Expected*: `~/.config/grit` directory and all contents are securely deleted, CLI exits cleanly.