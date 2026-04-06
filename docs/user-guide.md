# 📖 User Guide

Get started with Grit in three easy steps.

![Git Push Meme](https://media.tenor.com/bK1RAdR_iP4AAAAC/dog-coding.gif)

---

## 1. Initial Setup

Before using Grit, you need to tell it your goals. Run the setup wizard:

```bash
$ grit config
```

You will be prompted for four simple things:

1.  **Daily Target:** How many commits do you want per day?
2.  **Start Date:** The historical boundary for backfilling (YYYY-MM-DD).
3.  **Allocation Strategy:** Choose between `today` (fill recent gaps first) or `start_date` (fill from the beginning).
4.  **GitHub Username:** Your public username to synchronize your contribution graph.

!!! tip "Headless Setup for CI/CD"
    You can bypass the interactive prompts entirely using flags:
    ```bash
    $ grit config --target 5 --start 2024-01-01 --username yourgithub --fill-from today
    ```

---

## 2. Intelligence Dashboard (`grit dashboard`)

Grit includes a built-in, high-fidelity web dashboard that works completely offline. It provides deep insights into your commit velocity and pipeline.

```bash
$ grit dashboard
```

- **Visual Velocity:** Interactive charts showing your last 30 days of work.
- **Journey Progress:** Track exactly how many commits are pending to reach your "Green Wall" goal.
- **Live Pipeline:** See where your next 10 commits will land before you even type them.

---

## 3. Committing Code

Grit is designed to be frictionless. You can use it as a silent wrapper, or let it do the heavy lifting for you.

### The Interactive DevX Wizard (Recommended)
Simply type `grit commit` with no arguments to launch the Interactive Wizard.

```bash
$ grit commit
```
1.  **File Picker:** Use your arrow keys to navigate and **Spacebar** to select which files to stage.
    *   **Folding:** Use **Tab** or **Left/Right Arrow keys** to collapse and expand directories. This is extremely helpful for navigating deep project structures like `node_modules` or complex skill paths.
2.  **Semantic Auto-Commit:** Choose a conventional commit type, or select `✨ Auto-generate (AI)` to let Grit read your diff and write the perfect message for you.
3.  **Smart Push:** Grit will ask if you want to push immediately. If the remote rejects it, Grit will gracefully offer to `git pull --rebase` for you.

### Standard Execution
Use it exactly like standard Git to bypass the wizard:

=== "Standard"
    ```bash
    grit commit -m "fix: resolve memory leak"
    ```

=== "Bypass Hooks"
    ```bash
    grit commit -m "wip" --no-verify
    ```

!!! success "How it works"
    Grit automatically generates a valid Git timestamp in your local timezone, injects it into both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`, and safely executes the commit. If the commit fails (e.g. pre-commit hook failure) or the HEAD hash doesn't change, Grit will **not** increment your daily counter.

---

## 4. History Redistributor (`grit spread`)

Finished a massive feature and made 10 commits in one night? Use `grit spread` to intelligently redistribute them across your historical gaps.

```bash
$ grit spread HEAD~5
```

- **Analysis:** Grit scans the specified range of commits.
- **Allocation:** It finds the next available slots in your history based on your `daily_target` and `fill_strategy`.
- **Rewrite:** Grit performs an automated history rewrite using a safe "Shadow Branch" strategy.
- **Atomic Sync:** Your local database is updated only if the rewrite succeeds.

!!! warning "Rewriting History"
    Like `git rebase`, this command rewrites commit hashes. If you have already pushed these commits, you will need to `git push --force`.

---

## 5. Quantum Undo (`grit undo`)

Made a mistake? Committed to the wrong day? Use the panic button:

```bash
$ grit undo
```

This command safely performs a `git reset --soft HEAD~1` (keeping your files staged) and **decrements the commit count** in the Grit database, perfectly preserving your timeline.

!!! warning "Push Protection"
    If Grit detects that your commit has already been pushed to GitHub, it will warn you before allowing an undo to prevent you from rewriting public history.

---

## 6. Checking Status

Want to know how many commits you have left for the day, or view your overall journey progress?

```bash
$ grit status
```

**Example Output:**
```text
  █ █ █ ░ ░  3/5 today [OPTIMIZED]

✦ Journey Progress: 42.5% ━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░ 124 commits pending

╭──────────────────── Commit Intelligence Pipeline ────────────────────╮
│                                                                      │
│    Date                  Timeline             Status         Load    │
│    2026-04-06            today                   ◆            0/1    │
│    2026-03-04            next                    ◇            0/1    │
│    2026-03-05            fill                    ◇            0/1    │
│    2026-03-06            then fill               ◇            0/1    │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

---

## Maintenance Commands

### Self-Healing (`grit sync`)

If you commit from a different computer, merge a PR on GitHub, or bypass Grit by using an IDE's source control tab, your local database will become out of sync. 

To fix this, run:

```bash
$ grit sync
```

!!! info "Safe Merging"
    Grit fetches your local `git log` and remote GitHub data, merging them using a strict `MAX(current, new)` rule. **It will never lower your commit count.**

### Uninstallation (`grit ungrit`)

If you want to completely wipe Grit's state and configuration:

```bash
$ grit ungrit
```

!!! warning "Scripted Teardown"
    To bypass the confirmation prompt, use the force flag:
    ```bash
    $ grit ungrit --force
    ```

---

## 🗺️ Next Up: Dive Deeper

Ready to see how the sausage is made, or maybe contribute some code of your own?

<div class="grid cards" markdown>

-   :material-code-tags: **[Next Up: Developer Onboarding ➔](developer-guide.md)**
    
    Get your local environment running in under 2 minutes.
</div>
